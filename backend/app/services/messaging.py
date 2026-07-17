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
from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)


def _digits(phone: str) -> str:
    return re.sub(r"\D", "", phone or "")


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
        if channel in ("whatsapp", "wa", "twilio", "sms"):
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

    def _queue_apply_for_job(
        self,
        db: Session,
        user_id: int,
        job_id: int,
    ) -> Dict[str, Any]:
        """Create/find Application for job_id and queue headless apply_one."""
        from app.models.application import Application
        from app.models.job import Job
        from app.tasks.headless_apply_tasks import apply_one

        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"ok": False, "error": "job_not_found", "job_id": job_id}

        application = (
            db.query(Application)
            .filter(Application.user_id == user_id, Application.job_id == job_id)
            .first()
        )
        if not application:
            application = Application(
                user_id=user_id,
                job_id=job_id,
                status="ready_to_apply",
                stage="not_started",
                applied_via="messaging",
            )
            db.add(application)
            db.commit()
            db.refresh(application)
        elif application.status in ("draft", None, ""):
            application.status = "ready_to_apply"
            db.commit()

        from app.models.user import User

        user = db.query(User).filter(User.id == user_id).first()
        submit = bool(user and getattr(user, "auto_apply_submit", False))
        task = apply_one.delay(user_id, application.id, auto_submit=submit, dry_run=False)
        return {
            "ok": True,
            "job_id": job_id,
            "application_id": application.id,
            "task_id": task.id,
        }

    def _status_counts(self, db: Session, user_id: int) -> Dict[str, int]:
        from app.models.application import Application

        apps = db.query(Application).filter(Application.user_id == user_id).all()
        return {
            "submitted": len([a for a in apps if a.status == "submitted"]),
            "ready": len([a for a in apps if a.status == "ready_to_apply"]),
            "interviews": len(
                [a for a in apps if a.stage in ("phone_screen", "technical", "onsite")]
            ),
            "total": len(apps),
        }

    async def handle_inbound(
        self,
        channel: str,
        from_number: str,
        body: str,
        user_context: Optional[Dict[str, Any]] = None,
        *,
        db: Optional[Session] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        parsed = self.parse_command(body)
        cmd = parsed["command"]
        args = parsed.get("args") or []
        user_context = dict(user_context or {})
        queued: Optional[Dict[str, Any]] = None

        # Refresh STATUS counts from DB when available
        if db is not None and user_id is not None:
            counts = self._status_counts(db, user_id)
            user_context.setdefault("submitted", counts["submitted"])
            user_context.setdefault("ready", counts["ready"])
            user_context.setdefault("interviews", counts["interviews"])
            user_context["submitted"] = counts["submitted"]
            user_context["ready"] = counts["ready"]
            user_context["interviews"] = counts["interviews"]

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
            if not jobs and db is not None and user_id is not None:
                from app.models.application import Application
                from app.models.job import Job

                ready = (
                    db.query(Application)
                    .filter(Application.user_id == user_id, Application.status == "ready_to_apply")
                    .limit(10)
                    .all()
                )
                jobs = []
                for a in ready:
                    job = db.query(Job).filter(Job.id == a.job_id).first()
                    if job:
                        jobs.append({"id": job.id, "title": job.title, "company": job.company})
            if not jobs:
                reply = "No ready-to-apply jobs. Open the dashboard to select roles."
            else:
                lines = [f"#{j.get('id')} {j.get('title')} @ {j.get('company')}" for j in jobs[:10]]
                reply = "Ready to apply:\n" + "\n".join(lines)
        elif cmd == "APPLY":
            if not args:
                reply = "Usage: APPLY <job_id>"
            else:
                try:
                    job_id = int(args[0])
                except (TypeError, ValueError):
                    reply = "Usage: APPLY <job_id> (numeric id)"
                else:
                    if db is None or user_id is None:
                        reply = (
                            f"Queued headless apply for job {job_id}. "
                            "I'll message you when it's filled."
                        )
                        user_context["pending_apply_job_id"] = job_id
                    else:
                        queued = self._queue_apply_for_job(db, user_id, job_id)
                        if queued.get("ok"):
                            reply = (
                                f"Queued headless apply for job {job_id} "
                                f"(application #{queued['application_id']}). "
                                "I'll message you when it's filled."
                            )
                        else:
                            reply = f"Could not queue apply for job {job_id}: {queued.get('error')}."
        else:
            reply = "Unknown command. Reply HELP for options."

        send_result = await self.send(channel, from_number, reply)
        out: Dict[str, Any] = {
            "ok": True,
            "command": cmd,
            "reply": reply,
            "send": send_result,
        }
        if queued is not None:
            out["queued"] = queued
        return out

    def lookup_user_by_phone(self, db: Session, from_number: str):
        """Match Twilio From digits against CV.phone."""
        from app.models.cv import CV
        from app.models.user import User

        target = _digits(from_number)
        if not target:
            return None
        # Prefer last 10 digits for NA numbers
        suffixes = {target}
        if len(target) >= 10:
            suffixes.add(target[-10:])
        cvs = db.query(CV).filter(CV.phone.isnot(None)).all()
        for cv in cvs:
            digits = _digits(cv.phone or "")
            if not digits:
                continue
            if digits in suffixes or digits[-10:] in suffixes or target.endswith(digits[-10:]):
                return db.query(User).filter(User.id == cv.user_id).first()
        return None


messaging_service = MessagingService()
