# Architecture

discord-appkit is the tool. The consumer repository owns the jobs, assets, and declarations.

```
consumer repo
  apps/*.yaml
  assets/*
  state/ids.lock.json
        |
        v
  CI installs discord-appkit
        |
        v
  appkit plan / apply / publish
```

`appkit ci init` writes that CI into the consumer repo. FetchCord is one consumer; its resource catalogs and images do not live here.
