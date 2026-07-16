"""Encrypt board session storage_state at rest."""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any, Dict, Optional, Union

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

_PREFIX = "enc:v1:"


def _fernet() -> Fernet:
    digest = hashlib.sha256((settings.SECRET_KEY or "jobscale").encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_storage_state(storage_state: Union[str, Dict[str, Any]]) -> str:
    if isinstance(storage_state, dict):
        payload = json.dumps(storage_state, separators=(",", ":"))
    else:
        payload = str(storage_state)
    token = _fernet().encrypt(payload.encode("utf-8")).decode("ascii")
    return f"{_PREFIX}{token}"


def decrypt_storage_state(raw: Optional[str]) -> Optional[str]:
    """Return plaintext JSON string. Supports legacy unencrypted rows."""
    if not raw:
        return None
    if raw.startswith(_PREFIX):
        try:
            plain = _fernet().decrypt(raw[len(_PREFIX) :].encode("ascii"))
            return plain.decode("utf-8")
        except InvalidToken:
            return None
    return raw


def decrypt_storage_state_dict(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    plain = decrypt_storage_state(raw)
    if not plain:
        return None
    try:
        data = json.loads(plain)
        return data if isinstance(data, dict) else None
    except Exception:
        return None
