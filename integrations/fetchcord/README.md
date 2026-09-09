# FetchCord adapter files

Prefer `appkit setup-fetchcord <checkout>` to install the sync CI. That command is the source of the workflow written into FetchCord.

These copies are the same public-safe pieces:

- `validate_resources.py` — catalog shape check, no credentials
- `workflows/validate-catalogs.yml` — optional extra check for FetchCord CI
- `workflows/deploy-discord-apps.yml` — not used by setup; Discord apply stays in the private repo
