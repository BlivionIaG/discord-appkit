import json
from pathlib import Path

from discord_appkit.adapters.fetchcord import (
    catalogs_to_lock,
    load_testing_catalog,
    merge_resources,
)


def test_import_testing_catalog():
    lock = catalogs_to_lock(load_testing_catalog(Path("catalog/fetchcord-testing")))
    assert any(entry.application_id == "740476198437650473" for entry in lock.applications.values())
    assert all(entry.application_id.isdigit() for entry in lock.applications.values())
    assert all(entry.annotations.get("consumer") == "fetchcord" for entry in lock.applications.values())


def test_merge_preserves_asset_name_keys(tmp_path: Path):
    shell = tmp_path / "shell.json"
    shell.write_text('{"bash": ["(?i)bash"], "742887089179197462": ["unknown"]}\n', encoding="utf-8")
    written = merge_resources(
        tmp_path,
        {"shell.json": {"999999999999999999": ["other"]}},
    )
    assert written == ["shell.json"]
    merged = json.loads(shell.read_text(encoding="utf-8"))
    assert merged["bash"] == ["(?i)bash"]
    assert merged["742887089179197462"] == ["unknown"]
    assert merged["999999999999999999"] == ["other"]


def test_merge_does_not_drop_unmanaged_application_ids(tmp_path: Path):
    os_catalog = tmp_path / "os.json"
    os_catalog.write_text(
        '{"740476198437650473": ["(?i)arch"], "740485660703719464": ["(?i)fedora"]}\n',
        encoding="utf-8",
    )
    merge_resources(tmp_path, {"os.json": {"740476198437650473": ["(?i)arch linux"]}})
    merged = json.loads(os_catalog.read_text(encoding="utf-8"))
    assert merged["740485660703719464"] == ["(?i)fedora"]
    assert merged["740476198437650473"] == ["(?i)arch linux"]
