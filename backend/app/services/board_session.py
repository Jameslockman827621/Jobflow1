"""Load / save Playwright storage_state for board logins."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.board_session import BoardSession

SUPPORTED_BOARDS = frozenset({"linkedin", "indeed"})

# Auth cookie signals — without these, Easy Apply will hit login walls
REQUIRED_COOKIES = {
    "linkedin": ("li_at",),
    "indeed": ("PPID", "CTK", "INDEED_CSRF_TOKEN", "indeed_rcc", "SOC"),
}

BOARD_HOME = {
    "linkedin": "https://www.linkedin.com/feed/",
    "indeed": "https://www.indeed.com/",
}


def cookies_to_storage_state(cookies: list, board: str) -> Dict[str, Any]:
    """Convert Chrome/extension cookie objects into Playwright storage_state."""
    board = (board or "").lower().strip()
    if board not in SUPPORTED_BOARDS:
        raise ValueError(f"Unsupported board: {board}")
    if not isinstance(cookies, list) or not cookies:
        raise ValueError("cookies must be a non-empty list")

    out = []
    names = set()
    for c in cookies:
        if not isinstance(c, dict) or not c.get("name"):
            continue
        name = str(c["name"])
        names.add(name)
        domain = c.get("domain") or (
            ".linkedin.com" if board == "linkedin" else ".indeed.com"
        )
        # Playwright wants expires as float seconds; chrome uses expirationDate
        expires = c.get("expires")
        if expires is None and c.get("expirationDate") is not None:
            expires = float(c["expirationDate"])
        if expires is None:
            expires = -1
        same_site = c.get("sameSite") or c.get("same_site") or "Lax"
        if isinstance(same_site, str):
            # Chrome: no_restriction | lax | strict | unspecified
            ss = same_site.lower().replace("_", "")
            if ss in ("norestriction", "none"):
                same_site = "None"
            elif ss == "strict":
                same_site = "Strict"
            else:
                same_site = "Lax"
        out.append(
            {
                "name": name,
                "value": str(c.get("value") or ""),
                "domain": domain,
                "path": c.get("path") or "/",
                "expires": expires,
                "httpOnly": bool(c.get("httpOnly", c.get("http_only", False))),
                "secure": bool(c.get("secure", True)),
                "sameSite": same_site,
            }
        )

    if not out:
        raise ValueError("No valid cookies provided")

    required = REQUIRED_COOKIES.get(board) or ()
    if board == "linkedin":
        if "li_at" not in names:
            raise ValueError(
                "LinkedIn session incomplete — missing li_at. "
                "Log into LinkedIn in Chrome, then Connect again."
            )
    elif board == "indeed":
        if not any(n in names for n in required):
            raise ValueError(
                "Indeed session incomplete — log into Indeed in Chrome, then Connect again."
            )

    return {"cookies": out, "origins": []}


def connect_status(db: Session, user_id: int) -> Dict[str, Any]:
    """Dashboard-facing connect status for LinkedIn / Indeed."""
    boards = {}
    for board in sorted(SUPPORTED_BOARDS):
        row = get_board_session(db, user_id, board)
        cookie_names = []
        if row:
            state = storage_state_dict(row) or {}
            cookie_names = [c.get("name") for c in (state.get("cookies") or []) if c.get("name")]
        boards[board] = {
            "connected": bool(row and row.is_valid),
            "label": row.label if row else None,
            "last_used_at": row.last_used_at.isoformat() if row and row.last_used_at else None,
            "updated_at": row.updated_at.isoformat() if row and getattr(row, "updated_at", None) else None,
            "cookie_count": len(cookie_names),
            "has_auth_cookie": (
                ("li_at" in cookie_names)
                if board == "linkedin"
                else any(n in cookie_names for n in REQUIRED_COOKIES["indeed"])
            ),
            "connect_url": BOARD_HOME[board],
        }
    return {
        "boards": boards,
        "extension_required": True,
        "method": "extension_cookie_sync",
        "message": (
            "Install the JobScale extension, click Connect, log into the board, "
            "and we sync your session for Easy Apply."
        ),
    }


def upsert_board_session(
    db: Session,
    user_id: int,
    board: str,
    storage_state: Dict[str, Any],
    *,
    label: Optional[str] = None,
    expires_at: Optional[datetime] = None,
) -> BoardSession:
    board = (board or "").lower().strip()
    if board not in SUPPORTED_BOARDS:
        raise ValueError(f"Unsupported board: {board}")
    if not isinstance(storage_state, dict):
        raise ValueError("storage_state must be an object")

    row = (
        db.query(BoardSession)
        .filter(BoardSession.user_id == user_id, BoardSession.board == board)
        .first()
    )
    payload = json.dumps(storage_state)
    if row:
        row.storage_state_json = payload
        row.label = label or row.label
        row.expires_at = expires_at
        row.is_valid = 1
    else:
        row = BoardSession(
            user_id=user_id,
            board=board,
            storage_state_json=payload,
            label=label,
            expires_at=expires_at,
            is_valid=1,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_board_session(db: Session, user_id: int, board: str) -> Optional[BoardSession]:
    board = (board or "").lower().strip()
    return (
        db.query(BoardSession)
        .filter(
            BoardSession.user_id == user_id,
            BoardSession.board == board,
            BoardSession.is_valid == 1,
        )
        .first()
    )


def delete_board_session(db: Session, user_id: int, board: str) -> bool:
    row = get_board_session(db, user_id, board)
    if not row:
        # also delete invalid rows
        row = (
            db.query(BoardSession)
            .filter(BoardSession.user_id == user_id, BoardSession.board == board)
            .first()
        )
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def list_board_sessions(db: Session, user_id: int) -> list:
    rows = db.query(BoardSession).filter(BoardSession.user_id == user_id).all()
    out = []
    for r in rows:
        out.append(
            {
                "board": r.board,
                "label": r.label,
                "is_valid": bool(r.is_valid),
                "expires_at": r.expires_at.isoformat() if r.expires_at else None,
                "last_used_at": r.last_used_at.isoformat() if r.last_used_at else None,
                "has_storage_state": bool(r.storage_state_json),
                "updated_at": r.updated_at.isoformat() if getattr(r, "updated_at", None) else None,
            }
        )
    return out


def storage_state_dict(row: BoardSession) -> Optional[Dict[str, Any]]:
    if not row or not row.storage_state_json:
        return None
    try:
        data = json.loads(row.storage_state_json)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def write_storage_state_file(row: BoardSession) -> Optional[str]:
    """Write storage_state to a temp JSON file for Playwright new_context."""
    data = storage_state_dict(row)
    if not data:
        return None
    fd, path = tempfile.mkstemp(prefix=f"jobscale_{row.board}_", suffix=".json")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


def touch_last_used(db: Session, row: BoardSession) -> None:
    row.last_used_at = datetime.utcnow()
    db.commit()
