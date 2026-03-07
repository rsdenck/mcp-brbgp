import requests
import sqlite3
import os
from loguru import logger
from collections import defaultdict
from datetime import datetime

DATASET_URL = "https://iptoasn.com/data/ip2asn-combined.tsv.gz"
DATASET_FILE = "ip2asn-combined.tsv.gz"
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "brbgp.db")


def download_dataset():
    logger.info("Downloading iptoasn dataset...")
    response = requests.get(DATASET_URL, stream=True, timeout=300)
    total = int(response.headers.get("content-length", 0))

    with open(DATASET_FILE, "wb") as f:
        downloaded = 0
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                percent = (downloaded / total) * 100
                if downloaded % (1024 * 1024 * 10) == 0:
                    logger.info(f"Downloaded: {percent:.1f}%")

    import gzip

    with gzip.open(DATASET_FILE, "rt", encoding="utf-8") as f:
        content = f.read()

    with open(DATASET_FILE.replace(".gz", ""), "w") as f:
        f.write(content)

    logger.info("Dataset downloaded and extracted")
    return DATASET_FILE.replace(".gz", "")


def import_asns(filepath):
    logger.info(f"Importing ASNs from {filepath}...")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS asns_global (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asn INTEGER UNIQUE,
            country TEXT,
            name TEXT,
            ip_start TEXT,
            ip_end TEXT,
            created DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    asns_data = defaultdict(
        lambda: {"country": None, "name": None, "ip_start": None, "ip_end": None}
    )
    total_lines = 0

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            total_lines += 1
            parts = line.strip().split("\t")

            if len(parts) >= 5:
                ip_start = parts[0]
                ip_end = parts[1]
                asn = parts[2]
                country = parts[3]
                name = parts[4] if len(parts) > 4 else None

                if asn and asn != "0" and asn != "None":
                    try:
                        asn_int = int(asn)
                        if asn_int not in asns_data or name:
                            asns_data[asn_int] = {
                                "country": country
                                if country and country != "None"
                                else None,
                                "name": name
                                if name and name != "Not routed" and name != "None"
                                else None,
                                "ip_start": ip_start,
                                "ip_end": ip_end,
                            }
                    except ValueError:
                        continue

            if total_lines % 500000 == 0:
                logger.info(f"Processed {total_lines} lines...")

    logger.info(f"Found {len(asns_data)} unique ASNs")

    batch_size = 1000
    asns_list = list(asns_data.items())

    for i in range(0, len(asns_list), batch_size):
        batch = asns_list[i : i + batch_size]
        values = [
            (asn, data["country"], data["name"], data["ip_start"], data["ip_end"])
            for asn, data in batch
        ]
        cur.executemany(
            "INSERT OR REPLACE INTO asns_global (asn, country, name, ip_start, ip_end) VALUES (?, ?, ?, ?, ?)",
            values,
        )
        conn.commit()
        logger.info(
            f"Inserted {min(i + batch_size, len(asns_list))}/{len(asns_list)} ASNs"
        )

    cur.execute("SELECT COUNT(*) FROM asns_global")
    count = cur.fetchone()[0]
    logger.info(f"Total ASNs in database: {count}")

    conn.close()
    return count


def get_global_stats():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    stats = {}

    cur.execute("SELECT COUNT(*) FROM asns_global")
    stats["total_asns"] = cur.fetchone()[0]

    cur.execute(
        "SELECT country, COUNT(*) as cnt FROM asns_global WHERE country IS NOT NULL GROUP BY country ORDER BY cnt DESC LIMIT 10"
    )
    stats["top_countries"] = cur.fetchall()

    cur.execute(
        "SELECT asn, name, country FROM asns_global WHERE name IS NOT NULL ORDER BY asn ASC LIMIT 20"
    )
    stats["sample_asns"] = cur.fetchall()

    conn.close()
    return stats


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "download":
        download_dataset()
    else:
        filepath = "ip2asn-combined.tsv"
        if not os.path.exists(filepath):
            filepath = download_dataset()

        count = import_asns(filepath)
        stats = get_global_stats()

        print(f"\n=== Global ASN Statistics ===")
        print(f"Total ASNs: {stats['total_asns']}")
        print(f"\nTop Countries:")
        for country, cnt in stats["top_countries"]:
            print(f"  {country}: {cnt}")
        print(f"\nSample ASNs:")
        for asn, name, country in stats["sample_asns"]:
            print(f"  AS{asn}: {name} ({country})")
