# How FetchCord syncs assets

This repo is the public source for Discord application catalogs. FetchCord pulls that source and merges it. No token is required for the pull.

```
apps/*.yaml + assets/*
        |
        v
appkit fetchcord publish
        |
        v
export/fetchcord/          public URL, raw.githubusercontent.com
        |
        v
FetchCord CI               curl index.json, merge into fetch_cord/resources
```

Install the pull job into a FetchCord checkout:

```bash
appkit fetchcord install /path/to/FetchCord
```

That writes a workflow with no secrets. It downloads `export/fetchcord` and merges managed application IDs. Asset-name catalogs such as `gpus.json` are not in the export, so they stay as FetchCord owns them.

Uploading the actual images to Discord is separate, and stays on a protected environment in this repo:

```bash
appkit fetchcord deploy /path/to/FetchCord --apply
```

`DISCORD_USER_TOKEN` is an environment secret. It is not committed, and FetchCord never receives it.
