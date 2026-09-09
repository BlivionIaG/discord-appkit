# discord-appkit

Declarative Discord application deployment: manifests in git, a lockfile of assigned IDs, and a plan/apply loop.

This toolkit is consumer-agnostic. FetchCord is the first adapter, not a dependency of `validate`, `plan`, or `apply`.

## Commands

```bash
pip install -e ".[dev]"
appkit validate apps/
appkit plan apps/
appkit apply apps/                       # dry-run
appkit apply apps/ --no-dry-run          # live; requires DISCORD_USER_TOKEN
appkit emit --format lock --out state/ids.lock.json
appkit emit --format fetchcord-testing --out /tmp/fetchcord-resources --merge
appkit import-ids catalog/fetchcord-testing
```

`apply` defaults to dry-run and never runs from pull-request CI. Live apply is a manual workflow on a protected GitHub Environment. The token is read from the environment and is never printed.

## FetchCord

See [docs/integration-fetchcord.md](docs/integration-fetchcord.md). Catalog emit/import lives in `discord_appkit.adapters.fetchcord`. Public FetchCord CI must not receive `DISCORD_USER_TOKEN`.
