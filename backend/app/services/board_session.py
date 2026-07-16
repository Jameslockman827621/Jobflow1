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
