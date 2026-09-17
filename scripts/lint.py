#!/usr/bin/env python3
"""Validate the lock and build contract without any downloads or binary execution."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
sources = json.loads((ROOT / "build/sources.lock.json").read_text())
packages = json.loads((ROOT / "build/apk-lock.json").read_text())
assert re.fullmatch(r"alpine:3\.22\.1@sha256:[a-f0-9]{64}", sources["container"])
assert sources["container"] in (ROOT / "build/Dockerfile").read_text()
assert re.fullmatch(r"[a-f0-9]{40}", sources["x264_commit"])
for item in sources["sources"] + packages:
    assert item["url"].startswith("https://")
    assert re.fullmatch(r"[a-f0-9]{64}", item["sha256"])
    assert "latest" not in item["url"]
for item in packages:
    assert item["name"] + "-" + item["version"] + ".apk" == item["url"].rsplit("/", 1)[1]
    assert re.fullmatch(r"[a-f0-9]{40}", item["aports_commit"])
key = ROOT / "build/ffmpeg-release-key.asc"
assert hashlib.sha256(key.read_bytes()).hexdigest() == sources["ffmpeg_signing_key_sha256"]
flags = json.loads((ROOT / "build/ffmpeg-configure.json").read_text())
for flag in ["--enable-gpl", "--enable-libx264", "--enable-libzimg", "--disable-autodetect", "--enable-static", "--disable-shared"]:
    assert flag in flags
assert not any("nonfree" in flag or "libx265" in flag for flag in flags)
workflow = ROOT / ".github/workflows/gate1.yml"
if workflow.exists():
    for action in re.findall(r"uses:\s*(\S+)", workflow.read_text()):
        assert re.fullmatch(r"[\w-]+/[\w-]+@[a-f0-9]{40}", action), action
print("Lock/configuration validation PASS")
