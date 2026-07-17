"""Redact secrets from log messages (cookies, storage_state, tokens)."""

from __future__ import annotations

import logging
import re

_SENSITIVE = re.compile(
    r"(li_at|JSESSIONID|storage_state|cookie|authorization|bearer|api[_-]?key|secret)"
    r"([\"'=\s:]*)([^\s\"',;]{8,})",
    re.IGNORECASE,
)


def redact_text(text: str) -> str:
    if not text:
        return text
    return _SENSITIVE.sub(r"\1\2[REDACTED]", text)


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = redact_text(record.msg)
            if record.args:
                if isinstance(record.args, dict):
                    record.args = {
                        k: redact_text(v) if isinstance(v, str) else v for k, v in record.args.items()
                    }
                elif isinstance(record.args, tuple):
                    record.args = tuple(
                        redact_text(a) if isinstance(a, str) else a for a in record.args
                    )
        except Exception:
            pass
        return True


def install_redacting_filter() -> None:
    f = RedactingFilter()
    root = logging.getLogger()
    root.addFilter(f)
    for h in root.handlers:
        h.addFilter(f)
