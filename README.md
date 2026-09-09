# discord-appkit

Tool for managing Discord applications and assets, and for writing the CI that syncs them.

```bash
appkit validate apps/
appkit plan apps/
appkit apply apps/ --no-dry-run
appkit publish
appkit ci init /path/to/project --format fetchcord-testing --out fetch_cord/resources
```

`ci init` writes a workflow into the project that will run it. On FetchCord that is:

```bash
appkit ci init . --format fetchcord-testing --out fetch_cord/resources
```

Commit that workflow. FetchCord CI then checks out this tool and syncs catalogs into `fetch_cord/resources`. The Discord token stays on a protected environment and is not written into that workflow.
