from __future__ import annotations

import json
from pathlib import Path

from .lockfile import DEFAULT_LOCK, load_lock
from .models import LockEntry, Lockfile

EXPORT_PATH = Path("export/catalog.json")


def catalog_from_lock(lock: Lockfile) -> dict:
    applications = []
    for entry in lock.applications.values():
        assets = []
        for name, raw in entry.assets.items():
            file = raw if isinstance(raw, str) else raw.file
            assets.append({"name": name, "file": file})
        applications.append(
            {
                "name": entry.name,
                "applicationId": entry.application_id,
                "category": entry.category,
                "keys": list(entry.keys),
                "vendor": entry.vendor,
                "annotations": dict(entry.annotations),
                "assets": assets,
            }
        )
    applications.sort(key=lambda item: item["name"])
    return {"version": 1, "applications": applications}


def publish_catalog(out: Path = EXPORT_PATH, lock_path: Path = DEFAULT_LOCK) -> Path:
    lock = load_lock(lock_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(catalog_from_lock(lock), indent=2) + "\n", encoding="utf-8")
    return out


def lock_from_catalog(payload: dict) -> Lockfile:
    if payload.get("version") != 1 or not isinstance(payload.get("applications"), list):
        raise ValueError("unsupported catalog")
    lock = Lockfile()
    for item in payload["applications"]:
        name = str(item["name"])
        assets = {asset["name"]: asset["file"] for asset in item.get("assets", [])}
        lock.applications[name] = LockEntry(
            name=name,
            category=str(item.get("category") or "other"),
            application_id=str(item["applicationId"]),
            keys=[str(key) for key in item.get("keys", [])],
            vendor=item.get("vendor"),
            annotations={str(k): str(v) for k, v in (item.get("annotations") or {}).items()},
            assets=assets,
        )
    return lock


def load_catalog(path: Path) -> Lockfile:
    return lock_from_catalog(json.loads(path.read_text(encoding="utf-8")))
