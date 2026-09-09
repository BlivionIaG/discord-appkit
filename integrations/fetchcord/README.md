# FetchCord adapter files

These files are the public-repo side of the integration. They do not contain tokens.

- `validate_resources.py` — catalog shape check. Safe to run in public CI.
- `workflows/validate-catalogs.yml` — copy to FetchCord `.github/workflows/`. No Discord secrets.
- `workflows/deploy-discord-apps.yml` — optional, locked-down deploy. Prefer the private `deploy-discord` workflow in this repo.

See [docs/integration-fetchcord.md](../../docs/integration-fetchcord.md).
