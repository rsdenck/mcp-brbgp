import peeringdb
import asyncio
from datetime import datetime
from typing import Optional
from loguru import logger
from db.database import get_db_context, ASN, IX, IXMember


class PeeringDBCollector:
    def __init__(self, cache_time: int = 3600):
        self.cache_time = cache_time
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = peeringdb.Client()
        return self._client

    async def sync_all(self):
        logger.info("Starting PeeringDB sync...")

        await self._sync_asns()
        await self._sync_ixs()

        logger.info("PeeringDB sync completed")

    async def _sync_asns(self):
        logger.info("Syncing ASNs from PeeringDB...")

        try:
            asns = self.client.query_all("asn")

            async with get_db_context() as db:
                for asn_data in asns:
                    asn = asn_data.get("asn")
                    if not asn:
                        continue

                    result = await db.execute(
                        "SELECT id FROM asns WHERE asn = ?", (asn,)
                    )
                    existing = result.fetchone()

                    if existing:
                        await db.execute(
                            """UPDATE asns SET name = ?, description = ?, 
                               country = ?, is_peeringdb_synced = 1, updated = ? 
                               WHERE asn = ?""",
                            (
                                asn_data.get("name"),
                                asn_data.get("desc"),
                                asn_data.get("country"),
                                datetime.utcnow(),
                                asn,
                            ),
                        )
                    else:
                        await db.execute(
                            """INSERT INTO asns (asn, name, description, country, 
                               is_peeringdb_synced, created, updated) 
                               VALUES (?, ?, ?, ?, 1, ?, ?)""",
                            (
                                asn,
                                asn_data.get("name"),
                                asn_data.get("desc"),
                                asn_data.get("country"),
                                datetime.utcnow(),
                                datetime.utcnow(),
                            ),
                        )

                await db.commit()

            logger.info(f"Synced {len(asns)} ASNs from PeeringDB")

        except Exception as e:
            logger.error(f"Error syncing ASNs from PeeringDB: {e}")
            raise

    async def _sync_ixs(self):
        logger.info("Syncing IXs from PeeringDB...")

        try:
            ixs = self.client.query_all("ix")

            async with get_db_context() as db:
                for ix_data in ixs:
                    ix_id = ix_data.get("id")
                    if not ix_id:
                        continue

                    country = ix_data.get("country")
                    if country != "BR":
                        continue

                    result = await db.execute(
                        "SELECT id FROM ixs WHERE ix_id = ?", (ix_id,)
                    )
                    existing = result.fetchone()

                    name = ix_data.get("name", "")
                    city = ix_data.get("city", "")

                    if existing:
                        await db.execute(
                            """UPDATE ixs SET name = ?, name_long = ?, city = ?, 
                               country = ?, latitude = ?, longitude = ?, 
                               website = ?, tech_email = ?, updated = ? 
                               WHERE ix_id = ?""",
                            (
                                name,
                                ix_data.get("name_long"),
                                city,
                                country,
                                ix_data.get("latitude"),
                                ix_data.get("longitude"),
                                ix_data.get("website"),
                                ix_data.get("tech_email"),
                                datetime.utcnow(),
                                ix_id,
                            ),
                        )
                    else:
                        await db.execute(
                            """INSERT INTO ixs (ix_id, name, name_long, city, country, 
                               latitude, longitude, website, tech_email, status, updated) 
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)""",
                            (
                                ix_id,
                                name,
                                ix_data.get("name_long"),
                                city,
                                country,
                                ix_data.get("latitude"),
                                ix_data.get("longitude"),
                                ix_data.get("website"),
                                ix_data.get("tech_email"),
                                datetime.utcnow(),
                            ),
                        )

                await db.commit()

            logger.info(f"Synced Brazilian IXs from PeeringDB")

        except Exception as e:
            logger.error(f"Error syncing IXs from PeeringDB: {e}")
            raise

    async def sync_ix_members(self, ix_id: int):
        logger.info(f"Syncing members for IX {ix_id}...")

        try:
            members = self.client.query("ixf", ix_id)

            async with get_db_context() as db:
                for member in members.get("member_list", []):
                    asn = member.get("asnum")
                    if not asn:
                        continue

                    await db.execute(
                        """INSERT OR REPLACE INTO ix_members (ix_id, asn, name, is_peeringdb)
                           VALUES (?, ?, ?, 1)""",
                        (ix_id, asn, member.get("name")),
                    )

                await db.commit()

            logger.info(f"Synced members for IX {ix_id}")

        except Exception as e:
            logger.error(f"Error syncing IX members: {e}")

    async def get_asn_details(self, asn: int) -> Optional[dict]:
        try:
            result = self.client.query_all("asn", asn=asn)
            if result:
                return result[0]
        except Exception as e:
            logger.error(f"Error getting ASN details: {e}")
        return None

    async def get_brazilian_asns(self) -> list:
        try:
            return self.client.query_all("asn", country="BR")
        except Exception as e:
            logger.error(f"Error getting Brazilian ASNs: {e}")
            return []
