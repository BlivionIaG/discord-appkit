"""Install and run the FetchCord asset sync.

discord-appkit declares Discord applications. This module writes those
declarations into a FetchCord checkout and installs the CI that keeps
``fetch_cord/resources`` in sync. Secret values are never written.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from .adapters.fetchcord import emit_fetchcord_testing, merge_resources
from .lockfile import DEFAULT_LOCK, load_lock

RESOURCES_DIR = Path("fetch_cord/resources")
WORKFLOW_PATH = Path(".github/workflows/sync-discord-assets.yml")
CONFIG_PATH = Path(".github/discord-appkit.yml")

DEFAULT_APPKIT_REPO = "BlivionIaG/discord-appkit"
DEFAULT_FETCHCORD_REPO = "fetchcord/FetchCord"

WORKFLOW_TEMPLATE = """name: sync-discord-assets

# Installed by discord-appkit.
# Syncs declared Discord application catalogs into fetch_cord/resources.
# Does not read DISCORD_USER_TOKEN. Do not add pull_request or pull_request_target.
on:
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  sync:
    if: github.event_name == 'workflow_dispatch' && github.repository == '__FETCHCORD_REPO__'
    runs-on: ubuntu-latest
    steps:
      - name: checkout FetchCord
        uses: actions/checkout@v4

      - name: checkout discord-appkit
        env:
          APPKIT_READ_TOKEN: ${{ secrets.APPKIT_READ_TOKEN }}
        run: |
          set +x
          if [ -z "$APPKIT_READ_TOKEN" ]; then
            echo "APPKIT_READ_TOKEN is not set"
            exit 1
          fi
          git -c "http.extraheader=AUTHORIZATION: bearer ${APPKIT_READ_TOKEN}" \\
            clone --depth 1 --branch "__APPKIT_REF__" \\
            "https://github.com/__APPKIT_REPO__.git" /tmp/discord-appkit

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: declare catalogs
        working-directory: /tmp/discord-appkit
        run: |
          pip install -e .
          appkit sync-fetchcord "$GITHUB_WORKSPACE"

      - name: open pull request if catalogs changed
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          set +x
          git config user.name "discord-appkit"
          git config user.email "appkit@users.noreply.github.com"
          git add fetch_cord/resources
          if git diff --cached --quiet; then
            echo "catalogs already match declared assets"
            exit 0
          fi
          branch="appkit/sync-assets-${GITHUB_RUN_ID}"
          git checkout -b "$branch"
          git commit -m "chore: sync declared Discord application catalogs"
          git push origin "HEAD:refs/heads/${branch}"
          gh pr create --base "${GITHUB_REF_NAME}" --head "$branch" \\
            --title "chore: sync declared Discord application catalogs" \\
            --body "Declared by discord-appkit. Application IDs only. No tokens."
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
    """Merge declared application catalogs into a FetchCord resources directory."""
    lock = load_lock(lock_path)
    emitted = emit_fetchcord_testing(lock)
    if not emitted:
        raise ValueError("lockfile has no FetchCord application catalogs to sync")
    return merge_resources(resources_dir(checkout), emitted)


def render_config(appkit_repo: str, appkit_ref: str) -> str:
    payload = {
        "version": 1,
        "resources": RESOURCES_DIR.as_posix(),
        "appkit": {
            "repo": appkit_repo,
            "ref": appkit_ref,
            "lock": DEFAULT_LOCK.as_posix(),
        },
        "secrets": {
            "read_appkit": "APPKIT_READ_TOKEN",
        },
    }
    header = (
        "# Written by discord-appkit. Secret names only; never store token values here.\n"
    )
    return header + yaml.safe_dump(payload, sort_keys=False)


def render_workflow(appkit_repo: str, appkit_ref: str, fetchcord_repo: str) -> str:
    text = (
        WORKFLOW_TEMPLATE.replace("__FETCHCORD_REPO__", fetchcord_repo)
        .replace("__APPKIT_REPO__", appkit_repo)
        .replace("__APPKIT_REF__", appkit_ref)
    )
    if "DISCORD_USER_TOKEN" in text and "Does not read DISCORD_USER_TOKEN" not in text:
        raise ValueError("workflow must not reference a Discord user token")
    return text


def setup_checkout(
    checkout: Path,
    appkit_repo: str = DEFAULT_APPKIT_REPO,
    appkit_ref: str = "master",
    fetchcord_repo: str = DEFAULT_FETCHCORD_REPO,
    sync: bool = True,
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
