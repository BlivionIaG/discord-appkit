"""FetchCord call contract.

discord-appkit owns Discord applications and assets. The FetchCord org calls
one command, ``appkit fetchcord``, either locally or from CI. The Discord
user token never leaves this repo.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from .adapters.fetchcord import emit_fetchcord_testing, merge_resources
from .lockfile import DEFAULT_LOCK, load_lock

RESOURCES_DIR = Path("fetch_cord/resources")
WORKFLOW_PATH = Path(".github/workflows/deploy-discord-assets.yml")
CONFIG_PATH = Path(".github/discord-appkit.yml")
DISPATCH_EVENT = "fetchcord-deploy"

DEFAULT_APPKIT_REPO = "BlivionIaG/discord-appkit"
DEFAULT_FETCHCORD_REPO = "fetchcord/FetchCord"

CALLER_WORKFLOW = """name: deploy-discord-assets

# Installed by discord-appkit.
# The FetchCord org calls discord-appkit. This file does not deploy Discord
# itself and must not define DISCORD_USER_TOKEN.
on:
  workflow_dispatch:
    inputs:
      apply:
        description: Ask appkit to upload assets to Discord before syncing catalogs
        type: boolean
        default: false
      fetchcord_ref:
        description: FetchCord ref appkit should update
        type: string
        default: testing

jobs:
  call:
    if: github.event_name == 'workflow_dispatch' && github.repository == '__FETCHCORD_REPO__'
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - name: call discord-appkit
        env:
          APPKIT_DISPATCH_TOKEN: ${{ secrets.APPKIT_DISPATCH_TOKEN }}
          APPLY: ${{ inputs.apply }}
          FETCHCORD_REF: ${{ inputs.fetchcord_ref }}
        run: |
          set +x
          if [ -z "$APPKIT_DISPATCH_TOKEN" ]; then
            echo "APPKIT_DISPATCH_TOKEN is not set"
            exit 1
          fi
          python - <<'PY'
          import json, os, urllib.request
          apply = os.environ.get("APPLY", "false") == "true"
          body = json.dumps({
              "event_type": "__EVENT__",
              "client_payload": {
                  "fetchcord_repo": "__FETCHCORD_REPO__",
                  "fetchcord_ref": os.environ["FETCHCORD_REF"],
                  "apply": apply,
              },
          }).encode()
          req = urllib.request.Request(
              "https://api.github.com/repos/__APPKIT_REPO__/dispatches",
              data=body,
              headers={
                  "Authorization": f"Bearer {os.environ['APPKIT_DISPATCH_TOKEN']}",
                  "Accept": "application/vnd.github+json",
                  "Content-Type": "application/json",
              },
              method="POST",
          )
          with urllib.request.urlopen(req) as resp:
              if resp.status not in (200, 204):
                  raise SystemExit(f"dispatch failed: {resp.status}")
          print("dispatched fetchcord-deploy to __APPKIT_REPO__")
          PY
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


def resources_dir(checkout: Path) -> Path:
    path = checkout / RESOURCES_DIR
    if not path.is_dir():
        raise FileNotFoundError(f"not a FetchCord checkout (missing {RESOURCES_DIR}): {checkout}")
    return path


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
        "contract": "appkit fetchcord",
        "resources": RESOURCES_DIR.as_posix(),
        "appkit": {
            "repo": appkit_repo,
            "ref": appkit_ref,
            "event": DISPATCH_EVENT,
        },
        "secrets": {
            "dispatch": "APPKIT_DISPATCH_TOKEN",
        },
    }
    header = (
        "# Written by discord-appkit.\n"
        "# Names only. Do not store DISCORD_USER_TOKEN or any token value here.\n"
    )
    return header + yaml.safe_dump(payload, sort_keys=False)


def render_workflow(appkit_repo: str, appkit_ref: str, fetchcord_repo: str) -> str:
    text = (
        CALLER_WORKFLOW.replace("__FETCHCORD_REPO__", fetchcord_repo)
        .replace("__APPKIT_REPO__", appkit_repo)
        .replace("__APPKIT_REF__", appkit_ref)
        .replace("__EVENT__", DISPATCH_EVENT)
    )
    if "secrets.DISCORD_USER_TOKEN" in text:
        raise ValueError("FetchCord caller must not reference a Discord user token")
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
