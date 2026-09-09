from __future__ import annotations

from pathlib import Path

import typer

from .apply import apply_manifests
from .ci import DEFAULT_APPKIT_REPO, init_ci
from .discord_api import DiscordPortal
from .emit import render_lock
from .loader import load_manifests
from .lockfile import DEFAULT_LOCK, load_lock, save_lock
from .plan import build_plan
from .publish import EXPORT_PATH, publish_catalog
from .secrets import load_user_token

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.command()
def validate(apps: Path = typer.Argument(Path("apps"))) -> None:
    typer.echo(f"ok {len(load_manifests(apps))} manifest(s)")


@app.command()
def plan(apps: Path = typer.Argument(Path("apps")), lock_path: Path = typer.Option(DEFAULT_LOCK, "--lock")) -> None:
    typer.echo(build_plan(load_manifests(apps), load_lock(lock_path), Path.cwd()).render())


@app.command()
def emit(
    lock_path: Path = typer.Option(DEFAULT_LOCK, "--lock"),
    out: Path | None = typer.Option(None, "--out"),
) -> None:
    text = render_lock(load_lock(lock_path))
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        typer.echo(f"wrote {out}")
    else:
        typer.echo(text, nl=False)


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
    if not token:
        typer.echo("DISCORD_USER_TOKEN is not set; refusing live apply")
        raise typer.Exit(code=2)
    lock = apply_manifests(manifests, lock, Path.cwd(), DiscordPortal(token), live=True)
    save_lock(lock, lock_path)
    typer.echo(f"wrote {lock_path}")


@app.command()
def publish(
    out: Path = typer.Option(EXPORT_PATH, "--out"),
    lock_path: Path = typer.Option(DEFAULT_LOCK, "--lock"),
) -> None:
    """Write a consumer-neutral catalog of bound application IDs."""
    path = publish_catalog(out, lock_path)
    typer.echo(f"wrote {path}")


ci_app = typer.Typer(no_args_is_help=True, help="Write CI that runs this tool in another repository.")
app.add_typer(ci_app, name="ci")


@ci_app.command("init")
def ci_init(
    checkout: Path = typer.Argument(..., help="Repository that owns the Discord apps and assets"),
    appkit_repo: str = typer.Option(DEFAULT_APPKIT_REPO, "--appkit-repo"),
    appkit_ref: str = typer.Option("master", "--appkit-ref"),
) -> None:
    """Write a workflow into a project that owns apps/, assets/, and the lockfile."""
    written = init_ci(checkout, appkit_repo, appkit_ref)
    for path in written:
        typer.echo(f"wrote {path}")
    typer.echo("Commit the workflow. Put DISCORD_USER_TOKEN on that repo's discord-portal environment.")
