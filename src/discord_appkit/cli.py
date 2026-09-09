from __future__ import annotations

import json
import os
from pathlib import Path
import typer
from .apply import apply_manifests
from .discord_api import DiscordPortal
from .emit import emit_fetchcord, emit_fetchcord_testing
from .import_ids import catalogs_to_lock, load_testing_catalog, load_v2_map, write_manifests
from .loader import load_manifests
from .lockfile import DEFAULT_LOCK, load_lock, save_lock
from .plan import build_plan

app = typer.Typer(no_args_is_help=True, add_completion=False)

@app.command()
def validate(apps: Path = typer.Argument(Path("apps"))) -> None:
    typer.echo(f"ok {len(load_manifests(apps))} manifest(s)")

@app.command()
def plan(apps: Path = typer.Argument(Path("apps")), lock_path: Path = typer.Option(DEFAULT_LOCK, "--lock")) -> None:
    typer.echo(build_plan(load_manifests(apps), load_lock(lock_path), Path.cwd()).render())

@app.command()
def emit(lock_path: Path = typer.Option(DEFAULT_LOCK, "--lock"), format: str = typer.Option("fetchcord", "--format"), out: Path | None = typer.Option(None, "--out")) -> None:
    lock = load_lock(lock_path)
    if format == "fetchcord":
        text = json.dumps(emit_fetchcord(lock), indent=4) + "\n"
        if out:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8")
        else:
            typer.echo(text, nl=False)
        return
    if format == "fetchcord-testing":
        files = emit_fetchcord_testing(lock)
        dest = out or Path("-")
        if dest.as_posix() == "-":
            typer.echo(json.dumps(files, indent=2))
            return
        dest.mkdir(parents=True, exist_ok=True)
        for name, content in files.items():
            (dest / name).write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
        typer.echo(f"wrote {len(files)} file(s) to {dest}")
        return
    raise typer.BadParameter("supported formats: fetchcord, fetchcord-testing")

@app.command("import-ids")
def import_ids(source: Path = typer.Argument(...), apps: Path = typer.Option(Path("apps"), "--apps"), lock_path: Path = typer.Option(DEFAULT_LOCK, "--lock")) -> None:
    catalogs = load_testing_catalog(source) if source.is_dir() else load_v2_map(source)
    lock = catalogs_to_lock(catalogs)
    save_lock(lock, lock_path)
    n = write_manifests(lock, apps)
    typer.echo(f"imported {n} application(s) -> {apps} and {lock_path}")

@app.command()
def apply(apps: Path = typer.Argument(Path("apps")), lock_path: Path = typer.Option(DEFAULT_LOCK, "--lock"), dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run")) -> None:
    manifests = load_manifests(apps)
    lock = load_lock(lock_path)
    typer.echo(build_plan(manifests, lock, Path.cwd()).render())
    if dry_run:
        typer.echo("dry-run: lockfile unchanged")
        return
    live = bool(os.environ.get("DISCORD_USER_TOKEN"))
    portal = DiscordPortal() if live else None
    lock = apply_manifests(manifests, lock, Path.cwd(), portal, live=live)
    save_lock(lock, lock_path)
    typer.echo(f"wrote {lock_path}")
