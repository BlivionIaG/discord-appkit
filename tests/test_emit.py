from discord_appkit.emit import emit_lock
from discord_appkit.models import LockEntry, Lockfile


def _lock():
    return Lockfile(applications={
        "presence-arch": LockEntry(
            name="presence-arch",
            category="distro",
            application_id="740476198437650473",
            keys=["(?i)arch"],
        ),
    })


def test_emit_lock_is_consumer_neutral():
    out = emit_lock(_lock())
    assert out["applications"]["presence-arch"]["application_id"] == "740476198437650473"
    assert "map" not in out
