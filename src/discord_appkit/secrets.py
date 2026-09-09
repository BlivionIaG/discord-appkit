from __future__ import annotations

import os
import re


class SecretStr:
    """A token that must not appear in logs, reprs, or exception text."""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value

    def reveal(self) -> str:
        return self._value

    def __str__(self) -> str:
        return "***"

    def __repr__(self) -> str:
        return "SecretStr('***')"

    def __bool__(self) -> bool:
        return bool(self._value)


def load_user_token(explicit: str | None = None) -> SecretStr:
    raw = explicit if explicit is not None else os.environ.get("DISCORD_USER_TOKEN", "")
    return SecretStr(raw.strip())


def redact(text: str, secret: str | SecretStr | None) -> str:
    if not secret:
        return text
    value = secret.reveal() if isinstance(secret, SecretStr) else secret
    if not value:
        return text
    redacted = text.replace(value, "***")
    # User tokens are long opaque strings; also scrub anything that looks like one
    # if it was split across a log line.
    if len(value) >= 20:
        redacted = redacted.replace(value[:20], "***")
    return redacted


_TOKEN_ASSIGNMENT = re.compile(
    r"(DISCORD_USER_TOKEN\s*[=:]\s*)(\S+)",
    re.IGNORECASE,
)


def redact_assignments(text: str) -> str:
    return _TOKEN_ASSIGNMENT.sub(r"\1***", text)
