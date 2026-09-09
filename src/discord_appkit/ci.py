"""Write a CI workflow that runs this tool against the consumer repository.

The consumer repo owns apps, assets, and the lockfile. This tool is installed
and invoked there. No consumer-specific layout is assumed.
"""

from __future__ import annotations

from pathlib import Path

import yaml

DEFAULT_APPKIT_REPO = "BlivionIaG/discord-appkit"
WORKFLOW_PATH = Path(".github/workflows/discord-apps.yml")
CONFIG_PATH = Path("discord-appkit.yml")

WORKFLOW = """name: discord-apps

# Written by discord-appkit. Runs against this repository's apps/ and lockfile.
on:
  pull_request:
    paths: ["apps/**", "assets/**", "state/**"]
  workflow_dispatch:
    inputs:
      apply:
        description: Upload assets to Discord
        type: boolean
        default: false

jobs:
  plan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: install discord-appkit
        run: pip install "git+https://github.com/__APPKIT_REPO__.git@__APPKIT_REF__"
      - name: validate and plan
        run: |
          appkit validate apps/
          appkit plan apps/

  apply:
    if: github.event_name == 'workflow_dispatch' && inputs.apply
    runs-on: ubuntu-latest
    environment: discord-portal
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: install discord-appkit
        run: pip install "git+https://github.com/__APPKIT_REPO__.git@__APPKIT_REF__"
      - name: apply
        env:
          DISCORD_USER_TOKEN: ${{ secrets.DISCORD_USER_TOKEN }}
        run: |
          set +x
          if [ -z "$DISCORD_USER_TOKEN" ]; then
            echo "DISCORD_USER_TOKEN is not set on the discord-portal environment"
            exit 1
          fi
          appkit apply apps/ --no-dry-run
      - name: commit lockfile
        run: |
          git config user.name "discord-appkit"
          git config user.email "appkit@users.noreply.github.com"
          git add state/ids.lock.json
          if git diff --cached --quiet; then
            echo "lockfile unchanged"
          else
            git commit -m "chore: update Discord application lockfile"
            git push origin HEAD
          fi
"""


def render_config(appkit_repo: str, appkit_ref: str) -> str:
    payload = {
        "version": 1,
        "apps": "apps",
        "lock": "state/ids.lock.json",
        "appkit": {"repo": appkit_repo, "ref": appkit_ref},
    }
    return "# Written by discord-appkit. Apps, assets, and lockfile live in this repo.\n" + yaml.safe_dump(
        payload, sort_keys=False
    )


def render_workflow(appkit_repo: str, appkit_ref: str) -> str:
    return WORKFLOW.replace("__APPKIT_REPO__", appkit_repo).replace("__APPKIT_REF__", appkit_ref)


def init_ci(
    checkout: Path,
    appkit_repo: str = DEFAULT_APPKIT_REPO,
    appkit_ref: str = "master",
) -> list[Path]:
    if not checkout.is_dir():
        raise FileNotFoundError(f"not a directory: {checkout}")
    written: list[Path] = []

    config = checkout / CONFIG_PATH
    config.write_text(render_config(appkit_repo, appkit_ref), encoding="utf-8")
    written.append(config)

    workflow = checkout / WORKFLOW_PATH
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(render_workflow(appkit_repo, appkit_ref), encoding="utf-8")
    written.append(workflow)
    return written
