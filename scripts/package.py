#!/usr/bin/env python3
"""Package runtime, licenses and manifests, and a separate reconstruction bundle."""
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tarfile

RECIPE = Path("/recipe")
OUT = Path("/out")
PKG = OUT / "package"
EPOCH = int(os.environ["SOURCE_DATE_EPOCH"])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(*args):
    return subprocess.check_output(args, stderr=subprocess.STDOUT, text=True).strip()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


sources = json.loads((RECIPE / "build/sources.lock.json").read_text())
packages = json.loads((RECIPE / "build/apk-lock.json").read_text())
flags = json.loads((RECIPE / "build/ffmpeg-configure.json").read_text())
# Repeat the fail-closed inspection at packaging, using the same audited policy.
from static_link import inspect
linked = {}
for name in ("ffmpeg", "ffprobe"):
    content = (OUT / "audit" / (name + "_g.map")).read_text()
    linked[name] = inspect(content)
shutil.copytree(RECIPE / "licenses", PKG / "LICENSES")
shutil.copy(RECIPE / "docs/THIRD-PARTY-NOTICES.md", PKG / "THIRD-PARTY-NOTICES.md")
shutil.copy(RECIPE / "docs/CORRESPONDING-SOURCE.md", PKG / "LICENSES/CORRESPONDING-SOURCE.md")
write(PKG / "SOURCE-MANIFEST.json", dict(sources, alpine_packages=packages))
manifest = {
    "build_repository": "https://github.com/GeryZlatev/ffmpeg-cloud-arm64",
    "build_repository_commit": os.environ["BUILD_REPOSITORY_COMMIT"],
    "platform": "linux/arm64", "libc": "musl 1.2.5-r12", "linkage": "static",
    "container": sources["container"], "source_date_epoch": EPOCH,
    "ffmpeg": "7.1.5", "zimg": "3.0.6", "x264_commit": sources["x264_commit"],
    "runtime_candidate": "1.0.1", "dav1d": sources['dav1d_version'],
    "dav1d_commit": sources['dav1d_commit'],
    "dav1d_configure_argv": ['meson', 'setup', 'build'] + json.loads((RECIPE / 'build/dav1d-configure.json').read_text()),
    "compiler": command("gcc", "--version"), "cxx_compiler": command("g++", "--version"),
    "linker": command("ld", "--version"),
    "build_tools": {name: command(name, "--version") for name in ["make", "autoconf", "automake", "libtool", "pkgconf", "python3", "tar", "meson", "ninja"]},
    "ffmpeg_configure_argv": ["./configure"] + flags,
    "ffmpeg_configure_command": shlex.join(["./configure"] + flags),
    "x264_configure_argv": ["./configure", "--prefix=/work/prefix", "--host=aarch64-linux-musl", "--enable-static", "--disable-cli", "--disable-opencl", "--bit-depth=8", "--chroma-format=420"],
    "zimg_configure_argv": ["./configure", "--prefix=/work/prefix", "--host=aarch64-linux-musl", "--enable-static", "--disable-shared", "--disable-testapp", "--disable-example", "--disable-unit-test"],
    "environment": {k: os.environ[k] for k in ["LANG", "LC_ALL", "TZ", "SOURCE_DATE_EPOCH", "CFLAGS", "CXXFLAGS", "LDFLAGS", "PKG_CONFIG_LIBDIR", "ZERO_AR_DATE"]},
    "binary_files": {"bin/" + name: {"size_bytes": (PKG / "bin" / name).stat().st_size, "sha256": sha(PKG / "bin" / name)} for name in ["ffmpeg", "ffprobe"]},
    "linked_static_archives": linked,
    "static_link_audit": json.loads((OUT / 'audit/static-link.json').read_text()),
    "compatibility_results": json.loads((OUT / 'audit/compatibility-results.json').read_text()),
    "fixture_provenance": json.loads((RECIPE / 'fixtures/manifest.json').read_text()),
    "capability_results": json.loads((OUT / "audit/capability-results.json").read_text()),
    "reproducibility": "See sibling reproducibility.json comparing two independent builds; a single build is not evidence.",
}
write(PKG / "BUILD-MANIFEST.json", manifest)
baseline = json.loads((RECIPE / 'build/baseline-v1.0.0/provenance.json').read_text())
write(OUT / 'audit/size-comparison.json', {
    'baseline': baseline,
    'candidate': manifest['binary_files'],
    'delta_bytes': {name: value['size_bytes'] - baseline['binary_files'][name]['size_bytes']
                    for name, value in manifest['binary_files'].items()}})
(PKG / "SHA256SUMS").write_text("".join(sha(p) + "  " + str(p.relative_to(PKG)) + "\n" for p in sorted(PKG.rglob("*")) if p.is_file() and p.name != "SHA256SUMS"))


def archive(folder, output):
    # Fixed metadata, sorted members, gzip header without wall-clock timestamp.
    import gzip
    with output.open("wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=EPOCH) as gz, tarfile.open(fileobj=gz, mode="w", format=tarfile.GNU_FORMAT) as tar:
        for path in sorted(folder.rglob("*")):
            if not path.is_file():
                continue
            info = tar.gettarinfo(str(path), arcname=str(path.relative_to(folder)))
            info.uid = info.gid = 0
            info.uname = info.gname = "root"
            info.mtime = EPOCH
            info.mode = 0o755 if "bin" in path.relative_to(folder).parts else 0o644
            with path.open("rb") as file:
                tar.addfile(info, file)


archive(PKG, OUT / "ffmpeg-7.1.5-linux-arm64-musl.tar.gz")
# These source copies accompany even the audit binaries, not just a later release.
source_dir = OUT / "corresponding-source"
shutil.copytree(RECIPE, source_dir / "recipe", ignore=shutil.ignore_patterns("__pycache__"))
(source_dir / "inputs").mkdir()
for item in sources["sources"]:
    shutil.copy(Path("/inputs") / item["file"], source_dir / "inputs" / item["file"])
(source_dir / "BUILD-REPOSITORY-COMMIT").write_text(os.environ["BUILD_REPOSITORY_COMMIT"] + "\n")
archive(source_dir, OUT / "corresponding-source.tar.gz")
shutil.rmtree(source_dir)
(OUT / "ARCHIVE-SHA256SUMS").write_text("".join(sha(p) + "  " + p.name + "\n" for p in sorted(OUT.glob("*.tar.gz"))))
print(json.dumps(manifest, indent=2))
