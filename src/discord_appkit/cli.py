from __future__ import annotations

import json
import os
from pathlib import Path

import typer

from .emit import emit_fetchcord
from .loader import load_manifests
from .lockfile import DEFAULT_LOCK, load_lock, save_lock
from .models import LockEntry
from .plan import build_plan

app = typer.Typer(no_args_is_help=True, add_completion=False)


def _root() -> Path:
    return Path.cwd()


@app.command()
def validate(apps: Path = typer.Argument(Path("apps"))) -> None:
    manifests = load_manifests(apps)
    typer.echo(f"ok {len(manifests)} manifest(s)")


@app.command()
def plan(
    apps: Path = typer.Argument(Path("apps")),
    lock_path: Path = typer.Option(DEFAULT_LOCK, "--lock"),
) -> None:
    manifests = load_manifests(apps)
    lock = load_lock(lock_path)
    rendered = build_plan(manifests, lock, _root()).render()
    typer.echo(rendered)


@app.command()
def emit(
    lock_path: Path = typer.Option(DEFAULT_LOCK, "--lock"),
    format: str = typer.Option("fetchcord", "--format"),
) -> None:
    lock = load_lock(lock_path)
    if format != "fetchcord":
        raise typer.BadParameter("only --format fetchcord is implemented")
    typer.echo(json.dumps(emit_fetchcord(lock), indent=4))


@app.command()
def apply(
    apps: Path = typer.Argument(Path("apps")),
    lock_path: Path = typer.Option(DEFAULT_LOCK, "--lock"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
) -> None:
    """Apply is gated. Live Discord writes land in a follow-up commit.

    Today this only binds existingId values into the lockfile so emit works
    before the HTTP client exists.
    """
    if not dry_run and not os.environ.get("DISCORD_USER_TOKEN"):
        raise typer.Exit("DISCORD_USER_TOKEN is required for --no-dry-run")

    manifests = load_manifests(apps)
    lock = load_lock(lock_path)
    typer.echo(build_plan(manifests, lock, _root()).render())

    if dry_run:
        typer.echo("dry-run: lockfile unchanged (pass --no-dry-run to bind existingId)")
        return

    for manifest in manifests:
        name = manifest.metadata.name
        app_id = manifest.spec.existingId
        if not app_id:
            typer.echo(f"skip {name}: no existingId and create-via-API is not wired yet")
            continue
        lock.applications[name] = LockEntry(
            name=name,
            category=manifest.metadata.category,
            application_id=app_id,
            keys=list(manifest.metadata.keys),
            assets={a.name: a.file for a in manifest.spec.assets},
        )
    save_lock(lock, lock_path)
    typer.echo(f"wrote {lock_path}")


if __name__ == "__main__":
    app()
