# discord-appkit

Public tool for managing Discord applications and their assets.

FetchCord does not talk to Discord. It pulls a published catalog from this repo and merges it into `fetch_cord/resources`.

```bash
appkit fetchcord publish
appkit fetchcord sync /path/to/FetchCord
appkit fetchcord install /path/to/FetchCord
appkit fetchcord deploy /path/to/FetchCord --apply
```

The public catalog lives at `export/fetchcord/` and is served from:

`https://raw.githubusercontent.com/BlivionIaG/discord-appkit/<ref>/export/fetchcord/index.json`

Uploading images to Discord still needs `DISCORD_USER_TOKEN`, and only on a protected GitHub Environment. That token is never required to sync catalogs.

See [docs/integration-fetchcord.md](docs/integration-fetchcord.md).
