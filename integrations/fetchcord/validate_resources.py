"""Validate FetchCord resource catalogs without Discord credentials.

Copy this next to fetch_cord/resources or run it from a FetchCord checkout:

    python validate_resources.py fetch_cord/resources
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SNOWFLAKE = re.compile(r"^[0-9]{17,20}$")

APP_FILES = ("os.json", "cpus.json", "terminal.json", "motherboards.json")
MIXED_FILES = ("shell.json",)
ASSET_FILES = ("gpus.json", "desktop.json", "windowmanager.json", "system_types.json")


def _patterns(value: object, path: str, *, allow_scalar: bool) -> None:
    if isinstance(value, str):
        if not allow_scalar:
            raise SystemExit(f"{path}: expected a list of patterns")
        return
    if not isinstance(value, list) or not value:
        raise SystemExit(f"{path}: expected a non-empty list of patterns")
    for pattern in value:
        if not isinstance(pattern, str) or not pattern:
            raise SystemExit(f"{path}: pattern must be a non-empty string")
        try:
            re.compile(pattern)
        except re.error as exc:
            raise SystemExit(f"{path}: invalid regex {pattern!r}: {exc}") from exc


def validate(resources: Path) -> None:
    if not resources.is_dir():
        raise SystemExit(f"not a directory: {resources}")
    for name in APP_FILES + MIXED_FILES + ASSET_FILES:
        path = resources / name
        if not path.is_file():
            raise SystemExit(f"missing {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not data:
            raise SystemExit(f"{name}: expected a non-empty object")
        snowflakes = 0
        for key, value in data.items():
            _patterns(value, f"{name}:{key}", allow_scalar=name in ASSET_FILES)
            if SNOWFLAKE.match(str(key)):
                snowflakes += 1
        if name in APP_FILES and snowflakes != len(data):
            raise SystemExit(f"{name}: every key must be a Discord application id")
        if name in MIXED_FILES and snowflakes < 1:
            raise SystemExit(f"{name}: expected at least one application id key")
    print(f"ok {len(APP_FILES + MIXED_FILES + ASSET_FILES)} catalog file(s)")


if __name__ == "__main__":
    validate(Path(sys.argv[1] if len(sys.argv) > 1 else "fetch_cord/resources"))
