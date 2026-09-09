# discord-appkit

Tooling that declares Discord applications and installs the CI that syncs those declarations into the FetchCord project.

You keep the manifests and the Discord user token here. FetchCord receives application catalogs through a workflow this tool writes into that repo. The public workflow never receives the Discord token.

## Commands

```bash
pip install -e ".[dev]"
appkit validate apps/
appkit plan apps/
appkit apply apps/ --no-dry-run          # private; requires DISCORD_USER_TOKEN
appkit sync-fetchcord /path/to/FetchCord
appkit setup-fetchcord /path/to/FetchCord
```

`setup-fetchcord` writes:

- `.github/workflows/sync-discord-assets.yml` — manual job that checks out this repo and declares catalogs into `fetch_cord/resources`
- `.github/discord-appkit.yml` — secret names and repo refs, never token values

On the FetchCord repository, set `APPKIT_READ_TOKEN` (read access to this private repo). Do not set `DISCORD_USER_TOKEN` there.

See [docs/integration-fetchcord.md](docs/integration-fetchcord.md).
