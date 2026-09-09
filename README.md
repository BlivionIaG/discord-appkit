# discord-appkit

Private toolkit to make Discord application deployment **declarative and reproducible**.

Born from maintaining [FetchCord](https://github.com/fetchcord/FetchCord) (`testing` → 3.0 / fastfetch). FetchCord maps distros, CPUs, GPUs, terminals, and hosts onto Discord application IDs + Rich Presence assets. That mapping (`fetchcord_ids.json`) and the Developer Portal assets have historically been hand-edited.

This repo treats those apps as infrastructure:

1. Describe each Discord application and its assets in YAML.
2. `plan` against live Developer Portal state.
3. `apply` creates/updates apps and uploads assets.
4. `emit` writes a stable ID map FetchCord (or any RPC client) can consume.

Same pattern works for bots, activities, and other Discord apps — not only Rich Presence.

## Why

- Creating an app in the portal, uploading art, copying the snowflake into JSON is not reviewable.
- Adding Parrot OS / a new APU / a new laptop chassis currently means tribal knowledge.
- CI should be able to prove "these assets exist on this application" before a FetchCord release.
- A second maintainer should be able to reproduce the portal from git.

## Layout

```
apps/                 # one YAML manifest per Discord application
assets/               # source images referenced by manifests
state/                # committed lockfile of application IDs (no secrets)
src/discord_appkit/   # CLI + API client
schemas/              # JSON Schema for manifests
.github/workflows/    # validate + dry-run plan
```

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

export DISCORD_USER_TOKEN="..."   # owner account; never commit this
appkit validate apps/
appkit plan apps/
appkit apply apps/                # writes state/ids.lock.json
appkit emit --format fetchcord > fetchcord_ids.generated.json
```

Auth is a **user token** for the Discord account that owns the applications. Bot tokens cannot create applications or manage RPC assets. Prefer a dedicated alt used only for FetchCord apps. Store the token in GitHub Actions secrets as `DISCORD_USER_TOKEN` if you enable apply-from-CI later.

## Manifest sketch

```yaml
# apps/distro-arch.yaml
apiVersion: appkit.discord/v1
kind: DiscordApplication
metadata:
  name: fetchcord-distro-arch
  category: distro
  keys: [arch]
spec:
  description: FetchCord Rich Presence — Arch Linux
  flags:
    richPresence: true
  assets:
    - name: arch
      type: rich
      file: assets/distro/arch.png
```

`metadata.keys` are the lookup strings FetchCord already uses (`arch`, `ryzen 7`, `konsole`, …). `emit` folds those into the existing map shape.

## Safety

- Default GitHub Action is **validate + plan only**. `apply` is explicit.
- Lockfile is the source of truth for IDs so re-runs are idempotent.
- Tokens stay in env / Actions secrets. Manifests and lockfile contain only public snowflakes and asset names.
- Discord rate limits asset uploads; apply is batched and retries with backoff.

## Status

Scaffold. Next slices:

- [ ] Live Discord HTTP client (`plan` / `apply`) against `/applications` and `/oauth2/applications/{id}/assets`
- [ ] Import existing FetchCord IDs from `testing` into `apps/` + `state/`
- [ ] Asset hash check so unchanged PNGs are skipped
- [ ] Optional GitHub Action that comments the plan on PRs that touch `apps/` or `assets/`
- [ ] Bot/command registration target (slash commands as code) if needed beyond RPC
