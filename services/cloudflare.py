import requests
import json
from typing import Optional, Dict, Any
from config import get_cloudflare_token, get_cloudflare_account_id


class CloudflareService:
    def __init__(self):
        self.token = get_cloudflare_token()
        self.account_id = get_cloudflare_account_id()
        self.base_url = "https://api.cloudflare.com/client/v4"

    def verify_token(self) -> bool:
        if not self.token:
            return False
        try:
            response = requests.get(
                f"{self.base_url}/tokens/verify",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            return response.status_code == 200 and response.json().get("success")
        except:
            return False

    def get_radar_asn(self, asn: int) -> Optional[Dict]:
        if not self.token:
            return None
        try:
            response = requests.get(
                f"{self.base_url}/accounts/{self.account_id}/radar/entities/asn/{asn}",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error fetching ASN data: {e}")
        return None

    def get_radar_prefixes(self, prefix: str) -> Optional[Dict]:
        if not self.token:
            return None
        try:
            response = requests.get(
                f"{self.base_url}/accounts/{self.account_id}/radar/entities/ip_prefix/{prefix}",
                headers={"Authorization": f"Bearer {self.token}"},
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None

    def get_analytics(
        self, asn: int, start: str = None, end: str = None
    ) -> Optional[Dict]:
        if not self.token:
            return None
        try:
            params = {}
            if start:
                params["dateStart"] = start
            if end:
                params["dateEnd"] = end

            response = requests.get(
                f"{self.base_url}/accounts/{self.account_id}/radar/entities/asn/{asn}/timeseries",
                headers={"Authorization": f"Bearer {self.token}"},
                params=params,
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None


cloudflare = CloudflareService()
