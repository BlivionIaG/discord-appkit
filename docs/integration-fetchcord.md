# Using the tool from FetchCord CI

FetchCord is a consumer. The tool is not FetchCord-specific.

From a FetchCord checkout:

```bash
appkit ci init . --format fetchcord-testing --out fetch_cord/resources
```

That writes `.github/workflows/discord-assets.yml`. The workflow checks out this tool and runs:

```bash
appkit emit --lock .appkit/state/ids.lock.json --format fetchcord-testing --out fetch_cord/resources --merge
```

`--merge` updates application IDs this lockfile manages and leaves other keys in place. No Discord token is written into the FetchCord workflow.

Uploading images to Discord is `appkit apply --no-dry-run` on a protected environment, not part of the FetchCord sync job.
