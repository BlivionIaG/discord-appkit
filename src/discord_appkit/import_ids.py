from __future__ import annotations

# Compatibility shim. FetchCord-specific import lives in the adapter.
from .adapters.fetchcord import (
    catalogs_to_lock,
    load_testing_catalog,
    load_v2_map,
    write_manifests,
)

__all__ = [
    "catalogs_to_lock",
    "load_testing_catalog",
    "load_v2_map",
    "write_manifests",
]
