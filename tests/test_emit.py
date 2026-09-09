from discord_appkit.emit import emit_fetchcord, emit_fetchcord_testing
from discord_appkit.models import LockEntry, Lockfile


def _lock():
    return Lockfile(applications={
        "fetchcord-distro-arch": LockEntry(name="fetchcord-distro-arch", category="distro", application_id="740476198437650473", keys=["(?i)arch"]),
        "fetchcord-cpu-ryzen7": LockEntry(name="fetchcord-cpu-ryzen7", category="cpu", application_id="740752899054895105", keys=["(?i)Ryzen 7"], vendor="amd"),
    })


def test_emit_groups_keys_by_category():
    out = emit_fetchcord(_lock())
    assert out["distro"]["(?i)arch"] == "740476198437650473"
    assert out["cpu"]["amd"]["(?i)Ryzen 7"] == "740752899054895105"


def test_emit_testing_inverts_to_files():
    files = emit_fetchcord_testing(_lock())
    assert files["os.json"]["740476198437650473"] == ["(?i)arch"]
