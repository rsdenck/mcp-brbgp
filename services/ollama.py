import requests
import json
from typing import Optional, Dict, Any
from config import is_ollama_enabled, get_ollama_url, get_ollama_model


class OllamaService:
    def __init__(self):
        self.enabled = is_ollama_enabled()
        self.base_url = get_ollama_url()
        self.model = get_ollama_model()

    def is_available(self) -> bool:
        if not self.enabled:
            return False
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def chat(self, message: str, system_prompt: str = None) -> Optional[str]:
        if not self.is_available():
            return None

        try:
            payload = {"model": self.model, "messages": []}

            if system_prompt:
                payload["messages"].append({"role": "system", "content": system_prompt})

            payload["messages"].append({"role": "user", "content": message})

            response = requests.post(
                f"{self.base_url}/api/chat", json=payload, timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content")
        except Exception as e:
            print(f"Ollama error: {e}")

        return None

    def analyze_incident(self, incident_data: Dict) -> str:
        system_prompt = """Você é um assistente de análise de rede BGP. 
Analise incidentes de rede e forneça insights sobre possíveis causas e impactos.
Responda em português brasileiro de forma clara e concisa."""

        message = f"""Analise este incidente BGP:

Tipo: {incident_data.get("type", "desconhecido")}
ASN: {incident_data.get("asn", "N/A")}
Prefixo: {incident_data.get("prefix", "N/A")}
Mensagem: {incident_data.get("message", "N/A")}
Severidade: {incident_data.get("severity", "N/A")}

Forneça uma análise técnica."""

        result = self.chat(message, system_prompt)
        return result or "Análise não disponível - Ollama não está configurado"

    def get_asn_info(self, asn: int, asn_data: Dict) -> str:
        system_prompt = """Você é um assistente de informações de rede. 
Forneça informações sobre ASNs brasileiros de forma clara."""

        message = f"""Forneça informações sobre o ASN {asn}:

Nome: {asn_data.get("name", "Desconhecido")}
País: {asn_data.get("country", "BR")}
Descrição: {asn_data.get("description", "Não disponível")}

Este é um ASN brasileiro. Forneça contexto sobre o tipo de organização (ISP, empresa, etc)."""

        result = self.chat(message, system_prompt)
        return result or "Informação não disponível"


ollama = OllamaService()
