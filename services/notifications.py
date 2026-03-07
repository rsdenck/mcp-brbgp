import asyncio
import json
from typing import Dict, Any, Optional
from loguru import logger
import os


class NotificationService:
    def __init__(self):
        self.telegram_enabled = bool(os.getenv("TELEGRAM_BOT_TOKEN"))
        self.whatsapp_enabled = bool(os.getenv("TWILIO_ACCOUNT_SID"))
        self.webhook_enabled = bool(os.getenv("WEBHOOK_URL"))

        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.webhook_url = os.getenv("WEBHOOK_URL", "")

    async def send_notification(
        self, message: str, severity: str = "info", data: Optional[Dict] = None
    ):
        tasks = []

        if self.telegram_enabled:
            tasks.append(self._send_telegram(message, severity))

        if self.whatsapp_enabled:
            tasks.append(self._send_whatsapp(message, severity))

        if self.webhook_enabled:
            tasks.append(self._send_webhook(message, severity, data))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_telegram(self, message: str, severity: str):
        try:
            import aiohttp

            emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
                "info": "🔵",
            }.get(severity, "🔵")

            text = f"{emoji} *{severity.upper()}*\n\n{message}"

            async with aiohttp.ClientSession() as session:
                await session.post(
                    f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage",
                    json={
                        "chat_id": self.telegram_chat_id,
                        "text": text,
                        "parse_mode": "Markdown",
                    },
                )
            logger.info(f"Telegram notification sent: {severity}")
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")

    async def _send_whatsapp(self, message: str, severity: str):
        try:
            from twilio.rest import Client

            client = Client(
                os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN")
            )

            body = f"[{severity.upper()}] {message}"

            await asyncio.to_thread(
                client.messages.create,
                body=body,
                from_=os.getenv("TWILIO_WHATSAPP_FROM"),
                to=os.getenv("TWILIO_WHATSAPP_TO"),
            )
            logger.info(f"WhatsApp notification sent: {severity}")
        except Exception as e:
            logger.error(f"Error sending WhatsApp notification: {e}")

    async def _send_webhook(self, message: str, severity: str, data: Optional[Dict]):
        try:
            import aiohttp

            payload = {
                "message": message,
                "severity": severity,
                "data": data,
                "source": "mcp-brbgp",
            }

            async with aiohttp.ClientSession() as session:
                await session.post(self.webhook_url, json=payload)
            logger.info(f"Webhook notification sent: {severity}")
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")

    async def notify_incident(self, incident: Dict[str, Any]):
        severity = incident.get("severity", "info")
        message = incident.get("message", "")

        await self.send_notification(message, severity, incident)

    async def notify_withdrawal(self, prefix: str, asn: int):
        message = f"🚫 *WITHDRAWAL*\n\nPrefix: `{prefix}`\nOrigin: AS{asn}\n\nDetected by Armazem Radar"
        await self.send_notification(
            message, "medium", {"type": "withdrawal", "prefix": prefix, "asn": asn}
        )

    async def notify_route_leak(self, prefix: str, asn: int):
        message = f"⚠️ *ROUTE LEAK*\n\nPrefix: `{prefix}`\nAffected AS: AS{asn}\n\nPotential route leak detected!"
        await self.send_notification(
            message, "high", {"type": "route_leak", "prefix": prefix, "asn": asn}
        )

    async def notify_prefix_disappear(self, prefix: str):
        message = f"❌ *PREFIX DISAPPEAR*\n\nPrefix: `{prefix}`\n\nPreviously announced prefix has disappeared!"
        await self.send_notification(
            message, "high", {"type": "prefix_disappear", "prefix": prefix}
        )

    async def notify_as_fall(self, asn: int, prefix_count: int):
        message = f"🔴 *AS FALL*\n\nAS: AS{asn}\nAffected Prefixes: {prefix_count}\n\nMultiple withdrawals detected!"
        await self.send_notification(
            message,
            "critical",
            {"type": "as_fall", "asn": asn, "prefix_count": prefix_count},
        )
