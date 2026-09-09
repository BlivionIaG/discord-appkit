"""FetchCord catalog adapter.

Core appkit does not know FetchCord. This module is the only place that
understands FetchCord resource files and the 2.x ID map.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from ..models import AssetLock, LockEntry, Lockfile

SNOWFLAKE = re.compile(r"^[0-9]{17,20}$")

# Catalogs whose keys are Discord application IDs. Safe to rewrite from the lockfile.
APP_CATALOGS = {
    "distro": "os.json",
    "cpu": "cpus.json",
    "terminal": "terminal.json",
    "motherboard": "motherboards.json",
}

# Mixed catalogs: snowflake keys are application IDs; other keys are asset names.
MIXED_CATALOGS = {
    "shell": "shell.json",
}

# Owned by FetchCord as asset-name tables. Never rewritten by emit.
ASSET_CATALOGS = (
    "gpus.json",
    "desktop.json",
    "windowmanager.json",
    "system_types.json",
)

FILE_CATEGORY = {filename: category for category, filename in {**APP_CATALOGS, **MIXED_CATALOGS}.items()}

FETCHCORD_V2_MAP = {
    "GPU:": "gpu",
    "CPU:": "cpu",
    "Terminal:": "terminal",
    "Motherboard:": "motherboard",
    "Host:": "motherboard",
    "Shell:": "shell",
    "OS:": "distro",
    "DE:": "desktop",
    "WM:": "windowmanager",
    "Version:": "version",
}

VENDOR_HINTS = [
    ("amd", ("ryzen", "athlon", "fx apu", "a4 ", "a6 ", "a8 ", "a9 ", "a10", "a12")),
    ("intel", ("intel", "pentium", "celeron", "xeon", "core 2")),
]


def _slug(text: str) -> str:
    text = re.sub(r"^\(\?i\)", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text[:40] or "item"


def _vendor(keys: list[str]) -> str | None:
    blob = " ".join(keys).lower()
    for vendor, hints in VENDOR_HINTS:
        if any(hint in blob for hint in hints):
            return vendor
    return None


def _is_snowflake(value: object) -> bool:
    return bool(SNOWFLAKE.match(str(value)))


def load_testing_catalog(catalog_dir: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in sorted(catalog_dir.glob("*.json")):
        if path.name not in FILE_CATEGORY and path.name not in ASSET_CATALOGS:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            out[path.name] = data
    if not out:
        raise FileNotFoundError(f"no FetchCord catalog json in {catalog_dir}")
    return out


def load_v2_map(path: Path) -> dict[str, dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    inverted: dict[str, dict] = {}
    for category, bucket in raw.items():
        if category == "map" or not isinstance(bucket, dict):
            continue
        cat_file = {**APP_CATALOGS, **MIXED_CATALOGS}.get(category)
        if not cat_file:
            continue
        target = inverted.setdefault(cat_file, {})

        def walk(obj: dict, sink: dict) -> None:
            for key, val in obj.items():
                if isinstance(val, dict):
                    walk(val, sink)
                elif _is_snowflake(val):
                    sink.setdefault(str(val), []).append(key)

        walk(bucket, target)
    return inverted


def catalogs_to_lock(catalogs: dict[str, dict], consumer: str = "fetchcord") -> Lockfile:
    lock = Lockfile()
    used: set[str] = set()
    for fname, data in catalogs.items():
        category = FILE_CATEGORY.get(fname)
        if not category or not isinstance(data, dict):
            continue
        for app_id, patterns in data.items():
            if not _is_snowflake(app_id):
                continue
            keys = [str(key) for key in (patterns if isinstance(patterns, list) else [patterns])]
            base = f"{consumer}-{category}-{_slug(keys[0] if keys else str(app_id))}"
            name, index = base, 2
            while name in used:
                name = f"{base}-{index}"
                index += 1
            used.add(name)
            asset_name = _slug(keys[0] if keys else "icon").replace("-", "")[:32] or "icon"
            asset_file = f"assets/{category}/{_slug(keys[0] if keys else str(app_id))}.png"
            lock.applications[name] = LockEntry(
                name=name,
                category=category,
                application_id=str(app_id),
                keys=keys,
                vendor=_vendor(keys) if category == "cpu" else None,
                annotations={"consumer": consumer},
                assets={asset_name: AssetLock(file=asset_file)},
            )
    if not lock.applications:
        raise ValueError("no Discord application IDs found in FetchCord catalogs")
    return lock


def lock_to_manifest_yaml(entry: LockEntry, description_prefix: str = "FetchCord Rich Presence") -> str:
    lines = [
        "apiVersion: appkit.discord/v1",
        "kind: DiscordApplication",
        "metadata:",
        f"  name: {entry.name}",
        f"  category: {entry.category}",
    ]
    if entry.vendor:
        lines.append(f"  vendor: {entry.vendor}")
    if entry.annotations:
        lines.append("  annotations:")
        for key, value in entry.annotations.items():
            lines.append(f"    {key}: {json.dumps(value)}")
    lines.append("  keys:")
    for key in entry.keys:
        lines.append(f"    - {json.dumps(key)}")
    lines += [
        "spec:",
        f"  description: {json.dumps(description_prefix + ' — ' + entry.category)}",
        f'  existingId: "{entry.application_id}"',
        "  flags:",
        "    richPresence: true",
        "  assets:",
    ]
    for asset_name, raw in entry.assets.items():
        file = raw if isinstance(raw, str) else raw.file
        lines += [f"    - name: {asset_name}", "      type: rich", f"      file: {file}"]
    return "\n".join(lines) + "\n"


def write_manifests(lock: Lockfile, apps_dir: Path) -> int:
    apps_dir.mkdir(parents=True, exist_ok=True)
    for entry in lock.applications.values():
        (apps_dir / f"{entry.name}.yaml").write_text(lock_to_manifest_yaml(entry), encoding="utf-8")
    return len(lock.applications)


def emit_fetchcord(lock: Lockfile) -> dict:
    """2.x ``fetchcord_ids.json`` shape: category -> key -> application id."""
    out: dict = {"map": FETCHCORD_V2_MAP}
    buckets: dict[str, dict] = defaultdict(dict)
    cpu: dict[str, dict] = defaultdict(dict)
    for entry in lock.applications.values():
        if entry.category in {"bot", "other"}:
            continue
        if entry.category == "cpu":
            vendor = entry.vendor or "unknown"
            for key in entry.keys:
                cpu[vendor][key] = entry.application_id
            continue
        for key in entry.keys:
            buckets[entry.category][key] = entry.application_id
    if cpu:
        buckets["cpu"] = dict(cpu)
    out.update(buckets)
    return out


def emit_fetchcord_testing(lock: Lockfile) -> dict[str, dict]:
    """Testing-branch resource files: application id -> match patterns.

    Only application-id catalogs are emitted. Asset-name catalogs stay in FetchCord.
    """
    files: dict[str, dict] = {}
    catalog_for = {**APP_CATALOGS, **MIXED_CATALOGS}
    for entry in lock.applications.values():
        fname = catalog_for.get(entry.category)
        if not fname or not _is_snowflake(entry.application_id):
            continue
        files.setdefault(fname, {})[entry.application_id] = list(entry.keys)
    return files


def merge_resources(dest: Path, emitted: dict[str, dict], replace: bool = False) -> list[str]:
    """Update consumer catalogs from the lockfile without dropping unmanaged keys.

    Default merge updates application IDs this lockfile knows about and keeps
    every other key already in the destination. ``replace`` rewrites pure
    application-id catalogs from the lockfile alone.
    """
    dest.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    pure = set(APP_CATALOGS.values())
    mixed = set(MIXED_CATALOGS.values())
    for name, content in emitted.items():
        if name not in pure and name not in mixed:
            continue
        path = dest / name
        if path.is_file() and not (replace and name in pure):
            existing = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(existing, dict):
                existing = {}
            merged = {**existing, **content}
        else:
            merged = content
        path.write_text(json.dumps(merged, indent=4) + "\n", encoding="utf-8")
        written.append(name)
    return written
