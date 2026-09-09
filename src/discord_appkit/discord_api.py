from __future__ import annotations

import base64
import os
import time
from pathlib import Path
from typing import Any

import httpx


class DiscordPortal:
    def __init__(self, token: str | None = None, base: str | None = None) -> None:
        self.token = token or os.environ.get("DISCORD_USER_TOKEN", "")
        self.base = (base or os.environ.get("DISCORD_API_BASE") or "https://discord.com/api/v10").rstrip("/")
        if not self.token:
            raise RuntimeError("DISCORD_USER_TOKEN is not set")

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=self.base, headers={"Authorization": self.token, "User-Agent": "discord-appkit/0.2"}, timeout=30.0)

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        delay = 1.0
        last = None
        for _ in range(6):
            with self._client() as client:
                last = client.request(method, url, **kwargs)
            if last.status_code != 429:
                last.raise_for_status()
                return last
            time.sleep(float(last.headers.get("Retry-After", delay)))
            delay = min(delay * 2, 30)
        last.raise_for_status()
        return last

    def list_applications(self) -> list[dict[str, Any]]:
        return self._request("GET", "/applications").json()

    def create_application(self, name: str, description: str = "") -> dict[str, Any]:
        return self._request("POST", "/applications", json={"name": name, "description": description}).json()

    def list_assets(self, application_id: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/oauth2/applications/{application_id}/assets").json()

    def upload_asset(self, application_id: str, name: str, path: Path, type_: int = 1) -> dict[str, Any]:
        raw = path.read_bytes()
        mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
        payload = {"name": name, "type": type_, "image": f"data:{mime};base64,{base64.b64encode(raw).decode()}"}
        return self._request("POST", f"/oauth2/applications/{application_id}/assets", json=payload).json()

    def put_commands(self, application_id: str, commands: list[dict[str, Any]]) -> Any:
        return self._request("PUT", f"/applications/{application_id}/commands", json=commands).json()
