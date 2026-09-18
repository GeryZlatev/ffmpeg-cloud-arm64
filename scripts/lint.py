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
baseline = ROOT / 'build/baseline-v1.0.0'
original_sources = json.loads((baseline / 'sources.lock.json').read_text())
for key, value in original_sources.items():
    if key == 'sources':
        assert all(item in sources['sources'] for item in value), 'Changed v1.0.0 source pin'
    else:
        assert sources[key] == value, 'Changed v1.0.0 environment pin: ' + key
assert all(item in packages for item in json.loads((baseline / 'apk-lock.json').read_text())), 'Changed v1.0.0 package pin'
for flag in json.loads((baseline / 'ffmpeg-configure.json').read_text()):
    if flag.startswith(('--enable-encoder=', '--enable-decoder=', '--enable-muxer=', '--enable-demuxer=')):
        key, values = flag.split('=', 1)
        current = next(f.split('=', 1)[1] for f in flags if f.startswith(key + '='))
        assert set(values.split(',')) <= set(current.split(',')), 'Removed baseline capability: ' + flag
    else:
        assert flag in flags, 'Removed baseline configuration: ' + flag
assert '--enable-libdav1d' in flags
assert sources['dav1d_version'] == '1.5.4'
assert sources['dav1d_commit'] == '54706fc6bc0cdecab7e9593974a4039cc038fca7'
dav = next(s for s in sources['sources'] if s['name'] == 'dav1d')
assert dav['sha256'] == '9edb11a2108b375cc58370354e705feebc93430bb780130363815c1e1ac0c250'
for file, digest in {
    'dav1d-BSD-2-Clause.txt': 'dd92c3c2247c5651606fc23a5e2d6a1ebc5ace9a3e49cbde0e12f05ad1cb1ee5',
    'dav1d-AV1-PATENTS.txt': '335eca574598bf4ca181b12f708d6669e5a5e78c8e1513e5b35fa1f03901484b',
}.items():
    assert hashlib.sha256((ROOT / 'licenses' / file).read_bytes()).hexdigest() == digest
fixture_manifest = json.loads((ROOT / 'fixtures/manifest.json').read_text())
for file, expected in fixture_manifest['files'].items():
    data = (ROOT / 'fixtures' / file).read_bytes()
    assert len(data) == expected['size_bytes']
    assert hashlib.sha256(data).hexdigest() == expected['sha256']
workflow = ROOT / ".github/workflows/gate1.yml"
if workflow.exists():
    for action in re.findall(r"uses:\s*(\S+)", workflow.read_text()):
        assert re.fullmatch(r"[\w-]+/[\w-]+@[a-f0-9]{40}", action), action
print("Lock/configuration validation PASS")
