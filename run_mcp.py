import asyncio
import sys
import json
from loguru import logger

logger.add("logs/brbgp.log", rotation="1 day", level="INFO")


async def initialize_database():
    from db.database import init_db, get_db_context

    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized")


async def load_brazilian_asns():
    from collectors.lacnic_collector import fetch_brazilian_asns, save_asns_to_db

    logger.info("Loading Brazilian ASNs from LACNIC...")
    asns = fetch_brazilian_asns()

    if asns:
        await save_asns_to_db(asns)
        logger.info(f"Loaded {len(asns)} Brazilian ASNs")
        return len(asns)
    else:
        logger.warning("No ASNs loaded from LACNIC")
        return 0


async def sync_peeringdb():
    from collectors import PeeringDBCollector

    if PeeringDBCollector is None:
        logger.warning("PeeringDB not available on Windows - skipping sync")
        return False

    logger.info("Syncing from PeeringDB...")
    collector = PeeringDBCollector()

    try:
        await collector.sync_all()
        logger.info("PeeringDB sync completed")
        return True
    except Exception as e:
        logger.error(f"PeeringDB sync failed: {e}")
        return False


async def main():
    print("=" * 50)
    print("  ARMAZEM RADAR - MCP Server")
    print("  Brazilian BGP Monitoring")
    print("=" * 50)
    print()

    await initialize_database()

    asn_count = await load_brazilian_asns()
    print(f"  [OK] Loaded {asn_count} Brazilian ASNs")

    await sync_peeringdb()
    print(f"  [OK] PeeringDB sync completed")

    print()
    print("Starting MCP Server...")
    print("=" * 50)

    from mcp_server import main as mcp_main

    await mcp_main()


if __name__ == "__main__":
    asyncio.run(main())
