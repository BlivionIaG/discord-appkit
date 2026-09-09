from pathlib import Path

from discord_appkit.models import LockEntry, Lockfile
from discord_appkit.publish import catalog_from_lock, publish_catalog


def test_publish_catalog_is_consumer_neutral(tmp_path: Path):
    lock = Lockfile(
        applications={
            "example": LockEntry(
                name="example",
                category="other",
                application_id="740476198437650473",
                keys=["demo"],
            )
        }
    )
    out = catalog_from_lock(lock)
    assert out["applications"][0]["applicationId"] == "740476198437650473"
    assert "map" not in out
    path = publish_catalog(tmp_path / "catalog.json")
    assert path.is_file()
