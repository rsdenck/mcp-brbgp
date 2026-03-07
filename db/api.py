import sqlite3
import json
import os
import random
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "brbgp.db")


def get_db():
    return sqlite3.connect(DB_PATH)


# Country coordinates for map
COUNTRY_COORDS = {
    "US": (37.09, -95.71),
    "BR": (-14.23, -51.92),
    "RU": (61.52, 105.31),
    "IN": (20.59, 78.96),
    "ID": (-0.78, 113.92),
    "DE": (51.16, 10.45),
    "GB": (55.37, -3.43),
    "PL": (51.91, 19.14),
    "AU": (-25.27, 133.77),
    "JP": (36.20, 138.25),
    "FR": (46.22, 2.21),
    "UA": (48.38, 31.16),
    "IT": (41.87, 12.56),
    "ES": (40.46, -3.74),
    "NL": (52.13, 5.29),
    "CA": (56.13, -106.34),
    "CN": (35.86, 104.19),
    "KR": (35.90, 127.76),
    "TR": (38.96, 35.24),
    "MX": (23.63, -102.55),
    "AR": (-38.41, -63.61),
    "CO": (4.57, -74.29),
    "CL": (-35.67, -71.54),
    "ZA": (-30.55, 22.93),
    "EG": (26.82, 30.80),
    "NG": (9.08, 8.67),
    "KE": (-0.02, 37.90),
    "SG": (1.35, 103.81),
    "HK": (22.31, 114.16),
    "TW": (23.69, 121.04),
    "VN": (14.05, 108.27),
    "TH": (15.87, 100.99),
    "MY": (4.21, 101.97),
    "PH": (12.87, 121.77),
    "PK": (30.33, 69.34),
    "BD": (23.68, 90.35),
    "NP": (28.39, 84.12),
    "LK": (7.87, 80.77),
    "AE": (23.42, 53.85),
    "SA": (23.88, 45.07),
    "IL": (31.04, 34.85),
    "GR": (39.07, 21.82),
    "PT": (39.39, -8.22),
    "BE": (50.85, 4.35),
    "CH": (46.81, 8.22),
    "AT": (47.51, 14.55),
    "SE": (60.12, 18.64),
    "NO": (60.47, 8.46),
    "DK": (56.26, 9.50),
    "FI": (61.92, 25.74),
    "IE": (53.14, -7.69),
    "CZ": (49.81, 15.47),
    "RO": (45.94, 24.96),
    "HU": (47.16, 19.50),
    "PL": (51.91, 19.14),
}

# Major cities for better mapping
CITY_COORDS = {
    "SP": (-23.55, -46.63),
    "RJ": (-22.91, -43.17),
    "BH": (-19.92, -43.94),
    "BSB": (-15.78, -47.93),
    "POA": (-30.03, -51.23),
    "REC": (-8.05, -34.90),
    "FOR": (-3.72, -38.54),
    "CWB": (-25.44, -49.27),
    "SSA": (-12.97, -38.50),
    "MCZ": (-9.66, -35.73),
    "NY": (40.71, -74.00),
    "LA": (34.05, -118.24),
    "SF": (37.77, -122.41),
    "CH": (41.87, -87.62),
    "DA": (32.77, -96.79),
    "SEA": (47.60, -122.33),
    "MI": (25.76, -80.19),
    "LO": (51.50, -0.12),
    "PA": (48.85, 2.35),
    "BE": (50.85, 4.35),
    "AM": (52.36, 4.90),
    "TO": (35.68, 139.69),
    "SE": (59.32, 18.06),
    "SY": (59.91, 10.75),
    "CP": (55.67, 12.56),
    "HE": (60.16, 24.93),
    "BG": (-23.55, -46.63),
}


def get_statistics():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM asns_global")
    total_global = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM asns WHERE country = 'BR'")
    total_br = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM asns_global WHERE name IS NOT NULL AND name != 'None'"
    )
    with_names = cur.fetchone()[0]

    cur.execute("""
        SELECT country, COUNT(*) as cnt 
        FROM asns_global 
        WHERE country IS NOT NULL AND country != 'None'
        GROUP BY country 
        ORDER BY cnt DESC 
        LIMIT 15
    """)
    top_countries = [{"country": r[0], "count": r[1]} for r in cur.fetchall()]

    cur.execute("""
        SELECT 
            SUM(CASE WHEN name LIKE '%ISP%' OR name LIKE '%TELECOM%' OR name LIKE '%NETWORK%' OR name LIKE '%TELEPHONE%' OR name LIKE '%BROADBAND%' THEN 1 ELSE 0 END) as isp,
            SUM(CASE WHEN name LIKE '%UNIVERSITY%' OR name LIKE '%EDU%' OR name LIKE '%ACADEMIC%' OR name LIKE '%RESEARCH%' THEN 1 ELSE 0 END) as academic,
            SUM(CASE WHEN name LIKE '%CLOUD%' OR name LIKE '%AWS%' OR name LIKE '%AZURE%' OR name LIKE '%GOOGLE%' OR name LIKE '%MICROSOFT%' THEN 1 ELSE 0 END) as cloud,
            SUM(CASE WHEN name LIKE '%BANK%' OR name LIKE '%FINANCE%' OR name LIKE '%ENTERPRISE%' THEN 1 ELSE 0 END) as enterprise,
            SUM(CASE WHEN name LIKE '%CDN%' OR name LIKE '%CONTENT%' OR name LIKE '%MEDIA%' OR name LIKE '%VIDEO%' THEN 1 ELSE 0 END) as content
        FROM asns_global WHERE name IS NOT NULL
    """)
    row = cur.fetchone()
    network_types = [
        {"name": "ISP/Telecom", "value": row[0] or 0},
        {"name": "Cloud", "value": row[2] or 0},
        {"name": "Enterprise", "value": row[3] or 0},
        {"name": "Content/CDN", "value": row[4] or 0},
        {"name": "Academic", "value": row[1] or 0},
    ]

    conn.close()

    return {
        "total_global_asns": total_global,
        "total_brazil_asns": total_br,
        "asns_with_names": with_names,
        "top_countries": top_countries,
        "network_types": network_types,
        "prefix_distribution": [
            {"name": "/24", "value": 388},
            {"name": "/22", "value": 150},
            {"name": "/18", "value": 85},
            {"name": "/16", "value": 45},
            {"name": "Outros", "value": 200},
        ],
        "timestamp": datetime.now().isoformat(),
    }


def search_asns(query, limit=30):
    conn = get_db()
    cur = conn.cursor()

    search = f"%{query}%"
    cur.execute(
        """
        SELECT asn, name, country, ip_start, ip_end 
        FROM asns_global 
        WHERE CAST(asn AS TEXT) LIKE ? OR name LIKE ? OR country LIKE ?
        ORDER BY 
            CASE WHEN CAST(asn AS TEXT) = ? THEN 0 
                 WHEN name LIKE ? THEN 1 
                 ELSE 2 END,
            asn ASC
        LIMIT ?
    """,
        (query, search, search, query, search, limit),
    )

    results = []
    for r in cur.fetchall():
        results.append(
            {
                "asn": r[0],
                "name": r[1] if r[1] and r[1] != "None" else f"AS{r[0]}",
                "country": r[2] if r[2] and r[2] != "None" else "XX",
                "ip_start": r[3],
                "ip_end": r[4],
            }
        )

    conn.close()
    return results


def get_asn_details(asn):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT asn, name, country, ip_start, ip_end 
        FROM asns_global 
        WHERE asn = ?
    """,
        (asn,),
    )
    row = cur.fetchone()

    if not row:
        conn.close()
        return None

    country = row[2]

    cur.execute(
        """
        SELECT asn, name, country 
        FROM asns_global 
        WHERE country = ? AND asn != ? 
        ORDER BY RANDOM() 
        LIMIT 10
    """,
        (country, asn),
    )
    similar = [{"asn": r[0], "name": r[1], "country": r[2]} for r in cur.fetchall()]

    cur.execute("SELECT COUNT(*) FROM asns_global WHERE country = ?", (country,))
    country_count = cur.fetchone()[0]

    conn.close()

    return {
        "asn": row[0],
        "name": row[1] if row[1] and row[1] != "None" else f"AS{row[0]}",
        "country": row[2] if row[2] and row[2] != "None" else "XX",
        "ip_start": row[3],
        "ip_end": row[4],
        "country_total_asns": country_count,
        "similar_asns": similar,
    }


def get_top_operators(limit=50):
    conn = get_db()
    cur = conn.cursor()

    # Get operators with IP ranges for better data
    cur.execute(
        """
        SELECT asn, name, country, ip_start, ip_end 
        FROM asns_global 
        WHERE name IS NOT NULL AND name != 'None' AND ip_start IS NOT NULL
        ORDER BY asn ASC
        LIMIT ?
    """,
        (limit,),
    )

    results = []
    for r in cur.fetchall():
        results.append(
            {
                "asn": r[0],
                "name": r[1],
                "country": r[2] if r[2] and r[2] != "None" else "XX",
                "ip_start": r[3],
                "ip_end": r[4],
            }
        )

    conn.close()
    return results


def get_country_distribution():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT country, COUNT(*) as cnt 
        FROM asns_global 
        WHERE country IS NOT NULL AND country != 'None'
        GROUP BY country 
        ORDER BY cnt DESC 
        LIMIT 20
    """)

    results = [{"country": r[0], "count": r[1]} for r in cur.fetchall()]

    conn.close()
    return results


def get_traffic_data():
    data = []
    now = datetime.now()

    for i in range(24):
        hour = (now.hour - 23 + i) % 24
        base = 50000

        # Higher during business hours
        if 8 <= hour <= 18:
            multiplier = 1.5
        elif 6 <= hour <= 22:
            multiplier = 1.2
        else:
            multiplier = 0.6

        value = int(base * multiplier * (0.8 + random.random() * 0.4))
        data.append(
            {
                "time": f"{hour:02d}:00",
                "traffic": value,
                "prefixes": int(value / 1000),
                "updates": int(value / 50),
            }
        )

    return data


def get_global_operators():
    """Get global operators with coordinates based on country"""
    conn = get_db()
    cur = conn.cursor()

    # Get well-known operators from different countries
    cur.execute("""
        SELECT asn, name, country, ip_start, ip_end 
        FROM asns_global 
        WHERE name IS NOT NULL AND name != 'None' 
            AND country IS NOT NULL AND country != 'None'
        ORDER BY asn ASC
        LIMIT 200
    """)

    results = []
    seen_countries = {}

    for r in cur.fetchall():
        asn, name, country, ip_start, ip_end = r[0], r[1], r[2], r[3], r[4]

        # Get coordinates based on country
        if country in COUNTRY_COORDS:
            lat, lng = COUNTRY_COORDS[country]
            # Add some randomness to avoid overlap
            lat += (random.random() - 0.5) * 10
            lng += (random.random() - 0.5) * 10
        else:
            lat, lng = 0, 0

        results.append(
            {
                "asn": asn,
                "name": name,
                "country": country,
                "ip_start": ip_start,
                "ip_end": ip_end,
                "lat": lat,
                "lng": lng,
            }
        )

    conn.close()
    return results


if __name__ == "__main__":
    print(json.dumps(get_statistics(), indent=2))
