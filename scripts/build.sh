#!/usr/bin/env bash
set -euo pipefail
umask 022
test "$(uname -m)" = aarch64
[[ ${BUILD_REPOSITORY_COMMIT:?} =~ ^[0-9a-f]{40}$ ]]
test ! -e /work
mkdir -p /work/src /work/prefix /out/package/bin /out/audit
cd /recipe
shellcheck scripts/*.sh
python3 -m compileall -q scripts
python3 scripts/lint.py
export HOME=/work/home
mkdir -m 700 "$HOME" /work/gnupg
export GNUPGHOME=/work/gnupg
gpg --batch --import build/ffmpeg-release-key.asc
fingerprint=$(gpg --batch --with-colons --fingerprint | awk -F: '$1=="fpr" {print $10; exit}')
test "$fingerprint" = FCF986EA15E6E293A5644F10B4322F04D67658D8
gpg --batch --status-fd 1 --verify /inputs/ffmpeg.tar.xz.asc /inputs/ffmpeg.tar.xz > /out/audit/signature.txt
grep -q 'VALIDSIG FCF986EA15E6E293A5644F10B4322F04D67658D8 ' /out/audit/signature.txt
for source in ffmpeg zimg x264 dav1d; do
    mkdir "/work/src/$source"
    if [ "$source" = ffmpeg ]; then archive=/inputs/ffmpeg.tar.xz; else archive="/inputs/$source.tar.gz"; fi
    tar -xf "$archive" --strip-components=1 -C "/work/src/$source"
done
export CFLAGS='-O2 -march=armv8-a -ffile-prefix-map=/work=/usr/src/build -fdebug-prefix-map=/work=/usr/src/build'
export CXXFLAGS="$CFLAGS"
export LDFLAGS='-static -static-libgcc -static-libstdc++ -Wl,--build-id=none'
export PKG_CONFIG_LIBDIR=/work/prefix/lib/pkgconfig
export ZERO_AR_DATE=1
cd /work/src/dav1d
python3 - <<'PY'
import json, subprocess, shlex
from pathlib import Path
flags = json.loads(Path('/recipe/build/dav1d-configure.json').read_text())
argv = ['meson', 'setup', 'build'] + flags
Path('/out/audit/dav1d-configure.txt').write_text(shlex.join(argv) + '\n')
subprocess.run(argv, check=True)
PY
ninja -C build -j2
ninja -C build install
cp build/meson-logs/meson-log.txt /out/audit/dav1d-meson-log.txt
cp build/meson-info/intro-buildoptions.json /out/audit/dav1d-buildoptions.json
cp build/config.h /out/audit/dav1d-config.h
cp /work/prefix/lib/pkgconfig/dav1d.pc /out/audit/dav1d.pc
test -f /work/prefix/lib/libdav1d.a
test ! -e /work/prefix/lib/libdav1d.so
cd /work/src/x264
./configure --prefix=/work/prefix --host=aarch64-linux-musl --enable-static --disable-cli --disable-opencl --bit-depth=8 --chroma-format=420
make -j2
make install
cp config.mak /out/audit/x264-config.mak
cd /work/src/zimg
# autogen.sh was inspected at the pinned source revision; it only runs autoreconf.
./autogen.sh
./configure --prefix=/work/prefix --host=aarch64-linux-musl --enable-static --disable-shared --disable-testapp --disable-example --disable-unit-test
make -j2
make install
cp config.log /out/audit/zimg-config.log
cd /work/src/ffmpeg
python3 - <<'PY'
import json, subprocess, shlex
from pathlib import Path
flags=json.loads(Path('/recipe/build/ffmpeg-configure.json').read_text())
Path('/out/audit/ffmpeg-configure.txt').write_text(shlex.join(['./configure']+flags)+'\n')
subprocess.run(['./configure']+flags,check=True)
PY
# Keep linker maps to audit exactly which static archives supplied code.
printf '%s\n' 'LDFLAGS-ffmpeg += -Wl,-Map,ffmpeg_g.map' \
    'LDFLAGS-ffprobe += -Wl,-Map,ffprobe_g.map' >> ffbuild/config.mak
make -j2
cp ffmpeg ffprobe /out/package/bin/
cp ffbuild/config.log ffbuild/config.mak /out/audit/
cp ffmpeg_g.map ffprobe_g.map /out/audit/
python3 /recipe/scripts/static_link.py /out/audit
python3 /recipe/scripts/verify.py /out/package/bin /out/audit
python3 /recipe/scripts/compatibility.py /out/package/bin /out/audit
python3 /recipe/scripts/package.py
