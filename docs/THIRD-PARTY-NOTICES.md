# Third-party notices

These notices apply to the packaged third-party executables. This repository does
not relicense FFmpeg, x264 or their dependencies under project-specific terms.
No separate project license has been added in Gate 1.

| Component | Origin and copyright | Terms and included notice |
| --- | --- | --- |
| FFmpeg 7.1.5 and its libavcodec, libavformat, libavfilter, libavdevice, libavutil, libswscale, libswresample | https://ffmpeg.org; copyright the FFmpeg developers, individual notices retained in source | GPL-2.0-or-later for this GPL-enabled configuration; `FFmpeg-GPL-2.0.txt`, `FFmpeg-LICENSE.md` |
| x264, commit recorded in SOURCE-MANIFEST.json | https://code.videolan.org/videolan/x264; copyright 2003–2025 x264 project and contributing authors | GPL-2.0-or-later; `x264-GPL-2.0.txt` |
| zimg 3.0.6 | https://github.com/sekrit-twc/zimg; copyright its contributors, author notices in source | WTFPL version 2; `zimg-WTFPL-2.txt` |
| musl 1.2.5 (Alpine 1.2.5-r12), including libc, libm, pthread and startup code | https://musl.libc.org; Rich Felker and contributors, including incorporated code attribution | MIT and incorporated permissive notices; complete `musl-COPYRIGHT.txt` |
| GCC 14.2.0 runtime, Alpine 14.2.0-r6: libgcc/libgcc_eh and libstdc++ | https://gcc.gnu.org; Free Software Foundation and contributors | GPL-3.0 with GCC Runtime Library Exception 3.1; `GCC-GPL-3.0.txt`, `GCC-RUNTIME-EXCEPTION.txt`; individual source headers retained in companion source |
| libatomic.a, supplied by locked gcc 14.2.0-r6 | https://gcc.gnu.org; Free Software Foundation and contributors | GPL-3.0-or-later with GCC Runtime Library Exception 3.1; existing `GCC-GPL-3.0.txt` and `GCC-RUNTIME-EXCEPTION.txt` |
| libssp_nonshared.a, supplied by locked musl-dev 1.2.5-r12 | Alpine musl packaging compatibility wrapper (`__stack_chk_fail_local.c`), retained in the pinned aports-musl source snapshot | MIT per pinned musl-dev package metadata; wrapper has no separate license header; this is not GCC libssp |

`LICENSES/` contains the named files. BUILD-MANIFEST.json lists linker archive
inputs, including `LOAD` entries; the audit maps distinguish inputs from archives
that supplied extracted object members and symbols. In inspected Gate 1 run #7,
libatomic.a and libssp_nonshared.a are inputs to both executables but contribute
no extracted members or symbols. Empty musl compatibility archives likewise do
not represent additional code. The two expected inputs add no dependency pins
or change the documented GPL conclusion; their source/recipe snapshots and the
applicable GCC exception and musl notices are already retained.

libx264 enables GPL code in FFmpeg. This is not an LGPL-only binary. There is no
`--enable-nonfree` and no commercial x264 license assertion. GCC runtime exception
terms must be retained and assessed for any changes to this ordinary GCC build.
This is an engineering inventory, not a guarantee of legal compliance or patent
clearance. Review distribution obligations before v1.0.0.

x265 3.6-r0 is used only in the build environment to generate synthetic test
fixtures. It is not linked into the delivered binaries or shipped in the runtime
archive. Its pinned Alpine package and all other build-only packages are listed
with their license metadata in SOURCE-MANIFEST.json. Their use as tools does not
make them runtime dependencies. Build-only APKs are not redistributed; their exact upstream recipe commits
identify their source and licensing information.

Read `LICENSES/CORRESPONDING-SOURCE.md` for source availability and reconstruction
instructions. Preserve the runtime notices, manifests and companion source when
sharing these audit outputs.
