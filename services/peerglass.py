import httpx
import asyncio
from typing import Dict, List, Optional


class PeerGlassService:
    def __init__(self):
        self.rir_endpoints = {
            "AFRINIC": "https://rdap.afrinic.net/rdap",
            "APNIC": "https://rdap.apnic.net",
            "ARIN": "https://rdap.arin.net/registry",
            "LACNIC": "https://rdap.lacnic.net/rdap",
            "RIPE": "https://rdap.db.ripe.net",
        }
        self.headers = {
            "Accept": "application/rdap+json",
            "User-Agent": "ArmazemRadar/1.0.0",
        }
        self.rpki_endpoint = "https://rpki.cloudflare.com/RPKI/META"
        self.peeringdb_base = "https://www.peeringdb.com/api"

    async def query_all_rirs_ip(self, ip: str) -> Dict:
        results = {}
        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = []
            for rir_name, base_url in self.rir_endpoints.items():
                url = f"{base_url}/ip/{ip}"
                tasks.append(self._query_rir(client, rir_name, url))

            responses = await asyncio.gather(*tasks, return_exceptions=True)
            for rir_name, response in zip(self.rir_endpoints.keys(), responses):
                if isinstance(response, Exception):
                    results[rir_name] = {"error": str(response)}
                else:
                    results[rir_name] = response
        return results

    async def query_all_rirs_asn(self, asn: int) -> Dict:
        results = {}
        asn_clean = asn if isinstance(asn, int) else int(asn.replace("AS", ""))
        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = []
            for rir_name, base_url in self.rir_endpoints.items():
                url = f"{base_url}/autnum/{asn_clean}"
                tasks.append(self._query_rir(client, rir_name, url))

            responses = await asyncio.gather(*tasks, return_exceptions=True)
            for rir_name, response in zip(self.rir_endpoints.keys(), responses):
                if isinstance(response, Exception):
                    results[rir_name] = {"error": str(response)}
                else:
                    results[rir_name] = response
        return results

    async def _query_rir(
        self, client: httpx.AsyncClient, rir_name: str, url: str
    ) -> Dict:
        try:
            response = await client.get(
                url, headers=self.headers, follow_redirects=True
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "found",
                    "http_status": 200,
                    "objectClassName": data.get("objectClassName"),
                    "handle": data.get("handle"),
                    "name": data.get("name"),
                    "country": data.get("country"),
                }
            elif response.status_code == 404:
                return {"status": "not_found", "http_status": 404}
            else:
                return {"status": "error", "http_status": response.status_code}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def check_rpki(self, prefix: str, asn: int) -> Dict:
        try:
            asn_clean = asn if isinstance(asn, int) else int(str(asn).replace("AS", ""))
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"https://rpki-validator.ripe.net/api/v1/validity/{asn_clean}/{prefix}"
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "prefix": prefix,
                        "asn": asn_clean,
                        "valid": data.get("validated_route", {})
                        .get("validity", {})
                        .get("status")
                        == "valid",
                        "details": data,
                    }
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_bgp_status(self, resource: str) -> Dict:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"https://stat.ripe.net/data/bgp-state/data.json?resource={resource}"
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", {})
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_announced_prefixes(self, asn: int) -> List[str]:
        try:
            asn_clean = asn if isinstance(asn, int) else int(str(asn).replace("AS", ""))
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"https://stat.ripe.net/data/announced-prefixes/data.json?asn={asn_clean}"
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    prefixes = data.get("data", {}).get("prefixes", [])
                    return [p.get("prefix") for p in prefixes]
                return []
        except Exception:
            return []

    async def get_peering_info(self, asn: int) -> Dict:
        try:
            asn_clean = asn if isinstance(asn, int) else int(str(asn).replace("AS", ""))
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.peeringdb_base}/net?asn={asn_clean}"
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return {"data": data.get("data", [])}
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_ix_list(self) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.peeringdb_base}/ix"
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", [])
                return []
        except Exception:
            return []

    async def get_abuse_contact(self, ip: str) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for rir_name, base_url in self.rir_endpoints.items():
                    url = f"{base_url}/ip/{ip}"
                    response = await client.get(
                        url, headers=self.headers, follow_redirects=True
                    )
                    if response.status_code == 200:
                        data = response.json()
                        for entity in data.get("entities", []):
                            for role in entity.get("roles", []):
                                if role == "abuse":
                                    for email in entity.get("vcardArray", []):
                                        if isinstance(email, list) and len(email) >= 3:
                                            if email[0] == "email":
                                                return email[2]
                        return None
            return None
        except Exception:
            return None

    async def get_asn_neighbors(self, asn: int) -> Dict:
        try:
            asn_clean = asn if isinstance(asn, int) else int(str(asn).replace("AS", ""))
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"https://stat.ripe.net/data/asn-neighbours/data.json?asn={asn_clean}"
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", {})
                return {}
        except Exception:
            return {}

    async def get_prefix_history(self, prefix: str) -> Dict:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"https://stat.ripe.net/data/prefix-overview/data.json?prefix={prefix}"
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", {})
                return {}
        except Exception:
            return {}


peerglass_service = PeerGlassService()
