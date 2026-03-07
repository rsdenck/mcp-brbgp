import requests
from bs4 import BeautifulSoup
import asyncio
from datetime import datetime
from typing import List, Optional
from loguru import logger


class IXBRStatusCollector:
    def __init__(self):
        self.base_url = "https://status.ix.br"
        self._cached_status = None
        self._cache_time = None
        self.cache_duration = 60

    async def get_status(self) -> dict:
        if self._cached_status and self._cache_time:
            age = (datetime.now() - self._cache_time).total_seconds()
            if age < self.cache_duration:
                return self._cached_status

        try:
            response = requests.get(self.base_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            incidents = soup.find_all("incident")
            status_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_incidents": len(incidents),
                "incidents": [],
            }

            for incident in incidents:
                incident_data = self._parse_incident(incident)
                if incident_data:
                    status_data["incidents"].append(incident_data)

            self._cached_status = status_data
            self._cache_time = datetime.now()

            return status_data

        except Exception as e:
            logger.error(f"Error fetching IX.br status: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}

    def _parse_incident(self, incident_soup) -> Optional[dict]:
        try:
            incident_id = incident_soup.get("id", "")

            status_elem = incident_soup.find("incident-status")
            if status_elem:
                status = status_elem.get("status", "unknown")
            else:
                status = "unknown"

            title_elem = incident_soup.find("div", class_="incident-title")
            title = title_elem.text.strip() if title_elem else ""

            body_elem = incident_soup.find("div", class_="incident-body")
            body = body_elem.text.strip() if body_elem else ""

            components = []
            for comp in incident_soup.find_all("incident-component"):
                components.append(
                    {"name": comp.get("name", ""), "status": comp.get("status", "")}
                )

            return {
                "id": incident_id,
                "status": status,
                "title": title,
                "body": body,
                "components": components,
                "parsed_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.warning(f"Error parsing incident: {e}")
            return None

    async def get_ix_list(self) -> List[dict]:
        try:
            response = requests.get("https://ix.br", timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            ix_list = []
            for ix in soup.find_all("a", href=True):
                href = ix.get("href", "")
                if "/ix/" in href:
                    ix_list.append(
                        {"slug": href.split("/")[-1], "name": ix.text.strip()}
                    )

            return ix_list
        except Exception as e:
            logger.error(f"Error fetching IX list: {e}")
            return []

    async def fetch_all_status(self) -> List[dict]:
        ixs = [
            {"slug": "sp", "name": "São Paulo"},
            {"slug": "rj", "name": "Rio de Janeiro"},
            {"slug": "for", "name": "Fortaleza"},
            {"slug": "poa", "name": "Porto Alegre"},
            {"slug": "bh", "name": "Belo Horizonte"},
            {"slug": "cur", "name": "Curitiba"},
            {"slug": "rec", "name": "Recife"},
            {"slug": "sal", "name": "Salvador"},
            {"slug": "vix", "name": "Vitória"},
            {"slug": "mns", "name": "Manaus"},
            {"slug": "cwb", "name": "Campinas"},
            {"slug": "goi", "name": "Goiânia"},
            {"slug": "bsb", "name": "Brasília"},
            {"slug": "ssz", "name": "Santos"},
        ]

        results = []
        for ix in ixs:
            try:
                url = f"https://{ix['slug']}.ix.br/status"
                response = requests.get(url, timeout=5)
                results.append(
                    {
                        "ix": ix["name"],
                        "slug": ix["slug"],
                        "status": "operational"
                        if response.status_code == 200
                        else "offline",
                        "url": url,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "ix": ix["name"],
                        "slug": ix["slug"],
                        "status": "error",
                        "error": str(e),
                    }
                )

        return results
