# Architecture

## Desired loop

```
git (apps/*.yaml + assets/*)
        |
        v
   appkit plan     ---- dry comparison vs lockfile + (later) live portal
        |
        v
   appkit apply    ---- create/bind application, upload assets
        |
        v
state/ids.lock.json
        |
        v
   appkit emit --format fetchcord
        |
        v
fetch_cord/resources/fetchcord_ids.json   (copied into FetchCord testing)
```

## Why a lockfile

Discord application snowflakes are assigned at create time. Re-running apply
must not spawn a second Arch app. `existingId` in the manifest pins a known
app; the lockfile records what apply last believed was live.

## FetchCord 3 / testing

`fetchcord/FetchCord` branch `testing` is the 3.0 rewrite (Python 3.12+,
fastfetch). It still consumes an ID map with the same categories as 2.7.7
(`distro`, `cpu`, `gpu`, `terminal`, `motherboard`, …).

First real import job: explode current `fetchcord_ids.json` into one manifest
per application ID (many keys already share an ID, e.g. thinkpad/ideapad/lenovo).
Group by ID, not by key.

## Auth reality

Creating applications and uploading RPC assets is a Developer Portal user-token
flow. A bot token is not enough. Keep the owning account dedicated if possible.

## Out of scope for v0

- Discord Dispatch / Activities builds
- Slash-command registration (easy later: PUT /applications/{id}/commands)
- Multi-owner orgs
