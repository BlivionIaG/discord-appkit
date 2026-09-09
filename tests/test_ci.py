from pathlib import Path

from discord_appkit.ci import init_ci, render_workflow


def test_ci_init_writes_a_workflow_for_the_consumer_repo(tmp_path: Path):
    written = init_ci(tmp_path)
    workflow = (tmp_path / ".github/workflows/discord-apps.yml").read_text(encoding="utf-8")
    config = (tmp_path / "discord-appkit.yml").read_text(encoding="utf-8")
    assert tmp_path / ".github/workflows/discord-apps.yml" in written
    assert "appkit validate apps/" in workflow
    assert "appkit plan apps/" in workflow
    assert "appkit apply apps/ --no-dry-run" in workflow
    assert "git+https://github.com/BlivionIaG/discord-appkit.git" in workflow
    assert "apps: apps" in config
    assert ".appkit/state" not in workflow


def test_rendered_workflow_installs_the_tool_not_its_lockfile():
    text = render_workflow("BlivionIaG/discord-appkit", "master")
    assert "pip install" in text
    assert "ids.lock.json" not in text or "state/ids.lock.json" in text
    assert ".appkit/state/ids.lock.json" not in text
