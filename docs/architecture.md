# Architecture

discord-appkit manages Discord applications and assets. FetchCord calls it; it does not embed Discord credentials.

```
apps/*.yaml + assets/*
        |
        v
appkit fetchcord deploy --apply     private token, same command CI runs
        |
        v
state/ids.lock.json
        |
        v
appkit fetchcord sync               declare catalogs into fetch_cord/resources
```

The FetchCord org entry point is `repository_dispatch` event `fetchcord-deploy`, installed by `appkit fetchcord install`.
