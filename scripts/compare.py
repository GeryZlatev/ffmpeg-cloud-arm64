#!/usr/bin/env python3
"""Compare actual bytes from independently compiled binaries, not source versions."""
import hashlib
import json
from pathlib import Path
import sys

results = {}
for name in ("ffmpeg", "ffprobe"):
    paths = [Path(arg) / "package/bin" / name for arg in sys.argv[1:]]
    if len(paths) != 2:
        raise SystemExit("Expected two build directories")
    hashes = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
    results[name] = {"sha256": hashes, "byte_identical": paths[0].read_bytes() == paths[1].read_bytes()}
print(json.dumps(results, indent=2))
if not all(item["byte_identical"] for item in results.values()):
    raise SystemExit("Reproducibility gate failed")
