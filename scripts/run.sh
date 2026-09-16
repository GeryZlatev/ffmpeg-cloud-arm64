#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
test -z "$(git status --porcelain)" || { echo 'Use a clean committed checkout.' >&2; exit 1; }
test ! -e dist || { echo 'dist already exists; preserve it and use a fresh checkout.' >&2; exit 1; }
case "$(docker info --format '{{.Architecture}}')" in
    aarch64|arm64) ;;
    *) echo 'Native ARM64 Docker is required; no implicit QEMU fallback.' >&2; exit 1 ;;
esac
commit=$(git rev-parse HEAD)
python3 scripts/prepare.py
docker build --platform linux/arm64 --network=none -f build/Dockerfile -t ffmpeg-gate1-builder .
mkdir -p dist/first dist/second
for attempt in first second; do
    docker run --rm --platform linux/arm64 --network none \
        -e BUILD_REPOSITORY_COMMIT="$commit" \
        -v "$PWD/dist/$attempt:/out" ffmpeg-gate1-builder
done
python3 scripts/compare.py dist/first dist/second | tee dist/reproducibility.json
