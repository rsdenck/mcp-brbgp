import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
from loguru import logger
from sqlalchemy import text

from db.database import (
    init_db,
    get_db_context,
    ASN,
    Prefix,
    IX,
    IXMember,
    Incident,
    IXStatus,
    RIBEntry,
)
from collectors import (
    PeeringDBCollector,
    IXBRStatusCollector,
    BGPStreamCollector,
    RipeRISCollector,
)
from services import EventEngine, NotificationService

logger.add("logs/brbgp.log", rotation="1 day", level="INFO")


class BGPDataService:
    def __init__(self):
        self.peeringdb = PeeringDBCollector() if PeeringDBCollector else None
        self.ixbr_status = IXBRStatusCollector()
        self.bgpstream = BGPStreamCollector()
        self.ripe_ris = RipeRISCollector()
        self.event_engine = EventEngine()
        self.notifications = NotificationService()
        self.is_running = False

    async def initialize(self):
        await init_db()
        logger.info("Database initialized")

        self.event_engine.register_handler("withdrawal", self._handle_withdrawal)
        self.event_engine.register_handler("route_leak", self._handle_route_leak)
        self.event_engine.register_handler("announcement", self._handle_announcement)

    async def _handle_withdrawal(self, event: Dict):
        prefix = event.get("prefix")
        origin = event.get("origin_asn")

        if prefix and origin:
            await self.notifications.notify_withdrawal(prefix, origin)

    async def _handle_route_leak(self, event: Dict):
        prefix = event.get("prefix")
        origin = event.get("origin_asn")

        if prefix and origin:
            await self.notifications.notify_route_leak(prefix, origin)

    async def _handle_announcement(self, event: Dict):
        prefix = event.get("prefix")
        asn_path = event.get("as_path", "")

        asns = asn_path.split() if asn_path else []
        if len(asns) >= 3:
            first_as = asns[0]
            last_as = asns[-1]
            if first_as == last_as:
                await self._handle_route_leak(event)

    async def sync_peeringdb(self):
        if not self.peeringdb:
            return {
                "status": "skipped",
                "message": "PeeringDB not available on Windows",
            }
        try:
            await self.peeringdb.sync_all()
            return {"status": "success", "message": "PeeringDB sync completed"}
        except Exception as e:
            logger.error(f"Error syncing PeeringDB: {e}")
            return {"status": "error", "message": str(e)}

    async def get_ix_status(self) -> List[Dict]:
        return await self.ixbr_status.fetch_all_status()

    async def get_asn_info(self, asn: int) -> Optional[Dict]:
        async with get_db_context() as db:
            result = await db.execute(
                text("SELECT * FROM asns WHERE asn = :asn"), {"asn": asn}
            )
            row = result.fetchone()
            if row:
                return {
                    "asn": row[1],
                    "name": row[2],
                    "description": row[3],
                    "country": row[4],
                }
        return None

    async def get_prefixes_by_asn(self, asn: int) -> List[Dict]:
        async with get_db_context() as db:
            result = await db.execute(
                text(
                    "SELECT prefix, prefix_v6, is_announced FROM prefixes WHERE asn = :asn"
                ),
                {"asn": asn},
            )
            return [
                {"prefix": r[0], "prefix_v6": r[1], "announced": r[2]}
                for r in result.fetchall()
            ]

    async def get_brazilian_ixs(self) -> List[Dict]:
        async with get_db_context() as db:
            result = await db.execute(
                text(
                    "SELECT ix_id, name, city, country, latitude, longitude FROM ixs WHERE country = 'BR'"
                )
            )
            return [
                {
                    "ix_id": r[0],
                    "name": r[1],
                    "city": r[2],
                    "country": r[3],
                    "lat": r[4],
                    "lon": r[5],
                }
                for r in result.fetchall()
            ]

    async def get_incidents(
        self, limit: int = 50, incident_type: Optional[str] = None
    ) -> List[Dict]:
        async with get_db_context() as db:
            if incident_type:
                result = await db.execute(
                    text(
                        "SELECT * FROM incidents WHERE incident_type = :type ORDER BY detected_at DESC LIMIT :limit"
                    ),
                    {"type": incident_type, "limit": limit},
                )
            else:
                result = await db.execute(
                    text(
                        "SELECT * FROM incidents ORDER BY detected_at DESC LIMIT :limit"
                    ),
                    {"limit": limit},
                )
            return [
                {
                    "id": r[1],
                    "type": r[2],
                    "asn": r[3],
                    "prefix": r[4],
                    "message": r[5],
                    "severity": r[6],
                    "detected_at": r[9],
                }
                for r in result.fetchall()
            ]

    async def get_statistics(self) -> Dict:
        async with get_db_context() as db:
            asn_count = await db.execute(text("SELECT COUNT(*) FROM asns"))
            prefix_count = await db.execute(text("SELECT COUNT(*) FROM prefixes"))
            ix_count = await db.execute(
                text("SELECT COUNT(*) FROM ixs WHERE country = 'BR'")
            )
            incident_count = await db.execute(
                text("SELECT COUNT(*) FROM incidents WHERE is_resolved = 0")
            )

            return {
                "total_asns": asn_count.fetchone()[0] if asn_count else 0,
                "total_prefixes": prefix_count.fetchone()[0] if prefix_count else 0,
                "total_ixs": ix_count.fetchone()[0] if ix_count else 0,
                "active_incidents": incident_count.fetchone()[0]
                if incident_count
                else 0,
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def search_asn(self, query: str) -> List[Dict]:
        async with get_db_context() as db:
            result = await db.execute(
                text(
                    "SELECT asn, name, country FROM asns WHERE name LIKE :q OR CAST(asn AS TEXT) LIKE :q LIMIT 20"
                ),
                {"q": f"%{query}%"},
            )
            return [
                {"asn": r[0], "name": r[1], "country": r[2]} for r in result.fetchall()
            ]

    async def get_top_asns(self, limit: int = 10) -> List[Dict]:
        async with get_db_context() as db:
            result = await db.execute(
                text("""SELECT a.asn, a.name, COUNT(p.prefix) as prefix_count 
                   FROM asns a 
                   LEFT JOIN prefixes p ON a.asn = p.asn
                   GROUP BY a.asn, a.name
                   ORDER BY prefix_count DESC, a.asn ASC
                   LIMIT :limit"""),
                {"limit": limit},
            )
            return [
                {"asn": r[0], "name": r[1], "prefixes": r[2]} for r in result.fetchall()
            ]

    async def get_traffic_stats(self) -> Dict:
        async with get_db_context() as db:
            now = datetime.utcnow()
            hour_ago = now - timedelta(hours=1)

            result = await db.execute(
                text("""SELECT COUNT(*) FROM rib_entries 
                   WHERE collected_at > :hour_ago"""),
                {"hour_ago": hour_ago.isoformat()},
            )
            updates_last_hour = result.fetchone()[0] if result else 0

            withdrawal_count = await db.execute(
                text("""SELECT COUNT(*) FROM incidents 
                   WHERE incident_type = 'withdrawal' 
                   AND detected_at > :hour_ago"""),
                {"hour_ago": hour_ago.isoformat()},
            )
            withdrawals = withdrawal_count.fetchone()[0] if withdrawal_count else 0

            return {
                "updates_last_hour": updates_last_hour,
                "withdrawals_last_hour": withdrawals,
                "timestamp": now.isoformat(),
            }


bgp_service = BGPDataService()


async def get_asn_info(asn: int) -> str:
    info = await bgp_service.get_asn_info(asn)
    if info:
        return json.dumps(info, indent=2)
    return json.dumps({"error": "ASN not found"})


async def get_prefixes(asn: int) -> str:
    prefixes = await bgp_service.get_prefixes_by_asn(asn)
    return json.dumps(prefixes, indent=2)


async def get_statistics() -> str:
    stats = await bgp_service.get_statistics()
    return json.dumps(stats, indent=2)


async def get_ix_list() -> str:
    ixs = await bgp_service.get_brazilian_ixs()
    return json.dumps(ixs, indent=2)


async def get_incidents(limit: int = 50, incident_type: Optional[str] = None) -> str:
    incidents = await bgp_service.get_incidents(limit, incident_type)
    return json.dumps(incidents, indent=2)


async def search_asn(query: str) -> str:
    results = await bgp_service.search_asn(query)
    return json.dumps(results, indent=2)


async def get_top_asns(limit: int = 10) -> str:
    top = await bgp_service.get_top_asns(limit)
    return json.dumps(top, indent=2)


async def get_ix_status() -> str:
    status = await bgp_service.get_ix_status()
    return json.dumps(status, indent=2)


async def sync_data_sources() -> str:
    result = await bgp_service.sync_peeringdb()
    return json.dumps(result, indent=2)


async def get_traffic_stats() -> str:
    stats = await bgp_service.get_traffic_stats()
    return json.dumps(stats, indent=2)


TOOLS = {
    "get_asn_info": get_asn_info,
    "get_prefixes": get_prefixes,
    "get_statistics": get_statistics,
    "get_ix_list": get_ix_list,
    "get_incidents": get_incidents,
    "search_asn": search_asn,
    "get_top_asns": get_top_asns,
    "get_ix_status": get_ix_status,
    "sync_data_sources": sync_data_sources,
    "get_traffic_stats": get_traffic_stats,
}


async def initialize_service():
    await bgp_service.initialize()
    logger.info("BGP Data Service initialized")


async def handle_tool_call(tool_name: str, arguments: dict) -> str:
    if tool_name not in TOOLS:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    tool = TOOLS[tool_name]

    try:
        result = await tool(**arguments)
        return result
    except Exception as e:
        logger.error(f"Error calling tool {tool_name}: {e}")
        return json.dumps({"error": str(e)})
