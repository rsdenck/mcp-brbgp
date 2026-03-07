import asyncio
import json
from datetime import datetime
from typing import Optional, Callable
from loguru import logger


class BGPStreamCollector:
    def __init__(self, record_callback: Optional[Callable] = None):
        self.record_callback = record_callback
        self.is_running = False
        self._task = None
        self._known_prefixes = {}
        self._known_asns = {}

    async def start(self):
        if self.is_running:
            logger.warning("BGPStream already running")
            return

        self.is_running = True
        logger.info("Starting BGPStream collector...")

        try:
            import pybgpstream

            stream = pybgpstream.BGPStream(
                filter="peer-asn 0",
                collectors=[
                    "rrc00",
                    "rrc01",
                    "rrc02",
                    "rrc03",
                    "rrc04",
                    "rrc05",
                    "rrc06",
                    "rrc07",
                    "rrc08",
                    "rrc09",
                    "rrc10",
                    "rrc11",
                    "rrc12",
                    "rrc13",
                    "rrc14",
                    "rrc15",
                    "rrc16",
                    "rrc18",
                    "rrc19",
                    "rrc20",
                    "rrc21",
                    "rrc22",
                    "rrc23",
                    "rrc24",
                    "rrc25",
                    "rrc26",
                ],
                record_type="updates",
            )

            for elem in stream:
                if not self.is_running:
                    break

                try:
                    await self._process_element(elem)
                except Exception as e:
                    logger.error(f"Error processing element: {e}")

        except ImportError:
            logger.warning("pybgpstream not available, using mock data")
            await self._run_mock()
        except Exception as e:
            logger.error(f"Error in BGPStream: {e}")
            await self._run_mock()

    async def _run_mock(self):
        logger.info("Running mock BGP collector for demonstration")
        await asyncio.sleep(1)

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("BGPStream collector stopped")

    async def _process_element(self, elem):
        if elem.type == "A":
            await self._process_announcement(elem)
        elif elem.type == "W":
            await self._process_withdrawal(elem)
        elif elem.type == "R":
            await self._process_rib_entry(elem)

    async def _process_announcement(self, elem):
        prefix = elem.fields.get("prefix")
        as_path = elem.fields.get("as-path", "")
        origin = elem.fields.get("origin-asn")

        if not prefix or not origin:
            return

        asns = self._parse_as_path(as_path)
        asns.append(origin)

        prefix_key = f"{prefix}_{origin}"

        is_new = prefix_key not in self._known_prefixes
        self._known_prefixes[prefix_key] = {
            "prefix": prefix,
            "origin": origin,
            "as_path": as_path,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "announcement",
        }

        if is_new and self.record_callback:
            await self.record_callback(
                {
                    "type": "announcement",
                    "prefix": prefix,
                    "origin_asn": origin,
                    "as_path": as_path,
                    "timestamp": datetime.utcnow().isoformat(),
                    "collector": elem.collector,
                }
            )

    async def _process_withdrawal(self, elem):
        prefix = elem.fields.get("prefix")

        if not prefix:
            return

        for key in list(self._known_prefixes.keys()):
            if self._known_prefixes[key]["prefix"] == prefix:
                self._known_prefixes[key]["type"] = "withdrawal"
                self._known_prefixes[key]["withdrawn_at"] = (
                    datetime.utcnow().isoformat()
                )

                if self.record_callback:
                    await self.record_callback(
                        {
                            "type": "withdrawal",
                            "prefix": prefix,
                            "timestamp": datetime.utcnow().isoformat(),
                            "collector": elem.collector,
                        }
                    )

    async def _process_rib_entry(self, elem):
        prefix = elem.fields.get("prefix")
        as_path = elem.fields.get("as-path", "")
        origin = elem.fields.get("origin-asn")

        if not prefix:
            return

        if self.record_callback:
            await self.record_callback(
                {
                    "type": "rib",
                    "prefix": prefix,
                    "origin_asn": origin,
                    "as_path": as_path,
                    "timestamp": datetime.utcnow().isoformat(),
                    "collector": elem.collector,
                }
            )

    def _parse_as_path(self, as_path: str) -> list:
        if not as_path:
            return []

        try:
            parts = as_path.split()
            return [int(asn) for asn in parts if asn.isdigit()]
        except:
            return []

    async def get_brazilian_prefixes(self) -> list:
        brazilian_prefixes = []

        for key, value in self._known_prefixes.items():
            if value.get("type") == "announcement":
                prefix = value.get("prefix", "")
                if prefix.startswith(
                    (
                        "177.",
                        "186.",
                        "187.",
                        "189.",
                        "191.",
                        "198.",
                        "200.",
                        "201.",
                        "280:",
                        "300:",
                        "400:",
                        "600:",
                    )
                ):
                    brazilian_prefixes.append(value)

        return brazilian_prefixes

    async def get_top_asns(self, limit: int = 10) -> list:
        asn_counts = {}

        for key, value in self._known_prefixes.items():
            if value.get("type") == "announcement":
                origin = value.get("origin")
                if origin:
                    asn_counts[origin] = asn_counts.get(origin, 0) + 1

        sorted_asns = sorted(asn_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"asn": asn, "count": count} for asn, count in sorted_asns[:limit]]


class RipeRISCollector:
    def __init__(self):
        self.base_url = "https://ris-live.ripe.net/v1"
        self._ws = None
        self.is_running = False

    async def start(self):
        logger.info("Starting RIPE RIS collector...")
        self.is_running = True

    async def stop(self):
        self.is_running = False
        logger.info("RIPE RIS collector stopped")

    async def get_peers(self) -> list:
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/peers") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("peers", {})
        except Exception as e:
            logger.error(f"Error getting RIS peers: {e}")
        return []

    async def get_announcements(self, prefix: Optional[str] = None) -> list:
        try:
            import aiohttp

            params = {"format": "json"}
            if prefix:
                params["prefix"] = prefix

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/stream", params=params
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("data", [])
        except Exception as e:
            logger.error(f"Error getting RIS announcements: {e}")
        return []

    async def subscribe_to_stream(
        self, stream_type: str = "updates", callback: Optional[Callable] = None
    ):
        try:
            import aiohttp
            import json

            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(f"{self.base_url}/stream") as ws:
                    await ws.send_json(
                        {"type": "subscribe", "stream": stream_type, "data": {}}
                    )

                    async for msg in ws:
                        if not self.is_running:
                            break

                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)
                                if callback:
                                    await callback(data)
                            except:
                                pass

        except Exception as e:
            logger.error(f"Error in RIS stream: {e}")
