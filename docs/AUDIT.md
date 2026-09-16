# Source and toolchain audit

`build/sources.lock.json` is the source lock. `build/apk-lock.json` pins all 75
selected build/fixture packages, including transitive dependencies, by exact
version, official Alpine URL and SHA-256. The immutable Alpine 3.22.1 ARM64 image
is a bootstrap environment; the installed musl is the locked 1.2.5-r12 package.
No package index or floating resolution runs in CI. Deleted upstream inputs cause
a hard failure; never silently substitute a newer package or hash.

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
codec libraries plus x264, zimg, musl and GCC runtime are the allowed linked set.
All filters and parsers remain available to preserve normalization primitives;
external autodetection, networking, hardware acceleration and unrelated encoders
are disabled. The decoder/container allowlist targets the requested phone media
and is not a promise of compatibility with every phone recording mode (for
example AV1, ProRes, Dolby Vision or unrelated audio codecs).
