from pathlib import Path
from discord_appkit.import_ids import catalogs_to_lock, load_testing_catalog, write_manifests
from discord_appkit.loader import load_manifests
from discord_appkit.plan import build_plan

def test_plan_reports_missing_assets_without_failing(tmp_path: Path):
    lock = catalogs_to_lock(load_testing_catalog(Path("catalog/fetchcord-testing")))
    apps = tmp_path / "apps"
    write_manifests(lock, apps)
    rendered = build_plan(load_manifests(apps), lock, tmp_path).render()
    assert "missing" in rendered
