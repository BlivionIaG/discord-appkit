# Architecture

discord-appkit declares Discord applications and syncs those declarations into FetchCord.

```
apps/*.yaml + assets/*
        |
        v
   appkit plan / apply     bind application, upload assets (private token)
        |
        v
state/ids.lock.json
        |
        v
   appkit sync-fetchcord   declare catalogs into fetch_cord/resources
        |
        v
FetchCord CI               installed by appkit setup-fetchcord
```

`validate`, `plan`, and `apply` do not know FetchCord file names. The FetchCord checkout layout lives in `discord_appkit.setup_fetchcord` and `discord_appkit.adapters.fetchcord`.

## Why a lockfile

Discord application snowflakes are assigned at create time. Re-running apply must not spawn a second application. `existingId` pins a known app; the lockfile records what apply last believed was live.

## Auth

Creating applications and uploading Rich Presence assets needs a Developer Portal user token. A bot token is not enough. Use a dedicated owning account.

That token stays on the private `discord-portal` environment. It is a `SecretStr` and is not included in plan output, string conversions, or Discord API error text.

The workflow installed into FetchCord uses `APPKIT_READ_TOKEN` only, so it can read this repo and write catalogs. It must not receive `DISCORD_USER_TOKEN`.
