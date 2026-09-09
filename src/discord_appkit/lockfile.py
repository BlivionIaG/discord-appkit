from __future__ import annotations

import json
from pathlib import Path

from .models import Lockfile

DEFAULT_LOCK = Path("state/ids.lock.json")


def load_lock(path: Path = DEFAULT_LOCK) -> Lockfile:
    if not path.exists():
        return Lockfile()
    return Lockfile.model_validate_json(path.read_text(encoding="utf-8"))


def save_lock(lock: Lockfile, path: Path = DEFAULT_LOCK) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lock.model_dump(), indent=2) + "\n", encoding="utf-8")
