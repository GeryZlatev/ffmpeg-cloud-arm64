#!/usr/bin/env python3
"""Actual CPU decode/thumbnail paths and full v1.0.0 capability superset checks."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

RECIPE = Path(__file__).resolve().parents[1]
BIN, AUDIT = map(Path, sys.argv[1:])
FIX = RECIPE / 'fixtures'
BASE = RECIPE / 'build/baseline-v1.0.0'
OUT = AUDIT / 'fixtures'
results = {}
commands = []


def run(argv):
    argv = list(map(str, argv))
    process = subprocess.run(argv, capture_output=True, text=True)
    commands.append({'argv': argv, 'returncode': process.returncode, 'stderr': process.stderr})
    (AUDIT / 'compatibility-commands.json').write_text(json.dumps(commands, indent=2) + '\n')
    if process.returncode:
        raise RuntimeError(f'{argv}\n{process.stdout}\n{process.stderr}')
    return process.stdout


def ff(*args):
    return run([BIN / 'ffmpeg', '-hide_banner', '-nostdin', '-y', '-v', 'error',
                '-xerror', '-err_detect', 'explode', *args])


def require(condition, label):
    if not condition:
        raise AssertionError(label)
    results[label] = 'PASS'
    (AUDIT / 'compatibility-results.json').write_text(json.dumps(results, indent=2) + '\n')


def probe(path):
    return json.loads(run([BIN / 'ffprobe', '-v', 'error', '-count_frames', '-show_frames',
                           '-show_streams', '-of', 'json', path]))


def listing_names(listing):
    return {name for line in listing.splitlines()
            if re.match(r'^\s*[.A-Z|]{1,6}\s+\S+', line)
            for name in line.split()[1].split(',') if name != '='}


manifest = json.loads((FIX / 'manifest.json').read_text())
for name, expected in manifest['files'].items():
    data = (FIX / name).read_bytes()
    require(len(data) == expected['size_bytes'] and hashlib.sha256(data).hexdigest() == expected['sha256'],
            name + ' pinned synthetic fixture')

for kind in ('filters', 'encoders', 'decoders', 'demuxers', 'muxers'):
    before = listing_names((BASE / (kind + '.txt')).read_text())
    after = listing_names((AUDIT / (kind + '.txt')).read_text())
    require(bool(before) and before <= after, kind + ' v1.0.0 superset: ' + ','.join(sorted(before - after)))

# config.mak covers parsers, bitstream filters, protocols and internal components
# as well as the human-readable listings. No enabled baseline component may vanish.
before = set(re.findall(r'^(CONFIG_\w+)=yes$', (BASE / 'config.mak').read_text(), re.M))
after = set(re.findall(r'^(CONFIG_\w+)=yes$', (AUDIT / 'config.mak').read_text(), re.M))
require(bool(before) and before <= after, 'all enabled v1.0.0 CONFIG components preserved: ' + ','.join(sorted(before - after)))
previous = json.loads((BASE / 'capability-results.json').read_text())
current = json.loads((AUDIT / 'capability-results.json').read_text())
require(all(current.get(k) == v == 'PASS' for k, v in previous.items()), 'all v1.0.0 functional assertions still pass')
for component in ('LIBDAV1D', 'LIBDAV1D_DECODER', 'VP9_DECODER', 'MP3_DECODER', 'ALAC_DECODER',
                  'MJPEG_ENCODER', 'MJPEG_DECODER', 'IMAGE2_MUXER', 'IMAGE2_DEMUXER',
                  'MATROSKA_DEMUXER', 'MP3_DEMUXER'):
    require('CONFIG_' + component in after, component + ' enabled')
davconfig = (AUDIT / 'dav1d-config.h').read_text()
for define in ('ARCH_AARCH64', 'HAVE_ASM', 'CONFIG_8BPC', 'CONFIG_16BPC'):
    require(bool(re.search(r'^#define ' + define + r' 1$', davconfig, re.M)), 'dav1d ' + define)

for name, codec, decoder in [('av1.mp4', 'av1', 'libdav1d'), ('vp9.webm', 'vp9', 'vp9')]:
    raw = OUT / (name + '.yuv')
    ff('-hwaccel', 'none', '-c:v', decoder, '-threads', '1', '-i', FIX / name,
       '-map', '0:v:0', '-an', '-fps_mode', 'passthrough', '-pix_fmt', 'yuv420p',
       '-c:v', 'rawvideo', '-threads', '1', '-f', 'rawvideo', raw)
    info = probe(FIX / name)
    stream = info['streams'][0]
    require(stream['codec_name'] == codec and stream['width'] == 128 and stream['height'] == 72,
            name + ' expected codec and 128x72 dimensions')
    require(int(stream['nb_read_frames']) == len(info['frames']) == 24,
            name + ' 24 decoded frames')
    require(raw.stat().st_size == 24 * 128 * 72 * 3 // 2 and len(set(raw.read_bytes())) > 1,
            name + ' CPU decode to 24 real YUV420 frames using ' + decoder)
    if codec == 'vp9':
        require(hashlib.sha256(raw.read_bytes()).hexdigest() == manifest['raw_sources']['pattern.yuv'],
                'VP9 lossless decoded pixels equal generated source')
    (AUDIT / (name + '-probe.json')).write_text(json.dumps(info, indent=2) + '\n')

for name, codec in [('mp3.mp3', 'mp3'), ('alac.m4a', 'alac')]:
    info = probe(FIX / name)
    stream = info['streams'][0]
    require(stream['codec_name'] == codec and int(stream['sample_rate']) == 48000 and stream['channels'] == 1,
            name + ' expected codec, 48kHz mono')
    require(sum(int(f['nb_samples']) for f in info['frames']) == 48000,
            name + ' 48000 decoded samples')
    output = OUT / (name + '-aac.mp4')
    ff('-c:a', codec, '-i', FIX / name, '-map', '0:a:0', '-c:a', 'aac', output)
    ff('-i', output, '-c:a', 'aac', '-f', 'null', '-')
    require(probe(output)['streams'][0]['codec_name'] == 'aac', name + ' decode and AAC/MP4 roundtrip')
    (AUDIT / (name + '-probe.json')).write_text(json.dumps(info, indent=2) + '\n')

jpeg = OUT / 'thumbnail.jpg'
ff('-i', OUT / 'sdr-h264.mov', '-vf', r'select=eq(n\,12),scale=96:54',
   '-frames:v', '1', '-an', '-c:v', 'mjpeg', '-threads', '1', '-pix_fmt', 'yuvj420p',
   '-f', 'image2', '-update', '1', jpeg)
data = jpeg.read_bytes()
require(data.startswith(b'\xff\xd8') and data.endswith(b'\xff\xd9'), 'thumbnail JPEG SOI/EOI markers')
info = probe(jpeg)
stream = info['streams'][0]
require(stream['codec_name'] == 'mjpeg' and stream['width'] == 96 and stream['height'] == 54
        and int(stream['nb_read_frames']) == 1, 'thumbnail decodes as one 96x54 JPEG')
raw = OUT / 'thumbnail.yuv'
ff('-f', 'image2', '-c:v', 'mjpeg', '-i', jpeg, '-frames:v', '1', '-pix_fmt', 'yuv420p',
   '-c:v', 'rawvideo', '-f', 'rawvideo', raw)
require(raw.stat().st_size == 96 * 54 * 3 // 2, 'MJPEG/image2 JPEG decodes to real pixels')
(AUDIT / 'compatibility-fixture-hashes.json').write_text(json.dumps(
    {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.iterdir())}, indent=2) + '\n')
print(json.dumps(results, indent=2))
