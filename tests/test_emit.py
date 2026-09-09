from discord_appkit.emit import emit_fetchcord
from discord_appkit.models import LockEntry, Lockfile


def test_emit_groups_keys_by_category():
    lock = Lockfile(
        applications={
            "fetchcord-distro-arch": LockEntry(
                name="fetchcord-distro-arch",
                category="distro",
                application_id="740476198437650473",
                keys=["arch"],
            ),
            "fetchcord-cpu-ryzen7": LockEntry(
                name="fetchcord-cpu-ryzen7",
                category="cpu",
                application_id="740752899054895105",
                keys=["ryzen 7"],
            ),
        }
    )
    out = emit_fetchcord(lock)
    assert out["distro"]["arch"] == "740476198437650473"
    assert out["cpu"]["ryzen 7"] == "740752899054895105"
    assert "map" in out
