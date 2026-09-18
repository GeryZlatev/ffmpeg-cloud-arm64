# ffmpeg-cloud-arm64

Gate 1 builds auditable Linux ARM64/musl FFmpeg and FFprobe executables for
Laravel Cloud media processing. It does not change an application, Laravel Cloud
or R2. It publishes only expiring GitHub Actions audit artifacts: no release,
version tag, Packagist package, main-branch publishing or application integration.
A successful CI run, including the two-build comparison, is required before
calling the output reproducible. See the PR checks and downloaded evidence;
source pinning alone does not establish byte-identical binaries.

The v1.0.1 candidate adds CPU AV1 decoding through static **dav1d 1.5.4**,
VP9/MP3/ALAC input decoding and MJPEG/image2 thumbnails. All v1.0.0 tests and
capabilities are retained and checked against the immutable release baseline.
See [compatibility and provenance](docs/V1.0.1-COMPATIBILITY.md) for exact additions,
fixture provenance, licensing, and the approved empty musl libdl archive.

The media stack is FFmpeg **7.1.5**, zimg **3.0.6**, and x264 commit
**b35605ace3ddf7c1a5d67a2eb553f034aef41d55**. The executables are GPL-enabled
because of x264. The pinned compiler is GCC **14.2.0-r6**, linker binutils
**2.44-r3**, and static musl **1.2.5-r12**. The bootstrap image is:

```
alpine:3.22.1@sha256:4562b419adf48c5f3c763995d6014c123b3ce1d2e0ef2613b189779caa787192
```

GitHub Actions uses the supported native `ubuntu-24.04-arm` public-repository
runner. Local execution requires a native ARM64 Docker engine and Python 3.
`run.sh` rejects an x86 engine; no implicit QEMU fallback is supported. The host
orchestrates downloads and Docker; compilation/tests run offline inside the
pinned ARM64 Alpine environment. A fresh container and `/work` are used for each
build, without build caches or host compiler/library mounts.

```sh
git clone https://github.com/GeryZlatev/ffmpeg-cloud-arm64.git
cd ffmpeg-cloud-arm64
git checkout <reviewed-full-commit-sha>
bash scripts/run.sh
```

Use a clean committed checkout with no `dist/` directory. Preserve previous
results and use a separate checkout to repeat the audit. `prepare.py` only fetches
locked URLs and checks hashes; APK signatures are also checked by Alpine's
package manager. It does not execute remote scripts. The build checks FFmpeg's
PGP signature using the committed fingerprint before extracting/building source.
Network access is disabled during installation, compilation and testing.

The runtime archive contains exactly these categories of files:

```
bin/ffmpeg
bin/ffprobe
BUILD-MANIFEST.json
SOURCE-MANIFEST.json
SHA256SUMS
THIRD-PARTY-NOTICES.md
LICENSES/
```

`dist/first/` and `dist/second/` hold independent outputs and audit logs. The
runtime archive and separate `corresponding-source.tar.gz` have external checksums
in `ARCHIVE-SHA256SUMS`. The runtime's `SHA256SUMS` covers every other runtime
file, including both manifests and licenses. Verify from the appropriate folder:

```sh
sha256sum -c ARCHIVE-SHA256SUMS
# After unpacking the runtime archive:
sha256sum -c SHA256SUMS
```

CI fails on a mismatched binary comparison, missing required capability,
incorrect ELF architecture/dynamic linkage, unexpected static archive, invalid
signature/hash or failed fixture. `reproducibility.json` compares actual binary
bytes and SHA-256 values from two independent compiles. Manifests record actual
sizes/hashes, source URLs/hashes, build repository commit, exact configure argv,
compiler/linker/tool versions, flags/environment and linked archive paths.
A fixed SOURCE_DATE_EPOCH represents 2026-06-20 UTC; no wall-clock build timestamp
is embedded. Repeatability on one runner is not proof across all hosts.

Synthetic tests generate one-second 128×72 clips: H.264 SDR with AAC in MOV,
HEVC Main10 SDR, BT.2020 HLG and BT.2020 PQ in MP4. The fixture-only pinned x265
CLI is not linked or packaged. Tests inspect HEVC Main 10/pixel format and all
color fields, decode each input, execute filters, encode H.264 and decode the
result. The SDR test also decodes/re-encodes AAC and executes colorspace/scale.
HLG/PQ tests execute zscale and tonemap; their output is a capability smoke test,
not the BARDARO tone-mapping contract or a quality reference. Synthetic media is
generated from FFmpeg test patterns, with no third-party sample footage.

All built-in filters and parsers are retained for normalization primitives and
normal probing. Encoders/decoders, I/O and muxers/demuxers are constrained to the
requested media plus raw/PCM test primitives. This is not a general-purpose
FFmpeg distribution; see [audit scope](docs/AUDIT.md) for limits and pin review.
Exact FFmpeg configure command (also generated into the audit and manifest):

```sh
./configure --prefix=/opt/ffmpeg --arch=aarch64 --cpu=armv8-a --target-os=linux --cc=gcc --cxx=g++ --enable-gpl --enable-libx264 --enable-libzimg --enable-libdav1d --enable-static --disable-shared --disable-autodetect --disable-debug --disable-doc --disable-ffplay --disable-network --disable-hwaccels --disable-vulkan --disable-vaapi --disable-vdpau --disable-encoders --enable-encoder=libx264,aac,rawvideo,wrapped_avframe,mjpeg --disable-decoders --enable-decoder=h264,hevc,aac,pcm_s16le,pcm_s16be,rawvideo,wrapped_avframe,libdav1d,vp9,mp3,alac,mjpeg --disable-muxers --enable-muxer=mov,mp4,null,rawvideo,image2 --disable-demuxers --enable-demuxer=mov,h264,hevc,aac,rawvideo,matroska,mp3,image2 --disable-protocols --enable-protocol=file,pipe --disable-indevs --enable-indev=lavfi --disable-outdevs --disable-postproc --pkg-config-flags=--static '--extra-cflags=-O2 -march=armv8-a -ffile-prefix-map=/work=/usr/src/build -fdebug-prefix-map=/work=/usr/src/build' '--extra-cxxflags=-O2 -march=armv8-a -ffile-prefix-map=/work=/usr/src/build -fdebug-prefix-map=/work=/usr/src/build' '--extra-ldflags=-static -static-libgcc -static-libstdc++ -Wl,--build-id=none' '--extra-libs=-lstdc++ -lm -lpthread'
```

Repository layout:

```
.github/workflows/gate1.yml
build/
  Dockerfile
  apk-lock.json
  ffmpeg-configure.json
  ffmpeg-release-key.asc
  sources.lock.json
docs/
  AUDIT.md
  CORRESPONDING-SOURCE.md
  DISTRIBUTION.md
  THIRD-PARTY-NOTICES.md
licenses/
  FFmpeg-GPL-2.0.txt
  FFmpeg-LICENSE.md
  GCC-GPL-3.0.txt
  GCC-RUNTIME-EXCEPTION.txt
  musl-COPYRIGHT.txt
  x264-GPL-2.0.txt
  zimg-WTFPL-2.txt
scripts/
  build.sh
  compare.py
  lint.py
  package.py
  prepare.py
  run.sh
  verify.py
.dockerignore
.gitignore
README.md
```

Read [source reconstruction](docs/CORRESPONDING-SOURCE.md),
[third-party notices](docs/THIRD-PARTY-NOTICES.md), and the
[future distribution/update design](docs/DISTRIBUTION.md) before distributing
binaries. No third-party binary is licensed under a repository-specific license.
