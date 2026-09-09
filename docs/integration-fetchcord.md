# FetchCord integration

This private repo currently holds the FetchCord application manifests. That is deployment data, not a core dependency. Another consumer would add its own manifests and adapter.

## What each repo owns

| Concern | Where it lives | Public? |
| --- | --- | --- |
| Discord user token | GitHub Environment `discord-portal` on this private repo | never |
| Manifests, assets, lockfile | this repo (`apps/`, `assets/`, `state/`) | private |
| Live create/upload | `deploy-discord` workflow here | private, manual |
| Application-id catalogs | emitted, then PR'd into FetchCord | IDs are already public |
| Asset-name catalogs (`gpus.json`, `desktop.json`, `windowmanager.json`, `system_types.json`) | FetchCord `fetch_cord/resources/` | public, not rewritten by emit |
| FetchCord runtime lookup | `fetch_cord.fetch.get_component_id` | public |

Application IDs in FetchCord are public by design: the client must know them to set Rich Presence. The user token that can create or edit those applications must not be.

## Catalog contract

FetchCord testing loads `fetch_cord/resources/<name>.json` as `application_or_asset_id -> [regex patterns]`.

Application-id catalogs, emitted from the lockfile:

- `distro` -> `os.json`
- `cpu` -> `cpus.json`
- `terminal` -> `terminal.json`
- `motherboard` -> `motherboards.json`
- `shell` -> `shell.json` (merge only; non-snowflake keys are asset names and are kept)

Asset-name catalogs are FetchCord content. Emit does not replace them.

2.x `fetchcord_ids.json` is `appkit emit --format fetchcord`.

## Recommended loop

1. Change a manifest or asset in this private repo.
2. Pull request CI runs `validate` and `plan`. No secrets.
3. A maintainer runs **Deploy Discord applications** (`workflow_dispatch`, environment `discord-portal`). That is the only job that can see `DISCORD_USER_TOKEN`.
4. After a successful apply, run **Sync FetchCord catalogs**. It emits testing resources and opens a pull request on `fetchcord/FetchCord` with `FETCHCORD_SYNC_TOKEN`. That token is a GitHub token with contents and pull-request access, not a Discord token.

A lockfile that only tracks some applications must not be treated as the full catalog. Sync uses `--merge`, which updates managed IDs and leaves every other key in place.

Public FetchCord CI should only validate the committed catalogs and run the existing test suite. It must not check out this private repo with a Discord token, and it must not define `DISCORD_USER_TOKEN`.

## GitHub setup (this repo)

Create an environment named `discord-portal`:

- Required reviewers before the job starts
- Deployment branch rule: only the branch you actually deploy from
- Environment secret: `DISCORD_USER_TOKEN` (user token of the dedicated portal account)
- Do not also store that secret as a repository secret used by other workflows

Optional, for catalog sync:

- Repository or environment secret `FETCHCORD_SYNC_TOKEN`
- Fine-grained PAT or GitHub App token that can open PRs on `fetchcord/FetchCord`
- No Discord scopes, no access to this repo's environment secrets

## Why not deploy from public FetchCord CI

A workflow in a public repository can be forked, logged, or extended. GitHub hides secrets from `pull_request` events on forks, but a public workflow file still teaches the deploy path, and a compromised maintainer workflow or `pull_request_target` mistake would expose the portal account.

Keep the token on the private repo. The public repo receives catalogs through a pull request it can review.

## If a public deploy job is unavoidable

`integrations/fetchcord/workflows/deploy-discord-apps.yml` is a locked-down template, not the default. It is `workflow_dispatch` only, bound to a protected environment, and it refuses to run on pull requests. Do not add `pull_request` or `pull_request_target` to it. Prefer the private deploy workflow instead.
