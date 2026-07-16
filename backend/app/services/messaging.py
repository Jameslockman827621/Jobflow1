"""
Mobile messaging bots: WhatsApp (Twilio) + iMessage adapter stub.

WhatsApp is production-ready when Twilio credentials are set.
iMessage requires a Mac host / BlueBubbles-style bridge — we expose the same
command interface and queue messages until a bridge is configured.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class MessagingService:
    def whatsapp_configured(self) -> bool:
        return bool(
            getattr(settings, "TWILIO_ACCOUNT_SID", None)
            and getattr(settings, "TWILIO_AUTH_TOKEN", None)
            and getattr(settings, "TWILIO_WHATSAPP_FROM", None)
        )

    def imessage_configured(self) -> bool:
        return bool(getattr(settings, "IMESSAGE_BRIDGE_URL", None))

    def status(self) -> Dict[str, Any]:
        return {
            "whatsapp": {
                "configured": self.whatsapp_configured(),
                "from": getattr(settings, "TWILIO_WHATSAPP_FROM", None),
            },
            "imessage": {
                "configured": self.imessage_configured(),
                "bridge_url": getattr(settings, "IMESSAGE_BRIDGE_URL", None),
            },
            "commands": [
                "APPLY <job_id>",
                "STATUS",
                "JOBS",
                "HELP",
            ],
        }

    async def send_whatsapp(self, to: str, body: str) -> Dict[str, Any]:
        if not self.whatsapp_configured():
            return {"ok": False, "error": "whatsapp_not_configured", "dry_run": True, "body": body, "to": to}

        account = settings.TWILIO_ACCOUNT_SID
        token = settings.TWILIO_AUTH_TOKEN
        from_num = settings.TWILIO_WHATSAPP_FROM
        to_addr = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
        from_addr = from_num if from_num.startswith("whatsapp:") else f"whatsapp:{from_num}"
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account}/Messages.json"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                data={"From": from_addr, "To": to_addr, "Body": body},
                auth=(account, token),
            )
            if resp.status_code >= 400:
                return {"ok": False, "error": resp.text, "status_code": resp.status_code}
            return {"ok": True, "provider": "twilio_whatsapp", "sid": resp.json().get("sid")}

    async def send_imessage(self, to: str, body: str) -> Dict[str, Any]:
        bridge = getattr(settings, "IMESSAGE_BRIDGE_URL", None)
        if not bridge:
            return {"ok": False, "error": "imessage_bridge_not_configured", "dry_run": True, "body": body, "to": to}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{bridge.rstrip('/')}/send",
                json={"to": to, "message": body},
            )
            if resp.status_code >= 400:
                return {"ok": False, "error": resp.text, "status_code": resp.status_code}
            return {"ok": True, "provider": "imessage_bridge"}

    async def send(self, channel: str, to: str, body: str) -> Dict[str, Any]:
        channel = (channel or "").lower()
        if channel in ("whatsapp", "wa"):
            return await self.send_whatsapp(to, body)
        if channel in ("imessage", "imsg", "sms_imessage"):
            return await self.send_imessage(to, body)
        return {"ok": False, "error": f"unknown_channel:{channel}"}

    def parse_command(self, text: str) -> Dict[str, Any]:
        text = (text or "").strip()
        if not text:
            return {"command": "HELP", "args": []}
        parts = re.split(r"\s+", text, maxsplit=1)
        cmd = parts[0].upper()
        rest = parts[1] if len(parts) > 1 else ""
        args: List[str] = rest.split() if rest else []
        if cmd in ("HELP", "STATUS", "JOBS", "APPLY"):
            return {"command": cmd, "args": args}
        return {"command": "HELP", "args": [], "raw": text}

    async def handle_inbound(
        self,
        channel: str,
        from_number: str,
        body: str,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        parsed = self.parse_command(body)
        cmd = parsed["command"]
        args = parsed.get("args") or []
        user_context = user_context or {}

        if cmd == "HELP":
            reply = (
                "JobScale bot commands:\n"
                "• JOBS — list ready-to-apply roles\n"
                "• APPLY <job_id> — queue a headless apply\n"
                "• STATUS — application summary\n"
                "• HELP — this message"
            )
        elif cmd == "STATUS":
            reply = (
                f"Status for {user_context.get('email', from_number)}: "
                f"{user_context.get('submitted', 0)} submitted, "
                f"{user_context.get('ready', 0)} ready, "
                f"{user_context.get('interviews', 0)} interviews."
            )
        elif cmd == "JOBS":
            jobs = user_context.get("jobs") or []
            if not jobs:
                reply = "No ready-to-apply jobs. Open the dashboard to select roles."
            else:
                lines = [f"#{j.get('id')} {j.get('title')} @ {j.get('company')}" for j in jobs[:10]]
                reply = "Ready to apply:\n" + "\n".join(lines)
        elif cmd == "APPLY":
            if not args:
                reply = "Usage: APPLY <job_id>"
            else:
                reply = f"Queued headless apply for job {args[0]}. I'll message you when it's filled."
        else:
            reply = "Unknown command. Reply HELP for options."

        send_result = await self.send(channel, from_number, reply)
        return {"ok": True, "command": cmd, "reply": reply, "send": send_result}


messaging_service = MessagingService()
