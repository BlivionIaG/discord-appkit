from pathlib import Path

from discord_appkit.loader import load_manifests


def test_category_is_a_consumer_label(tmp_path: Path):
    apps = tmp_path / "apps"
    apps.mkdir()
    (apps / "presence.yaml").write_text(
        """
apiVersion: appkit.discord/v1
kind: DiscordApplication
metadata:
  name: example-presence
  category: custom-product
  annotations:
    consumer: example
spec:
  description: Not a consumer-specific application
  flags:
    richPresence: true
""",
        encoding="utf-8",
    )
    loaded = load_manifests(apps)
    assert loaded[0].metadata.category == "custom-product"
    assert loaded[0].metadata.annotations["consumer"] == "example"
