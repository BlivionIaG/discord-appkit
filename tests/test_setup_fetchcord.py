from pathlib import Path

import yaml

from discord_appkit.setup_fetchcord import render_workflow, setup_checkout, sync_checkout


def _checkout(tmp_path: Path) -> Path:
    resources = tmp_path / "fetch_cord" / "resources"
    resources.mkdir(parents=True)
    (resources / "os.json").write_text(
        '{"740476198437650473": ["(?i)arch"], "740485660703719464": ["(?i)fedora"]}\n',
        encoding="utf-8",
    )
    (resources / "gpus.json").write_text('{"amd": ["(?i)amd"]}\n', encoding="utf-8")
    return tmp_path


def test_sync_declares_managed_ids_and_keeps_the_rest(tmp_path: Path):
    checkout = _checkout(tmp_path)
    written = sync_checkout(checkout, Path("state/ids.lock.json"))
    assert "os.json" in written
    os_catalog = yaml.safe_load((checkout / "fetch_cord/resources/os.json").read_text(encoding="utf-8"))
    assert "740485660703719464" in os_catalog
    assert os_catalog["740476198437650473"]
    assert '"amd"' in (checkout / "fetch_cord/resources/gpus.json").read_text(encoding="utf-8")


def test_install_writes_a_caller_without_discord_token(tmp_path: Path):
    checkout = _checkout(tmp_path)
    written = setup_checkout(checkout, sync=False)
    workflow = (checkout / ".github/workflows/deploy-discord-assets.yml").read_text(encoding="utf-8")
    config = (checkout / ".github/discord-appkit.yml").read_text(encoding="utf-8")
    assert checkout / ".github/workflows/deploy-discord-assets.yml" in written
    assert "APPKIT_DISPATCH_TOKEN" in workflow
    assert "repository_dispatch" not in workflow or "fetchcord-deploy" in workflow
    assert "secrets.DISCORD_USER_TOKEN" not in workflow
    assert "event_type" in workflow
    assert "ghp_" not in workflow
    assert "APPKIT_DISPATCH_TOKEN" in config


def test_rendered_workflow_only_dispatches():
    text = render_workflow("BlivionIaG/discord-appkit", "master", "fetchcord/FetchCord")
    assert "secrets.APPKIT_DISPATCH_TOKEN" in text
    assert "secrets.DISCORD_USER_TOKEN" not in text
    assert "github.repository == 'fetchcord/FetchCord'" in text
    assert "/repos/BlivionIaG/discord-appkit/dispatches" in text
