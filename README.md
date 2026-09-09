# discord-appkit

Manages multiple Discord applications and their assets. The FetchCord org calls one command to deploy and declare those assets.

Discord credentials stay in this repo. FetchCord only dispatches a job.

## Contract

```bash
appkit fetchcord sync /path/to/FetchCord
appkit fetchcord deploy /path/to/FetchCord --apply
appkit fetchcord install /path/to/FetchCord
```

`install` writes a caller workflow into the FetchCord checkout. That workflow does not contain a Discord token. It sends `fetchcord-deploy` to this repo. This repo then applies assets if asked, and opens a pull request with the updated catalogs.

## On the FetchCord org

Set `APPKIT_DISPATCH_TOKEN` (permission to send `repository_dispatch` to this repo). Do not set `DISCORD_USER_TOKEN` there.

## On this repo

- Environment `discord-portal`: `DISCORD_USER_TOKEN`
- Secret `FETCHCORD_SYNC_TOKEN`: permission to push a branch and open a pull request on `fetchcord/FetchCord`

See [docs/integration-fetchcord.md](docs/integration-fetchcord.md).
