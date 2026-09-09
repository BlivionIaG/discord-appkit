# FetchCord integration

discord-appkit declares Discord applications. Its job for FetchCord is to sync those declarations into `fetch_cord/resources` and to install the CI that does that sync on the FetchCord project.

## What gets declared

FetchCord testing loads `fetch_cord/resources/<name>.json` as `id -> [patterns]`.

`appkit sync-fetchcord` writes the application-id catalogs from this repo's lockfile:

- `distro` -> `os.json`
- `cpu` -> `cpus.json`
- `terminal` -> `terminal.json`
- `motherboard` -> `motherboards.json`
- `shell` -> `shell.json`

Merge updates only IDs this lockfile manages. Other application IDs and asset-name catalogs (`gpus.json`, `desktop.json`, `windowmanager.json`, `system_types.json`) stay as they are.

## Install the CI

From a FetchCord checkout:

```bash
appkit setup-fetchcord .
```

That writes the workflow and a config file. Commit those files on FetchCord. Then add one GitHub secret on that repository:

- `APPKIT_READ_TOKEN` — a GitHub token that can read this private repo

Do not add `DISCORD_USER_TOKEN` to FetchCord. Creating and uploading Discord assets stays on the private `deploy-discord` workflow in this repo, bound to the `discord-portal` environment.

## Loop

1. Change a manifest or asset in this repo.
2. Pull-request CI here runs `validate` and `plan`. No Discord token.
3. A maintainer runs **Deploy Discord applications** here when Discord itself must change.
4. On FetchCord, run **sync-discord-assets**. It checks out this repo, declares the catalogs, and opens a pull request if `fetch_cord/resources` changed.

The installed workflow is `workflow_dispatch` only and refuses to run unless `github.repository` is `fetchcord/FetchCord`.
