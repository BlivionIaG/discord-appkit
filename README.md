# discord-appkit

Private toolkit to make Discord application deployment declarative and reproducible for FetchCord 3 (`testing` / fastfetch) and 2.x.

## Commands

```bash
pip install -e ".[dev]"
appkit validate apps/
appkit plan apps/
appkit apply apps/ --no-dry-run          # binds existingId; uploads if DISCORD_USER_TOKEN is set
appkit emit --format fetchcord --out fetchcord_ids.generated.json
appkit emit --format fetchcord-testing --out /tmp/fetchcord-resources
appkit import-ids catalog/fetchcord-testing
```

`apply` never runs from CI. The `plan-comment` workflow posts `validate` + `plan` on PRs that touch apps/assets. `emit-fetchcord` is workflow_dispatch only.

Auth for live apply is `DISCORD_USER_TOKEN` (Developer Portal owner account). Do not commit it.
