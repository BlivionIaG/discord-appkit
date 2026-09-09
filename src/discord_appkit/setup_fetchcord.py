"""Public FetchCord catalog contract.

discord-appkit publishes application catalogs. FetchCord pulls that public
export and merges it into ``fetch_cord/resources``. No Discord token is
required for the sync.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import yaml

from .adapters.fetchcord import emit_fetchcord_testing, merge_resources
from .lockfile import DEFAULT_LOCK, load_lock

RESOURCES_DIR = Path("fetch_cord/resources")
EXPORT_DIR = Path("export/fetchcord")
WORKFLOW_PATH = Path(".github/workflows/sync-discord-assets.yml")
CONFIG_PATH = Path(".github/discord-appkit.yml")

DEFAULT_APPKIT_REPO = "BlivionIaG/discord-appkit"
DEFAULT_FETCHCORD_REPO = "fetchcord/FetchCord"

CALLER_WORKFLOW = """name: sync-discord-assets

# Installed by discord-appkit.
# Pulls published catalogs from the public appkit repo and merges them
# into fetch_cord/resources. No Discord token. No private checkout.
on:
  workflow_dispatch:
  schedule:
    - cron: "0 6 * * 1"

jobs:
  sync:
    if: github.repository == '__FETCHCORD_REPO__'
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - name: pull published catalogs
        env:
          CATALOG_URL: https://raw.githubusercontent.com/__APPKIT_REPO__/__APPKIT_REF__/export/fetchcord
        run: |
          set -euo pipefail
          mkdir -p /tmp/appkit-export
          curl -fsSL "$CATALOG_URL/index.json" -o /tmp/appkit-export/index.json
          python - <<'PY'
          import json, os, urllib.request
          from pathlib import Path

          base = os.environ["CATALOG_URL"].rstrip("/")
          index = json.loads(Path("/tmp/appkit-export/index.json").read_text(encoding="utf-8"))
          export = Path("/tmp/appkit-export")
          for name in index["files"]:
              if not name.endswith(".json") or "/" in name or name == "index.json":
                  raise SystemExit(f"refusing unexpected catalog file: {name}")
              urllib.request.urlretrieve(f"{base}/{name}", export / name)

          dest = Path("fetch_cord/resources")
          for name in index["files"]:
              incoming = json.loads((export / name).read_text(encoding="utf-8"))
              path = dest / name
              current = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
              if not isinstance(current, dict):
                  current = {}
              merged = {**current, **incoming}
              path.write_text(json.dumps(merged, indent=4) + "\\n", encoding="utf-8")
              print(f"merged {name}")
          PY

      - name: open pull request if catalogs changed
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          git config user.name "discord-appkit"
          git config user.email "appkit@users.noreply.github.com"
          git add fetch_cord/resources
          if git diff --cached --quiet; then
            echo "catalogs already match the published export"
            exit 0
          fi
          branch="appkit/sync-assets-${GITHUB_RUN_ID}"
          git checkout -b "$branch"
          git commit -m "chore: sync Discord catalogs from discord-appkit"
          git push origin "HEAD:refs/heads/${branch}"
          gh pr create --base "${GITHUB_REF_NAME}" --head "$branch" \\
            --title "chore: sync Discord catalogs from discord-appkit" \\
            --body "Pulled from the public discord-appkit export. No tokens."
"""


def current_ref() -> str:
    try:
        ref = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "master"
    if not ref or ref == "HEAD":
        return "master"
    return ref


def catalog_url(appkit_repo: str, appkit_ref: str) -> str:
    return f"https://raw.githubusercontent.com/{appkit_repo}/{appkit_ref}/export/fetchcord"


def resources_dir(checkout: Path) -> Path:
    path = checkout / RESOURCES_DIR
    if not path.is_dir():
        raise FileNotFoundError(f"not a FetchCord checkout (missing {RESOURCES_DIR}): {checkout}")
    return path


def publish_export(out: Path = EXPORT_DIR, lock_path: Path = DEFAULT_LOCK) -> list[str]:
    """Write the public catalog FetchCord pulls."""
    emitted = emit_fetchcord_testing(load_lock(lock_path))
    if not emitted:
        raise ValueError("lockfile has no FetchCord application catalogs to publish")
    out.mkdir(parents=True, exist_ok=True)
    names = sorted(emitted)
    for name in names:
        (out / name).write_text(json.dumps(emitted[name], indent=4) + "\n", encoding="utf-8")
    index = {
        "version": 1,
        "files": names,
    }
    (out / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return names


def sync_checkout(checkout: Path, lock_path: Path = DEFAULT_LOCK) -> list[str]:
    """Declare lockfile application catalogs into a FetchCord resources directory."""
    lock = load_lock(lock_path)
    emitted = emit_fetchcord_testing(lock)
    if not emitted:
        raise ValueError("lockfile has no FetchCord application catalogs to sync")
    return merge_resources(resources_dir(checkout), emitted)


def render_config(appkit_repo: str, appkit_ref: str) -> str:
    payload = {
        "version": 1,
        "contract": "public catalog pull",
        "resources": RESOURCES_DIR.as_posix(),
        "catalog": catalog_url(appkit_repo, appkit_ref),
    }
    header = (
        "# Written by discord-appkit.\n"
        "# Public catalog URL. Do not store tokens here.\n"
    )
    return header + yaml.safe_dump(payload, sort_keys=False)


def render_workflow(appkit_repo: str, appkit_ref: str, fetchcord_repo: str) -> str:
    text = (
        CALLER_WORKFLOW.replace("__FETCHCORD_REPO__", fetchcord_repo)
        .replace("__APPKIT_REPO__", appkit_repo)
        .replace("__APPKIT_REF__", appkit_ref)
    )
    if "secrets.DISCORD_USER_TOKEN" in text or "APPKIT_DISPATCH_TOKEN" in text:
        raise ValueError("FetchCord sync must not reference tokens")
    return text


def setup_checkout(
    checkout: Path,
    appkit_repo: str = DEFAULT_APPKIT_REPO,
    appkit_ref: str = "master",
    fetchcord_repo: str = DEFAULT_FETCHCORD_REPO,
    sync: bool = False,
    lock_path: Path = DEFAULT_LOCK,
) -> list[Path]:
    resources_dir(checkout)
    written: list[Path] = []

    config = checkout / CONFIG_PATH
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(render_config(appkit_repo, appkit_ref), encoding="utf-8")
    written.append(config)

    workflow = checkout / WORKFLOW_PATH
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(render_workflow(appkit_repo, appkit_ref, fetchcord_repo), encoding="utf-8")
    written.append(workflow)

    if sync:
        sync_checkout(checkout, lock_path)
    return written
