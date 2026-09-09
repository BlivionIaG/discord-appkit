from __future__ import annotations

import os
from typing import Any

import httpx

# Endpoints used by the future apply path. Documented here so the next slice
# does not have to rediscover Discord's poorly advertised application APIs.
#
#   GET  /applications
#   POST /applications                         {"name": ...}
#   PATCH /applications/{id}                   name / description
#   GET  /oauth2/applications/{id}/assets
#   POST /oauth2/applications/{id}/assets      name, type, image (data URI)
#   DELETE /oauth2/applications/{id}/assets/{asset_id}
#
# Auth: Authorization: <user token>  (not Bot ...)
# These routes are what the Developer Portal itself uses. They are stable
# enough for ops but not covered by Discord's public bot-token docs.


class DiscordPortal:
    def __init__(self, token: str | None = None, base: str | None = None) -> None:
        self.token = token or os.environ.get("DISCORD_USER_TOKEN", "")
        self.base = (base or os.environ.get("DISCORD_API_BASE") or "https://discord.com/api/v10").rstrip("/")
        if not self.token:
            raise RuntimeError("DISCORD_USER_TOKEN is not set")

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.base,
            headers={
                "Authorization": self.token,
                "User-Agent": "discord-appkit/0.1",
            },
            timeout=30.0,
        )

    def list_applications(self) -> list[dict[str, Any]]:
        with self._client() as client:
            r = client.get("/applications")
            r.raise_for_status()
            return r.json()
