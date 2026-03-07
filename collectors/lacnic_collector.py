import requests
import asyncio
from loguru import logger
from concurrent.futures import ThreadPoolExecutor

LACNIC_URL = "https://ftp.lacnic.net/pub/stats/lacnic/delegated-lacnic-latest"
RDAP_URL = "https://rdap.lacnic.net/rdap/autnum"
RIPE_RDAP_URL = "https://rdap.db.ripe.net/autnum"


def fetch_brazilian_asns() -> list:
    logger.info("Fetching Brazilian ASNs from LACNIC...")

    try:
        response = requests.get(LACNIC_URL, timeout=60)
        response.raise_for_status()

        asns_br = []
        lines = response.text.splitlines()

        for line in lines:
            if line.startswith("#") or line.startswith(":"):
                continue

            parts = line.split("|")

            if len(parts) > 6:
                registry = parts[0].strip()
                country = parts[1].strip()
                rtype = parts[2].strip()

                if country == "BR" and rtype == "asn":
                    try:
                        start_asn = int(parts[3])
                        count = int(parts[4])

                        for i in range(count):
                            asns_br.append(start_asn + i)
                    except (ValueError, IndexError):
                        continue

        logger.info(f"Found {len(asns_br)} Brazilian ASNs")
        return asns_br

    except requests.RequestException as e:
        logger.error(f"Error fetching LACNIC data: {e}")
        return []


def fetch_asn_details(asn: int) -> dict:
    urls = [f"{RDAP_URL}/{asn}", f"{RIPE_RDAP_URL}/{asn}"]

    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                name = data.get("name")
                description = None
                for entity in data.get("entities", []):
                    for role in entity.get("roles", []):
                        if role == "registrant":
                            for vcard in entity.get("vcardArray", []):
                                if isinstance(vcard, list) and len(vcard) >= 3:
                                    if vcard[0] == "fn":
                                        description = vcard[2]
                            break
                if name:
                    return {"asn": asn, "name": name, "description": description}
        except Exception:
            continue

    return {"asn": asn, "name": None, "description": None}


def fetch_asn_names_batch(asns: list, max_workers: int = 20) -> dict:
    logger.info(f"Fetching names for {len(asns)} ASNs...")
    asn_names = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(fetch_asn_details, asns[:500]))

    for result in results:
        if result["name"]:
            asn_names[result["asn"]] = {
                "name": result["name"],
                "description": result["description"],
            }

    logger.info(f"Fetched names for {len(asn_names)} ASNs")
    return asn_names


async def save_asns_to_db(asns: list, asn_names: dict = None):
    from db.database import get_db_context
    from sqlalchemy import text

    logger.info(f"Saving {len(asns)} ASNs to database...")

    async with get_db_context() as db:
        for asn in asns:
            try:
                name = None
                description = None
                if asn_names and asn in asn_names:
                    name = asn_names[asn].get("name")
                    description = asn_names[asn].get("description")

                await db.execute(
                    text("""INSERT OR REPLACE INTO asns (asn, name, description, country, created, updated)
                       VALUES (:asn, :name, :description, 'BR', datetime('now'), datetime('now'))"""),
                    {"asn": asn, "name": name, "description": description},
                )
            except Exception as e:
                logger.warning(f"Error inserting ASN {asn}: {e}")

        await db.commit()

    logger.info("ASNs saved to database")


async def sync_brazilian_asns():
    asns = fetch_brazilian_asns()

    if asns:
        asn_names = fetch_asn_names_batch(asns)
        await save_asns_to_db(asns, asn_names)
        return {
            "status": "success",
            "asns_count": len(asns),
            "names_fetched": len(asn_names),
        }

    return {"status": "error", "message": "Failed to fetch ASNs"}


if __name__ == "__main__":
    asns = fetch_brazilian_asns()
    print(f"Total Brazilian ASNs: {len(asns)}")
    print(f"First 10 ASNs: {asns[:10]}")
    print(f"Last 10 ASNs: {asns[-10:]}")
