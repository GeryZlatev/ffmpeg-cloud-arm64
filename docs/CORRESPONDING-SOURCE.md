# Corresponding Source and reconstruction

Every successful Gate 1 artifact includes `corresponding-source.tar.gz` alongside
the runtime archive. It contains the exact FFmpeg, x264 and zimg input archives,
FFmpeg signature, GCC 14.2.0 and musl 1.2.5 source archives, Alpine GCC/musl recipe
snapshots and patches, the complete Alpine package lock, and this build
recipe. The package manifest records the build repository commit. FFmpeg/x264/zimg
source is unmodified; generated configure/build files and linker-map flags are
produced by the included scripts. The x264 source archive has no Git history, so
its abbreviated runtime version string is not a substitute for the manifest's
full commit SHA.

To reconstruct from the companion on an ARM64 Docker host: unpack it, put the
`inputs/` directory at `recipe/cache/`, and run from `recipe/`:

```sh
python3 scripts/prepare.py
docker build --platform linux/arm64 --network=none -f build/Dockerfile -t ffmpeg-gate1-builder .
mkdir result
docker run --rm --platform linux/arm64 --network none \
  -e BUILD_REPOSITORY_COMMIT="$(cat ../BUILD-REPOSITORY-COMMIT)" \
  -v "$PWD/result:/out" ffmpeg-gate1-builder
```

The base image is identified by an immutable ARM64 manifest digest; it must be
available locally or retrievable from Docker Hub. Container setup installs
verified Alpine-signed APKs offline. The two directly compiled external media
libraries and FFmpeg are built offline. Their source license files and original
copyright headers are retained in the source archives. GCC/musl are the exact
Alpine prebuilt toolchain/runtime packages, not falsely represented as rebuilt
from those upstream archives. The companion Alpine recipe snapshots contain the
patches and build options for reconstructing these runtime packages. Compiler
bootstrap dependencies can be found via those recipes; reproducing Alpine's
compiler itself is outside this gate.

Build-only APKs are not redistributed in the source or runtime archives. They
are downloaded from their locked official URLs by `prepare.py` and verified
before use. Each package's `origin` and `aports_commit` identifies its Alpine
recipe, upstream source and patches. GitHub Actions artifacts expire after
14 days and are not a durable source offer. Do not use an expired artifact link
as the source availability plan for a release.

For v1.0.0, archive the reviewed recipe, all required source and patches, notices,
checksums and build evidence together with the binaries for the applicable
retention period. Review the scope of Corresponding Source and any GCC exception
conditions with the distributor's legal reviewer. Source URLs alone must not be
assumed to satisfy distribution obligations.
