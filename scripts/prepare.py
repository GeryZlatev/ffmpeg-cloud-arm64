#!/usr/bin/env python3
"""Fetch locked inputs only; never execute downloads. Requires host Python 3."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "cache"


def fetch(item):
    target = CACHE / item["file"]
    if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != item["sha256"]:
        print("Fetching", item["url"], flush=True)
        with urllib.request.urlopen(item["url"], timeout=120) as response:
            content = response.read()
        if hashlib.sha256(content).hexdigest() != item["sha256"]:
            raise ValueError("SHA-256 mismatch: " + item["url"])
        target.write_bytes(content)
    return item["sha256"] + "  " + target.name


def main():
    CACHE.mkdir(exist_ok=True)
    sources = json.loads((ROOT / "build/sources.lock.json").read_text())["sources"]
    packages = json.loads((ROOT / "build/apk-lock.json").read_text())
    items = sources + [dict(p, file=p["url"].rsplit("/", 1)[1]) for p in packages]
    expected = {p["file"] for p in items} | {"SHA256SUMS"}
    if set(p.name for p in CACHE.iterdir()) - expected:
        raise ValueError("Unexpected cache files; use a fresh checkout or inspect cache manually")
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        sums = list(pool.map(fetch, items))
    (CACHE / "SHA256SUMS").write_text("\n".join(sorted(sums)) + "\n")


if __name__ == "__main__":
    main()
