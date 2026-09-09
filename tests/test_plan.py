from pathlib import Path

from discord_appkit.loader import load_manifests
from discord_appkit.models import LockEntry, Lockfile
from discord_appkit.plan import build_plan


def test_plan_reports_missing_assets_without_failing(tmp_path: Path):
    apps = tmp_path / "apps"
    apps.mkdir()
    (apps / "example.yaml").write_text(
        """
apiVersion: appkit.discord/v1
kind: DiscordApplication
metadata:
  name: example-presence
  category: other
spec:
  description: example
  existingId: "740476198437650473"
  assets:
    - name: icon
      file: assets/icon.png
""",
        encoding="utf-8",
    )
    lock = Lockfile(
        applications={
            "example-presence": LockEntry(
                name="example-presence",
                category="other",
                application_id="740476198437650473",
            )
        }
    )
    rendered = build_plan(load_manifests(apps), lock, tmp_path).render()
    assert "missing" in rendered
