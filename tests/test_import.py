from pathlib import Path
from discord_appkit.import_ids import catalogs_to_lock, load_testing_catalog

def test_import_testing_catalog():
    lock = catalogs_to_lock(load_testing_catalog(Path("catalog/fetchcord-testing")))
    assert any(e.application_id == "740476198437650473" for e in lock.applications.values())
    assert all(e.application_id.isdigit() for e in lock.applications.values())
