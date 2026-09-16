#!/usr/bin/env python3
"""Fail closed on ELF, capability, metadata, encode/decode and HDR smoke checks."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

BIN, AUDIT = map(Path, sys.argv[1:])
FF = str(BIN / "ffmpeg")
FP = str(BIN / "ffprobe")
FIX = AUDIT / "fixtures"
FIX.mkdir()
results = {}


def run(args):
    result = subprocess.run(list(map(str, args)), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode:
        raise RuntimeError(f"Command failed: {args}\n{result.stdout}\n{result.stderr}")
    return result.stdout + result.stderr


def ff(*args):
    return run([FF, "-hide_banner", "-nostdin", "-y", "-v", "error", *args])


def probe(path):
    return json.loads(run([FP, "-v", "error", "-show_streams", "-show_format", "-of", "json", path]))


def require(condition, label):
    if not condition:
        raise AssertionError(label)
    results[label] = "PASS"


for name in ("ffmpeg", "ffprobe"):
    path = BIN / name
    header = run(["readelf", "-h", path])
    require("AArch64" in header, name + " ELF AArch64")
    require("INTERP" not in run(["readelf", "-l", path]), name + " no ELF interpreter")
    require("NEEDED" not in run(["readelf", "-d", path]), name + " no shared library dependencies")
    version = run([path, "-version"])
    (AUDIT / (name + "-version.txt")).write_text(version)
    require(bool(re.search(r"^" + name + r" version 7\.1\.5(?:\s|$)", version)), name + " version 7.1.5")
conf = run([FF, "-buildconf"])
(AUDIT / "buildconf.txt").write_text(conf)
for flag in ("--enable-gpl", "--enable-libx264", "--enable-libzimg"):
    require(flag in conf.split(), flag)
for kind, required in {"filters": ["zscale", "tonemap", "colorspace", "scale", "format", "fps", "transpose", "setsar", "pad", "crop", "aresample"], "encoders": ["libx264", "aac"], "decoders": ["h264", "hevc", "aac"], "demuxers": ["mov"], "muxers": ["mov", "mp4"]}.items():
    listing = run([FF, "-" + kind])
    (AUDIT / (kind + ".txt")).write_text(listing)
    names = {name for line in listing.splitlines() if len(line.split()) >= 2 for name in line.split()[1].split(",")}
    for name in required:
        require(name in names, kind + ":" + name)

sdr = FIX / "sdr-h264.mov"
ff("-f", "lavfi", "-i", "testsrc2=size=128x72:rate=24:duration=1", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=1", "-c:v", "libx264", "-threads", "1", "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-c:a", "aac", "-shortest", sdr)
info = probe(sdr)
require(any(s["codec_name"] == "aac" for s in info["streams"]), "SDR AAC encode/probe")
ff("-i", sdr, "-vf", "colorspace=all=bt709:iall=bt709,scale=96:54,setsar=1", "-c:v", "libx264", "-c:a", "aac", FIX / "sdr-output.mp4")
require(any(s["codec_name"] == "aac" for s in probe(FIX / "sdr-output.mp4")["streams"]), "SDR H264/AAC decode and re-encode MOV to MP4")
raw = FIX / "main10.yuv"
ff("-f", "lavfi", "-i", "testsrc2=size=128x72:rate=24:duration=1", "-pix_fmt", "yuv420p10le", "-c:v", "rawvideo", "-f", "rawvideo", raw)
for name, primaries, transfer, matrix in [("main10-sdr", "bt709", "bt709", "bt709"), ("main10-hlg", "bt2020", "arib-std-b67", "bt2020nc"), ("main10-pq", "bt2020", "smpte2084", "bt2020nc")]:
    hevc = FIX / (name + ".hevc")
    # This is an independent, pinned fixture-only encoder, never linked into FFmpeg.
    log = run(["x265", "--input", raw, "--input-res", "128x72", "--fps", "24", "--frames", "24", "--input-depth", "10", "--output-depth", "10", "--profile", "main10", "--preset", "ultrafast", "--pools", "none", "--frame-threads", "1", "--colorprim", primaries, "--transfer", transfer, "--colormatrix", matrix, "--range", "limited", "--output", hevc])
    (AUDIT / (name + "-x265.txt")).write_text(log)
    mp4 = FIX / (name + ".mp4")
    ff("-r", "24", "-i", hevc, "-c:v", "copy", "-tag:v", "hvc1", mp4)
    metadata = probe(mp4)
    (AUDIT / (name + "-probe.json")).write_text(json.dumps(metadata, indent=2) + "\n")
    stream = metadata["streams"][0]
    for key, value in {"codec_name": "hevc", "profile": "Main 10", "pix_fmt": "yuv420p10le", "color_primaries": primaries, "color_transfer": transfer, "color_space": matrix, "color_range": "tv"}.items():
        require(stream.get(key) == value, name + ":" + key)
    ff("-i", mp4, "-f", "null", "-")
    require(True, name + " decode")
    vf = "scale=96:54,format=yuv420p"
    if name != "main10-sdr":
        # Capability proof only: no production appearance or tone-mapping contract.
        vf = "zscale=t=linear:npl=100,format=gbrpf32le,tonemap=tonemap=clip,zscale=p=bt709:t=bt709:m=bt709:r=limited,format=yuv420p"
    output = FIX / (name + "-output.mp4")
    ff("-i", mp4, "-vf", vf, "-c:v", "libx264", "-threads", "1", output)
    ff("-i", output, "-f", "null", "-")
    out = probe(output)["streams"][0]
    require(out["codec_name"] == "h264" and out["pix_fmt"] == "yuv420p", name + " filter and H264 encode")
    require(int(out["nb_frames"]) == 24, name + " 24 output frames")
(AUDIT / "capability-results.json").write_text(json.dumps(results, indent=2) + "\n")
(AUDIT / "fixture-hashes.json").write_text(json.dumps({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(FIX.iterdir())}, indent=2) + "\n")
print(json.dumps(results, indent=2))
