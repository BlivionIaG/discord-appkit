from __future__ import annotations

import json
from pathlib import Path

import typer

from .apply import apply_manifests
from .discord_api import DiscordPortal
from .emit import render_lock
from .loader import load_manifests
from .lockfile import DEFAULT_LOCK, load_lock, save_lock
from .plan import build_plan
from .secrets import load_user_token

app = typer.Typer(no_args_is_help=True, add_completion=False)

BUILTIN_FORMATS = ("lock",)
ADAPTER_FORMATS = ("fetchcord", "fetchcord-testing")


def _fetchcord():
    from .adapters import fetchcord

    return fetchcord


@app.command()
def validate(apps: Path = typer.Argument(Path("apps"))) -> None:
    typer.echo(f"ok {len(load_manifests(apps))} manifest(s)")


@app.command()
def plan(apps: Path = typer.Argument(Path("apps")), lock_path: Path = typer.Option(DEFAULT_LOCK, "--lock")) -> None:
    typer.echo(build_plan(load_manifests(apps), load_lock(lock_path), Path.cwd()).render())


@app.command()
def emit(
    lock_path: Path = typer.Option(DEFAULT_LOCK, "--lock"),
    format: str = typer.Option("lock", "--format"),
    out: Path | None = typer.Option(None, "--out"),
    merge: bool = typer.Option(
        False,
        "--merge",
        help="Update matching IDs in an existing catalog and keep keys this lockfile does not manage.",
    ),
) -> None:
    lock = load_lock(lock_path)
    if format == "lock":
        text = render_lock(lock)
        if out:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8")
            typer.echo(f"wrote {out}")
        else:
            typer.echo(text, nl=False)
        return

    adapter = _fetchcord()
    if format == "fetchcord":
        text = json.dumps(adapter.emit_fetchcord(lock), indent=4) + "\n"
        if out:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding="utf-8")
            typer.echo(f"wrote {out}")
        else:
            typer.echo(text, nl=False)
        return
    if format == "fetchcord-testing":
        files = adapter.emit_fetchcord_testing(lock)
        dest = out or Path("-")
        if dest.as_posix() == "-":
            typer.echo(json.dumps(files, indent=2))
            return
        if merge:
            written = adapter.merge_resources(dest, files)
        else:
            dest.mkdir(parents=True, exist_ok=True)
            written = []
            for name, content in files.items():
                (dest / name).write_text(json.dumps(content, indent=4) + "\n", encoding="utf-8")
                written.append(name)
        typer.echo(f"wrote {len(written)} file(s) to {dest}")
        return
    supported = ", ".join(BUILTIN_FORMATS + ADAPTER_FORMATS)
    raise typer.BadParameter(f"supported formats: {supported}")


@app.command("import-ids")
def import_ids(
    source: Path = typer.Argument(...),
    apps: Path = typer.Option(Path("apps"), "--apps"),
    lock_path: Path = typer.Option(DEFAULT_LOCK, "--lock"),
    format: str = typer.Option("auto", "--format"),
) -> None:
    """Import a consumer ID catalog into manifests and the lockfile.

    Core has no built-in catalog format. ``auto`` detects a FetchCord testing
    directory or a 2.x ID map. This command is an adapter, not a deploy step.
    """
    adapter = _fetchcord()
    detected = format
    if format == "auto":
        detected = "fetchcord-testing" if source.is_dir() else "fetchcord"
    if detected == "fetchcord-testing":
        catalogs = adapter.load_testing_catalog(source)
    elif detected == "fetchcord":
        catalogs = adapter.load_v2_map(source)
    else:
        raise typer.BadParameter("supported formats: auto, fetchcord, fetchcord-testing")
    lock = adapter.catalogs_to_lock(catalogs)
    save_lock(lock, lock_path)
    count = adapter.write_manifests(lock, apps)
    typer.echo(f"imported {count} application(s) -> {apps} and {lock_path}")


@app.command()
def apply(
    apps: Path = typer.Argument(Path("apps")),
    lock_path: Path = typer.Option(DEFAULT_LOCK, "--lock"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run"),
) -> None:
    manifests = load_manifests(apps)
    lock = load_lock(lock_path)
    typer.echo(build_plan(manifests, lock, Path.cwd()).render())
    if dry_run:
        typer.echo("dry-run: lockfile unchanged")
        return
    token = load_user_token()
    live = bool(token)
    portal = DiscordPortal(token) if live else None
    if not live:
        typer.echo("DISCORD_USER_TOKEN is not set; refusing live apply")
        raise typer.Exit(code=2)
    lock = apply_manifests(manifests, lock, Path.cwd(), portal, live=live)
    save_lock(lock, lock_path)
    typer.echo(f"wrote {lock_path}")
