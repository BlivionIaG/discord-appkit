from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class AssetSpec(BaseModel):
    name: str = Field(max_length=32)
    file: str
    type: str = "rich"


class AppFlags(BaseModel):
    richPresence: bool = True
    bot: bool = False


class Metadata(BaseModel):
    """Consumer-neutral identity. Category, keys, and vendor are labels for emitters."""

    name: str
    category: str = Field(min_length=1)
    keys: list[str] = Field(default_factory=list)
    vendor: str | None = None
    annotations: dict[str, str] = Field(default_factory=dict)


class Spec(BaseModel):
    description: str
    existingId: str | None = None
    flags: AppFlags = Field(default_factory=AppFlags)
    assets: list[AssetSpec] = Field(default_factory=list)
    commands: list[dict] = Field(default_factory=list)


class DiscordApplication(BaseModel):
    apiVersion: str = "appkit.discord/v1"
    kind: str = "DiscordApplication"
    metadata: Metadata
    spec: Spec
    source: Path | None = None


class AssetLock(BaseModel):
    file: str
    sha256: str | None = None
    discord_asset_id: str | None = None


class LockEntry(BaseModel):
    name: str
    category: str
    application_id: str
    keys: list[str] = Field(default_factory=list)
    vendor: str | None = None
    annotations: dict[str, str] = Field(default_factory=dict)
    assets: dict[str, AssetLock | str] = Field(default_factory=dict)

    def asset_file(self, name: str) -> str | None:
        raw = self.assets.get(name)
        if raw is None:
            return None
        if isinstance(raw, str):
            return raw
        return raw.file

    def asset_sha(self, name: str) -> str | None:
        raw = self.assets.get(name)
        if raw is None or isinstance(raw, str):
            return None
        return raw.sha256


class Lockfile(BaseModel):
    version: int = 1
    applications: dict[str, LockEntry] = Field(default_factory=dict)
