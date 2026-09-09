from __future__ import annotations

from collections import defaultdict
from .models import Lockfile

FETCHCORD_MAP = {
    "GPU:": "gpu", "CPU:": "cpu", "Terminal:": "terminal",
    "Motherboard:": "motherboard", "Host:": "motherboard", "Shell:": "shell",
    "OS:": "distro", "DE:": "desktop", "WM:": "windowmanager", "Version:": "version",
}
TESTING_FILES = {"distro": "os.json", "cpu": "cpus.json", "terminal": "terminal.json", "motherboard": "motherboards.json"}


def emit_fetchcord(lock: Lockfile) -> dict:
    out: dict = {"map": FETCHCORD_MAP}
    buckets: dict[str, dict] = defaultdict(dict)
    cpu: dict[str, dict] = defaultdict(dict)
    for entry in lock.applications.values():
        if entry.category in {"bot", "other"}:
            continue
        if entry.category == "cpu":
            vendor = entry.vendor or "unknown"
            for key in entry.keys:
                cpu[vendor][key] = entry.application_id
            continue
        for key in entry.keys:
            buckets[entry.category][key] = entry.application_id
    if cpu:
        buckets["cpu"] = dict(cpu)
    out.update(buckets)
    return out


def emit_fetchcord_testing(lock: Lockfile) -> dict[str, dict]:
    files: dict[str, dict] = {name: {} for name in TESTING_FILES.values()}
    for entry in lock.applications.values():
        fname = TESTING_FILES.get(entry.category)
        if fname:
            files[fname][entry.application_id] = list(entry.keys)
    return files
