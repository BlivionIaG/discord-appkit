# How FetchCord calls appkit

discord-appkit owns the Discord applications and asset files. FetchCord does not talk to the Discord API. It calls appkit, and appkit writes the catalogs back.

```
FetchCord workflow_dispatch
        |
        |  repository_dispatch  (APPKIT_DISPATCH_TOKEN)
        v
discord-appkit fetchcord-deploy
        |
        |  optional apply        (DISCORD_USER_TOKEN, private environment)
        |  appkit fetchcord sync
        v
pull request on fetchcord/FetchCord
        fetch_cord/resources/*.json
```

The same code path is available locally:

```bash
appkit fetchcord sync /path/to/FetchCord
appkit fetchcord deploy /path/to/FetchCord --apply
```

## Install the caller

```bash
appkit fetchcord install /path/to/FetchCord
```

Commit `.github/workflows/deploy-discord-assets.yml` and `.github/discord-appkit.yml` on FetchCord.

## Secrets

| Secret | Where | Used for |
| --- | --- | --- |
| `APPKIT_DISPATCH_TOKEN` | FetchCord org | call this repo |
| `DISCORD_USER_TOKEN` | this repo, environment `discord-portal` | create apps and upload assets |
| `FETCHCORD_SYNC_TOKEN` | this repo | open the catalog pull request |

`APPKIT_DISPATCH_TOKEN` is a GitHub token, not a Discord token. The public workflow is `workflow_dispatch` only and runs only when `github.repository` is `fetchcord/FetchCord`.
