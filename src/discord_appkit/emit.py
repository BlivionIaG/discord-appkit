from __future__ import annotations

import json

from .models import Lockfile


def emit_lock(lock: Lockfile) -> dict:
    """Consumer-neutral snapshot of bound application IDs and labels."""
    return lock.model_dump(mode="json")


def render_lock(lock: Lockfile) -> str:
    return json.dumps(emit_lock(lock), indent=2) + "\n"
