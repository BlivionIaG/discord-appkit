# discord-appkit

Tool for declaring Discord applications and assets, and for writing CI that applies them.

The project that uses the tool owns the manifests, images, lockfile, and workflows. This repository is the tool.

```bash
appkit validate apps/
appkit plan apps/
appkit apply apps/ --no-dry-run
appkit publish
appkit ci init /path/to/project
```

On FetchCord, keep `apps/`, `assets/`, and `state/ids.lock.json` in that repo, then:

```bash
appkit ci init .
```

That writes a workflow which installs this tool and runs it against FetchCord's own files. Set `DISCORD_USER_TOKEN` on FetchCord's `discord-portal` environment if that workflow should upload assets.
