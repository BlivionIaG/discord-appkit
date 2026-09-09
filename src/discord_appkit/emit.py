from __future__ import annotations

from collections import defaultdict

from .models import Lockfile

FETCHCORD_MAP = {
    "GPU:": "gpu",
    "CPU:": "cpu",
    "Terminal:": "terminal",
    "Motherboard:": "motherboard",
    "Host:": "motherboard",
    "Shell:": "shell",
    "OS:": "distro",
    "DE:": "desktop",
    "WM:": "windowmanager",
    "Version:": "version",
}


def emit_fetchcord(lock: Lockfile) -> dict:
    out: dict = {"map": FETCHCORD_MAP}
    buckets: dict[str, dict] = defaultdict(dict)
    for entry in lock.applications.values():
        if entry.category in {"bot", "other"}:
            continue
        target = buckets[entry.category]
        for key in entry.keys:
            target[key] = entry.application_id
    out.update(buckets)
    return out
