#!/usr/bin/env bash
# Shared caller used by fetchcord-deploy.yml. Does not print secrets.
set -euo pipefail
set +x

if [ -z "${FETCHCORD_SYNC_TOKEN:-}" ]; then
  echo "FETCHCORD_SYNC_TOKEN is not set"
  exit 1
fi

ref="${FETCHCORD_REF:-testing}"
pip install -e .

git -c "http.extraheader=AUTHORIZATION: bearer ${FETCHCORD_SYNC_TOKEN}" \
  clone --depth 1 --branch "$ref" \
  https://github.com/fetchcord/FetchCord.git /tmp/FetchCord

if [ "${APPLY:-false}" = "true" ]; then
  if [ -z "${DISCORD_USER_TOKEN:-}" ]; then
    echo "DISCORD_USER_TOKEN is not set on the discord-portal environment"
    exit 1
  fi
  appkit fetchcord deploy /tmp/FetchCord --apply
else
  appkit fetchcord sync /tmp/FetchCord
fi

branch="appkit/fetchcord-${GITHUB_RUN_ID}"
git -C /tmp/FetchCord config user.name "discord-appkit"
git -C /tmp/FetchCord config user.email "appkit@users.noreply.github.com"
git -C /tmp/FetchCord checkout -b "$branch"
git -C /tmp/FetchCord add fetch_cord/resources
if git -C /tmp/FetchCord diff --cached --quiet; then
  echo "catalogs already match declared assets"
  exit 0
fi
git -C /tmp/FetchCord commit -m "chore: sync declared Discord application catalogs"
git -c "http.extraheader=AUTHORIZATION: bearer ${FETCHCORD_SYNC_TOKEN}" \
  -C /tmp/FetchCord push https://github.com/fetchcord/FetchCord.git "HEAD:refs/heads/${branch}"

FETCHCORD_REF="$ref" BRANCH="$branch" python - <<'PY'
import json, os, urllib.request
body = json.dumps({
    "title": "chore: sync declared Discord application catalogs",
    "head": os.environ["BRANCH"],
    "base": os.environ["FETCHCORD_REF"],
    "body": "Called from discord-appkit. Application catalogs only. No tokens.",
}).encode()
req = urllib.request.Request(
    "https://api.github.com/repos/fetchcord/FetchCord/pulls",
    data=body,
    headers={
        "Authorization": f"Bearer {os.environ['FETCHCORD_SYNC_TOKEN']}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    },
    method="POST",
)
with urllib.request.urlopen(req) as resp:
    payload = json.loads(resp.read().decode())
url = payload.get("html_url")
if not url:
    raise SystemExit("pull request was not created")
print(url)
PY
