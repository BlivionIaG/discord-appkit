from __future__ import annotations

from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from .models import DiscordApplication

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "app.schema.json"


def _schema() -> dict:
    import json

    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_manifests(apps_dir: Path) -> list[DiscordApplication]:
    validator = Draft202012Validator(_schema())
    manifests: list[DiscordApplication] = []
    paths = sorted(apps_dir.glob("*.yaml")) + sorted(apps_dir.glob("*.yml"))
    if not paths:
        raise FileNotFoundError(f"no manifests in {apps_dir}")
    for path in paths:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(raw), key=lambda e: list(e.path))
        if errors:
            msgs = "; ".join(f"{list(e.path)}: {e.message}" for e in errors)
            raise ValueError(f"{path}: {msgs}")
        app = DiscordApplication.model_validate(raw)
        app.source = path
        manifests.append(app)
    names = [m.metadata.name for m in manifests]
    if len(names) != len(set(names)):
        raise ValueError(f"duplicate metadata.name in {apps_dir}")
    return manifests
