from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class AssetSpec(BaseModel):
    name: str = Field(max_length=32)
    file: str
    type: Literal["rich", "cover"] = "rich"


class AppFlags(BaseModel):
    richPresence: bool = True
    bot: bool = False


class Metadata(BaseModel):
    name: str
    category: Literal[
        "distro",
        "cpu",
        "gpu",
        "terminal",
        "motherboard",
        "shell",
        "desktop",
        "windowmanager",
        "version",
        "bot",
        "other",
    ]
    keys: list[str] = Field(default_factory=list)
    vendor: str | None = None


class Spec(BaseModel):
    description: str
    existingId: str | None = None
    flags: AppFlags = Field(default_factory=AppFlags)
    assets: list[AssetSpec] = Field(default_factory=list)


class DiscordApplication(BaseModel):
    apiVersion: Literal["appkit.discord/v1"]
    kind: Literal["DiscordApplication"]
    metadata: Metadata
    spec: Spec
    source: Path | None = None


class LockEntry(BaseModel):
    name: str
    category: str
    application_id: str
    keys: list[str] = Field(default_factory=list)
    assets: dict[str, str] = Field(default_factory=dict)


class Lockfile(BaseModel):
    version: int = 1
    applications: dict[str, LockEntry] = Field(default_factory=dict)
