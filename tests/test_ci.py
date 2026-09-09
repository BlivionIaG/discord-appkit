from pathlib import Path

from discord_appkit.ci import init_ci, render_workflow


def test_ci_init_writes_a_sync_workflow_without_a_token(tmp_path: Path):
    written = init_ci(tmp_path, "fetchcord-testing", "fetch_cord/resources")
    workflow = (tmp_path / ".github/workflows/discord-assets.yml").read_text(encoding="utf-8")
    config = (tmp_path / "discord-appkit.yml").read_text(encoding="utf-8")
    assert tmp_path / ".github/workflows/discord-assets.yml" in written
    assert "appkit emit" in workflow
    assert "--format fetchcord-testing" in workflow
    assert "--out fetch_cord/resources" in workflow
    assert "DISCORD_USER_TOKEN" not in workflow
    assert "format: fetchcord-testing" in config


def test_rendered_workflow_uses_the_tool_lockfile():
    text = render_workflow("lock", "export", "BlivionIaG/discord-appkit", "master")
    assert "--lock .appkit/state/ids.lock.json" in text
    assert "DISCORD_USER_TOKEN" not in text
