# Source and toolchain audit

`build/sources.lock.json` is the source lock. `build/apk-lock.json` pins all 79
selected build/fixture packages, including transitive dependencies, by exact
version, official Alpine URL and SHA-256. The immutable Alpine 3.22.1 ARM64 image
is a bootstrap environment; the installed musl is the locked 1.2.5-r12 package.
No package index or floating resolution runs in CI. Deleted upstream inputs cause
a hard failure; never silently substitute a newer package or hash.

`linux-headers` 6.14.2-r0 supplies `/usr/include/asm/hwcap.h` for zimg's ARM
build. It is a build-time Linux UAPI header dependency, not a linked library or
installed kernel. Its APK metadata declares GPL-2.0-only; the inspected
`asm/hwcap.h` declares `GPL-2.0 WITH Linux-syscall-note`. Its exact Alpine source
recipe commit and APK hash are recorded in the package lock and generated source
manifest. ARM SIMD/NEON and CPU detection remain enabled.

FFmpeg's downloaded release archive is checked by SHA-256 and its detached PGP
signature before extraction. The committed upstream public key is hash-checked,
and its primary fingerprint must be
`FCF986EA15E6E293A5644F10B4322F04D67658D8`, as published on
https://ffmpeg.org/download.html. Signature status is retained. The signed tarball
is the build input corresponding to n7.1.5; we do not claim verification of a
separate Git tag signature. zimg release-3.0.6 resolves through annotated tag
`ef19c4adcfda6e8b4af57aa9dc640e48f6306c35` to commit
`f819b14e8f39d1282400b0d9543e8ef73c1b2bbd`. That tag is unsigned; its authoritative
GitHub archive is content-hashed, not described as cryptographically signed.

The x264 pin is `b35605ace3ddf7c1a5d67a2eb553f034aef41d55` in the authoritative
VideoLAN project. Selection review inspected the upstream commit metadata and
diff: 2025-06-08, “i8mm & neon hpel_filter optimization”, parent
`291476d73386eb6f0362214f28dce058c3fff3d9`. Changes are in
`common/aarch64/mc-a.S` and `common/aarch64/mc-c.c`, adding I8MM dispatch behind
CPU capability detection and revising NEON half-pixel arithmetic. No configure,
network, installer or license changes occur in that commit. The selected source
configure/version machinery and license were inspected. This is a bounded
selection review, not an independent security audit of all x264 history or a
formal verification of the assembly. A newer 2025-09-10 commit concerned RISC-V
build support and is not needed for this ARM64 target.

zimg's inspected autogen.sh runs only `autoreconf --verbose --install --force`.
Its optional googletest submodule is not used: examples, testapp and unit tests
are disabled. No mutable submodule fetch occurs. The x264 CLI/OpenCL and 10-bit
encoder are excluded; the required 10-bit decoder is FFmpeg's internal HEVC
implementation. Build-only x265 generates 10-bit fixtures with explicit VUI
color values. They demonstrate execution and metadata routing capabilities,
not photographic HDR fidelity or the BARDARO production tone-mapping contract.

GCC 14.2.0-r6, binutils 2.44-r3, make 4.4.1-r3, autoconf 2.72-r1, automake
1.17-r1, libtool 2.5.4-r1 and pkgconf 2.4.3-r0 are pinned. Exact executed version
outputs go into BUILD-MANIFEST.json. We use official Alpine binary tool packages
to avoid implementing and auditing a compiler bootstrap here. All their bytes
are hash-pinned and packaging commits recorded; this materially constrains the
build environment but does not prove those compiler binaries trustworthy or
reproduce Alpine's own bootstrap. Static runtime source/patches are also retained.

The hosted runner, Docker daemon and host kernel are not immutable build inputs.
They orchestrate a digest-pinned, offline container and do not supply compiler
headers/libraries. Host Python downloads and hashes inputs; build Python is
pinned. A changed runner/kernel/CPU can still affect scheduling or detection, so
byte-identical results must be measured. Explicit armv8-a target, fixed paths,
fixed locale/timezone/SOURCE_DATE_EPOCH, no debug symbols, no linker build ID,
deterministic archives and two separate containers reduce nondeterminism.
The check establishes repeatability on the tested runner, not cross-host proof.

Link maps are captured before stripping and reject unexpected archive names.
Static ELF checks reject an interpreter or DT_NEEDED entries. FFmpeg's internal
codec libraries plus x264, zimg, dav1d, musl and GCC runtime are the allowed linked set.
All filters and parsers remain available to preserve normalization primitives;
external autodetection, networking, hardware acceleration and unrelated encoders
are disabled. The decoder/container allowlist targets the requested phone media
and is not a promise of compatibility with every phone recording mode (for
example ProRes, Dolby Vision or unrelated audio codecs).

The explicit archive allowlist also includes `/usr/lib/libatomic.a`, supplied by
locked `gcc=14.2.0-r6`, and `/usr/lib/libssp_nonshared.a`, supplied by locked
`musl-dev=1.2.5-r12`. Ownership was verified from the hash-checked APKs.
FFmpeg's atomic configure probe tries `-latomic` first and retains it on success;
Alpine's GCC driver patch adds `-lssp_nonshared` unconditionally for musl.
The latter archive provides a compatibility wrapper for `__stack_chk_fail_local`.

In Gate 1 run #7, both executables' maps list these archives as `LOAD` inputs,
but neither archive contributes an extracted object member or symbol. Stack
protector symbols are supplied by musl's `libc.a`; ARM64 atomic helpers are
supplied by `libgcc.a`. A listed linker input is not proof that its code entered
the executable: the manifest's archive list includes `LOAD` entries, while the
maps identify extracted members and their symbol references. This observation
is specific to the inspected build. Every other unexpected archive remains a
hard failure, and static ELF validation remains unchanged.

The v1.0.1 additive audit and exact dav1d/libdl provenance are documented in
[V1.0.1-COMPATIBILITY.md](V1.0.1-COMPATIBILITY.md). The original v1.0.0
recipe/tests are retained as a regression baseline; no v1.0.0 asset is changed.
