#!/usr/bin/env python3
"""Fail closed on static archives; only reviewed dav1d and empty musl libdl added."""
import hashlib
import json
from pathlib import Path
import re
import sys

# v1.0.0 set, plus the approved libdav1d and musl compatibility archive only.
ALLOWED = {"libavcodec.a", "libavformat.a", "libavfilter.a", "libavdevice.a",
           "libavutil.a", "libswscale.a", "libswresample.a", "libx264.a",
           "libzimg.a", "libstdc++.a", "libgcc.a", "libgcc_eh.a", "libc.a",
           "libm.a", "libpthread.a", "libatomic.a", "libssp_nonshared.a",
           "libdav1d.a", "libdl.a"}


def inspect(content, libdl=Path('/usr/lib/libdl.a')):
    archives = sorted(set(re.findall(r"[\w./+-]+\.a\b", content)))
    if not archives or {Path(p).name for p in archives} - ALLOWED:
        raise RuntimeError("Unexpected or missing link map archives: " + repr(archives))
    if '/work/prefix/lib/libdav1d.a' not in archives:
        raise RuntimeError('Missing pinned static dav1d archive')
    # Check installed bytes even if a linker omits the empty LOAD input.
    if libdl.read_bytes() != b'!<arch>\n':
        raise RuntimeError('Approved musl libdl.a is no longer an empty 8-byte archive')
    for archive in archives:
        if Path(archive).name == 'libdl.a':
            if Path(archive).resolve() != libdl.resolve():
                raise RuntimeError('libdl.a has unexpected provenance: ' + archive)
    if re.search(r'libdl\.a\s*\(', content):
        raise RuntimeError('libdl.a contributed an object member')
    return archives


def main():
    audit = Path(sys.argv[1])
    linked = {name: inspect((audit / (name + '_g.map')).read_text())
              for name in ('ffmpeg', 'ffprobe')}
    evidence = {'status': 'PASS', 'linked_static_archives': linked,
                'libdl': {'provider': 'musl-dev-1.2.5-r12', 'already_pinned': True,
                          'path': '/usr/lib/libdl.a', 'size_bytes': 8,
                          'sha256': hashlib.sha256(b'!<arch>\n').hexdigest(),
                          'object_members': 0, 'object_code_contributed': False}}
    (audit / 'static-link.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
