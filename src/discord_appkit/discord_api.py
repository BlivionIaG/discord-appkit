from __future__ import annotations

import base64
import os
import time
from pathlib import Path
from typing import Any

import httpx

from .secrets import SecretStr, load_user_token, redact


class DiscordApiError(RuntimeError):
    def __init__(self, method: str, path: str, status: int, detail: str = "") -> None:
        self.method = method
        self.path = path
        self.status = status
        message = f"Discord API {method} {path} failed ({status})"
        if detail:
            message = f"{message}: {detail}"
        super().__init__(message)


class DiscordPortal:
    def __init__(self, token: str | SecretStr | None = None, base: str | None = None) -> None:
        if isinstance(token, SecretStr):
            self.token = token
        else:
            self.token = load_user_token(token)
        self.base = (base or os.environ.get("DISCORD_API_BASE") or "https://discord.com/api/v10").rstrip("/")
        if not self.token:
            raise RuntimeError("DISCORD_USER_TOKEN is not set")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": self.token.reveal(),
            "User-Agent": "discord-appkit/0.3",
        }

    def _client(self) -> httpx.Client:
        return httpx.Client(base_url=self.base, headers=self._headers(), timeout=30.0)

    def _safe_detail(self, response: httpx.Response) -> str:
        try:
            body = response.text[:300]
        except httpx.HTTPError:
            body = ""
        return redact(body, self.token)

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        delay = 1.0
        last: httpx.Response | None = None
        for _ in range(6):
            try:
                with self._client() as client:
                    last = client.request(method, url, **kwargs)
            except httpx.HTTPError:
                raise RuntimeError(redact(f"Discord API {method} {url} transport error", self.token)) from None
            if last.status_code != 429:
                if last.is_error:
                    raise DiscordApiError(method, url, last.status_code, self._safe_detail(last))
                return last
            time.sleep(float(last.headers.get("Retry-After", delay)))
            delay = min(delay * 2, 30)
        if last is None:
            raise RuntimeError(f"Discord API {method} {url} failed")
        raise DiscordApiError(method, url, last.status_code, self._safe_detail(last))

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
