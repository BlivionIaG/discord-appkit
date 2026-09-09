# Architecture

This repo is public. It manages Discord applications and publishes the catalogs FetchCord syncs.

```
apps/*.yaml + assets/*
        |
        v
appkit fetchcord publish     export/fetchcord/
        |
        v
FetchCord pulls the public URL and merges fetch_cord/resources
```

Live upload to Discord uses `DISCORD_USER_TOKEN` on a protected environment. Catalog sync does not.
