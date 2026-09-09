from __future__ import annotations

import json
import re
from pathlib import Path

from .models import AssetLock, LockEntry, Lockfile

SNOWFLAKE = re.compile(r"^[0-9]{17,20}$")
FILE_CATEGORY = {"os.json": "distro", "cpus.json": "cpu", "terminal.json": "terminal", "motherboards.json": "motherboard"}
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
        if any(h in blob for h in hints):
            return vendor
    return None


def load_testing_catalog(catalog_dir: Path) -> dict[str, dict]:
    out = {}
    for fname in FILE_CATEGORY:
        path = catalog_dir / fname
        if path.exists():
            out[fname] = json.loads(path.read_text(encoding="utf-8"))
    if not out:
        raise FileNotFoundError(f"no testing catalog json in {catalog_dir}")
    return out


def load_v2_map(path: Path) -> dict[str, dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    inverted: dict[str, dict] = {}
    for category, bucket in raw.items():
        if category == "map" or not isinstance(bucket, dict):
            continue
        cat_file = {"distro": "os.json", "cpu": "cpus.json", "terminal": "terminal.json", "motherboard": "motherboards.json"}.get(category)
        if not cat_file:
            continue
        target = inverted.setdefault(cat_file, {})
        def walk(obj):
            for key, val in obj.items():
                if isinstance(val, dict):
                    walk(val)
                elif SNOWFLAKE.match(str(val)):
                    target.setdefault(str(val), []).append(key)
        walk(bucket)
    return inverted


def catalogs_to_lock(catalogs: dict[str, dict]) -> Lockfile:
    lock = Lockfile()
    used: set[str] = set()
    for fname, data in catalogs.items():
        category = FILE_CATEGORY[fname]
        for app_id, patterns in data.items():
            if not SNOWFLAKE.match(str(app_id)):
                continue
            keys = [str(k) for k in (patterns if isinstance(patterns, list) else [patterns])]
            base = f"fetchcord-{category}-{_slug(keys[0] if keys else app_id)}"
            name, i = base, 2
            while name in used:
                name = f"{base}-{i}"
                i += 1
            used.add(name)
            asset_name = _slug(keys[0] if keys else "icon").replace("-", "")[:32] or "icon"
            asset_file = f"assets/{category}/{_slug(keys[0] if keys else app_id)}.png"
            lock.applications[name] = LockEntry(
                name=name, category=category, application_id=str(app_id), keys=keys,
                vendor=_vendor(keys) if category == "cpu" else None,
                assets={asset_name: AssetLock(file=asset_file)},
            )
    return lock


def lock_to_manifest_yaml(entry: LockEntry) -> str:
    lines = ["apiVersion: appkit.discord/v1", "kind: DiscordApplication", "metadata:",
             f"  name: {entry.name}", f"  category: {entry.category}"]
    if entry.vendor:
        lines.append(f"  vendor: {entry.vendor}")
    lines.append("  keys:")
    for key in entry.keys:
        lines.append(f"    - {json.dumps(key)}")
    lines += ["spec:", f"  description: {json.dumps('FetchCord Rich Presence — ' + entry.category)}",
              f'  existingId: "{entry.application_id}"', "  flags:", "    richPresence: true", "  assets:"]
    for asset_name, raw in entry.assets.items():
        file = raw if isinstance(raw, str) else raw.file
        lines += [f"    - name: {asset_name}", "      type: rich", f"      file: {file}"]
    return "\n".join(lines) + "\n"


def write_manifests(lock: Lockfile, apps_dir: Path) -> int:
    apps_dir.mkdir(parents=True, exist_ok=True)
    for entry in lock.applications.values():
        (apps_dir / f"{entry.name}.yaml").write_text(lock_to_manifest_yaml(entry), encoding="utf-8")
    return len(lock.applications)
