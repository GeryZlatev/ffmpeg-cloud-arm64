# Original synthetic compatibility fixtures

These four small files were generated for this repository from integer-only
moving YUV patterns and a triangle-wave PCM signal. No third-party media or
copyrighted sample footage was used. The source patterns are fully defined in
`scripts/generate_compat_fixtures.py` and their SHA-256 values are in the manifest.

Authoring command (pass a new output directory):

```sh
python3 scripts/generate_compat_fixtures.py /path/to/fixture-only/ffmpeg new-fixtures
```

The tool used was Homebrew ARM64/macOS FFmpeg 9.0.1 (formula 9.0.1_1), with
SVT-AV1 4.2.0, libvpx 1.17.0 and LAME 4.0; ALAC uses FFmpeg's own encoder.
`manifest.json` records the executed version/configuration, exact commands,
encoder diagnostics, executable hash and library hashes. Each media file was
generated independently twice and verified byte-identical on that authoring
environment. This is not a claim of cross-version encoder determinism.

The fixtures are **data inputs**, not runtime components. The native build
consumes the checked-in exact bytes after SHA-256 validation; it does not run,
download, install or link the authoring FFmpeg, SVT-AV1, libvpx or LAME. Their
versions do not replace the runtime's pinned FFmpeg 7.1.5. Regeneration is an
explicit fixture-maintenance operation; it is not needed to reconstruct the
runtime or run the audit. The original fixture bytes and generation script are
included in the corresponding-source recipe.

AV1 MP4 and lossless VP9 WebM each contain 24 frames at 128x72. MP3 and ALAC
M4A each decode to 48,000 mono samples at 48 kHz (MP3 includes gapless metadata).
The image2/JPEG fixture is generated anew by each candidate build from the
existing H.264 SDR fixture, then decoded by that same candidate.
