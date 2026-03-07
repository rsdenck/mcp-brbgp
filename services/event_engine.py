from datetime import datetime
from typing import Optional, Dict, Any, List
from loguru import logger


class EventEngine:
    def __init__(self):
        self.handlers = {}
        self.event_history = []
        self.max_history = 1000

    def register_handler(self, event_type: str, handler):
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.info(f"Registered handler for event type: {event_type}")

    async def process_event(self, event: Dict[str, Any]):
        event_type = event.get("type", "unknown")

        event_record = {
            "type": event_type,
            "data": event,
            "timestamp": datetime.utcnow().isoformat(),
            "processed": False,
        }

        self.event_history.append(event_record)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history :]

        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                try:
                    await handler(event)
                    event_record["processed"] = True
                except Exception as e:
                    logger.error(f"Error processing event {event_type}: {e}")

    async def detect_withdrawal(self, event: Dict[str, Any]) -> Optional[Dict]:
        if event.get("type") != "withdrawal":
            return None

        return {
            "incident_type": "withdrawal",
            "prefix": event.get("prefix"),
            "message": f"Prefix {event.get('prefix')} was withdrawn",
            "severity": "medium",
            "source": "bgpstream",
        }

    async def detect_route_leak(self, event: Dict[str, Any]) -> Optional[Dict]:
        as_path = event.get("as_path", "")

        if not as_path:
            return None

        asns = as_path.split()

        if len(asns) >= 3:
            first_as = int(asns[0]) if asns[0].isdigit() else None
            last_as = int(asns[-1]) if asns[-1].isdigit() else None

            if first_as and last_as and first_as == last_as:
                return {
                    "incident_type": "route_leak",
                    "prefix": event.get("prefix"),
                    "asn": last_as,
                    "message": f"Potential route leak detected: AS path starts and ends with AS{last_as}",
                    "severity": "high",
                    "source": "bgpstream",
                }

        return None

    async def detect_prefix_disappear(
        self, event: Dict[str, Any], history: List[Dict]
    ) -> Optional[Dict]:
        if event.get("type") != "withdrawal":
            return None

        prefix = event.get("prefix")
        if not prefix:
            return None

        recent_announcements = [
            h
            for h in history
            if h.get("type") == "announcement" and h.get("prefix") == prefix
        ]

        if recent_announcements:
            return {
                "incident_type": "prefix_disappear",
                "prefix": prefix,
                "message": f"Previously announced prefix {prefix} has disappeared",
                "severity": "high",
                "source": "bgpstream",
            }

        return None

    async def detect_as_fall(self, event: Dict[str, Any], asn: int) -> Optional[Dict]:
        if event.get("type") != "withdrawal":
            return None

        return {
            "incident_type": "as_fall",
            "asn": asn,
            "message": f"Multiple withdrawals detected for AS{asn}",
            "severity": "critical",
            "source": "bgpstream",
        }

    def get_event_history(self, limit: int = 100) -> List[Dict]:
        return self.event_history[-limit:]

    def get_events_by_type(self, event_type: str) -> List[Dict]:
        return [e for e in self.event_history if e.get("type") == event_type]
