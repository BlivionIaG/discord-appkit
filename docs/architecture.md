# Architecture

discord-appkit deploys Discord applications. It does not know what a consumer does with the resulting application IDs.

```
apps/*.yaml + assets/*
        |
        v
   appkit plan          dry comparison vs lockfile
        |
        v
   appkit apply         create/bind application, upload assets
        |
        v
state/ids.lock.json     source of truth for assigned snowflakes
        |
        v
   appkit emit          consumer adapter (optional)
```

## Core vs adapter

Core commands (`validate`, `plan`, `apply`, `emit --format lock`) only understand:

- a manifest (`apiVersion: appkit.discord/v1`)
- application name, description, flags, assets
- an optional pinned `existingId`
- labels (`category`, `keys`, `vendor`, `annotations`) that apply stores and emitters may read

FetchCord catalog shapes live in `discord_appkit.adapters.fetchcord`. Adding another consumer means another adapter, not a change to apply.

## Why a lockfile

Discord application snowflakes are assigned at create time. Re-running apply must not spawn a second application. `existingId` pins a known app; the lockfile records what apply last believed was live.

## Auth

Creating applications and uploading Rich Presence assets is a Developer Portal user-token flow. A bot token is not enough. Use a dedicated owning account.

The token is a `SecretStr`. It is not included in plan output, string conversions, or Discord API error text. Do not commit it, do not put it in a public repository, and do not make it available to pull-request workflows.
