from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .models import DiscordApplication, Lockfile


@dataclass
class Action:
    kind: str
    name: str
    detail: str


@dataclass
class Plan:
    actions: list[Action] = field(default_factory=list)

    def add(self, kind: str, name: str, detail: str = "") -> None:
        self.actions.append(Action(kind, name, detail))

    def render(self) -> str:
        if not self.actions:
            return "No changes."
        lines = [f"{a.kind:10} {a.name}  {a.detail}".rstrip() for a in self.actions]
        return "\n".join(lines) + "\n"


def build_plan(
    manifests: list[DiscordApplication],
    lock: Lockfile,
    repo_root: Path,
) -> Plan:
    plan = Plan()
    known = set(lock.applications)
    wanted = {m.metadata.name for m in manifests}

    for name in sorted(known - wanted):
        plan.add("orphan", name, "in lockfile but no manifest")

    for manifest in manifests:
        name = manifest.metadata.name
        entry = lock.applications.get(name)
        pinned = manifest.spec.existingId
        if entry is None:
            if pinned:
                plan.add("bind", name, f"use existing application {pinned}")
            else:
                plan.add("create", name, manifest.spec.description)
        elif pinned and entry.application_id != pinned:
            plan.add("rebind", name, f"{entry.application_id} -> {pinned}")
        else:
            plan.add("keep", name, entry.application_id)

        for asset in manifest.spec.assets:
            path = repo_root / asset.file
            exists = path.is_file()
            locked = entry.assets.get(asset.name) if entry else None
            if not exists:
                plan.add("missing", f"{name}/{asset.name}", asset.file)
            elif locked is None:
                plan.add("upload", f"{name}/{asset.name}", asset.file)
            else:
                plan.add("asset", f"{name}/{asset.name}", "present in lockfile (hash check later)")
    return plan
