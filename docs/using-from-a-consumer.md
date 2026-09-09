# Using this tool from FetchCord

Do not keep FetchCord catalogs or assets in discord-appkit. Put them in the FetchCord repository:

- `apps/*.yaml`
- `assets/`
- `state/ids.lock.json`
- `.github/workflows/discord-apps.yml` from `appkit ci init .`

FetchCord CI installs this tool and runs it against those files. Mapping the published catalog into `fetch_cord/resources` is FetchCord's own step.
