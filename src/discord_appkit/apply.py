from __future__ import annotations

from pathlib import Path
from .discord_api import DiscordPortal
from .hashing import sha256_file
from .models import AssetLock, DiscordApplication, LockEntry, Lockfile


def apply_manifests(manifests: list[DiscordApplication], lock: Lockfile, repo_root: Path, portal: DiscordPortal | None, live: bool) -> Lockfile:
    for manifest in manifests:
        name = manifest.metadata.name
        app_id = manifest.spec.existingId
        if not app_id:
            if live and portal is not None:
                app_id = str(portal.create_application(name, manifest.spec.description)["id"])
            else:
                continue
        assets: dict[str, AssetLock] = {}
        entry = lock.applications.get(name)
        for asset in manifest.spec.assets:
            path = repo_root / asset.file
            prev = entry.asset_sha(asset.name) if entry else None
            digest = sha256_file(path) if path.is_file() else None
            discord_id = None
            if live and portal is not None and path.is_file() and digest != prev:
                discord_id = str(portal.upload_asset(app_id, asset.name, path).get("id") or "") or None
            elif entry and not isinstance(entry.assets.get(asset.name), str):
                raw = entry.assets.get(asset.name)
                if raw and not isinstance(raw, str):
                    discord_id = raw.discord_asset_id
            assets[asset.name] = AssetLock(file=asset.file, sha256=digest, discord_asset_id=discord_id)
        if live and portal is not None and manifest.spec.flags.bot and manifest.spec.commands:
            portal.put_commands(app_id, manifest.spec.commands)
        lock.applications[name] = LockEntry(name=name, category=manifest.metadata.category, application_id=app_id, keys=list(manifest.metadata.keys), vendor=manifest.metadata.vendor, assets=assets)
    return lock
