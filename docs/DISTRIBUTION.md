# Future release and application consumption — design only

No release, version tag, merge, Packagist registration or application integration
is performed by Gate 1. There is no main-push or tag-push publishing workflow.

Before a future v1.0.0, the maintainer must approve the source/license inventory,
Corresponding Source retention plan, exact capabilities and test evidence, and
any remaining security/patent/legal review. Review real application normalization
commands and representative legally obtained phone media in the later application
gate; synthetic HDR smoke tests are not that contract. Run a reviewed clean build
and ideally an independent rebuild on a second ARM64 host. Check size, binary
hashes and archive hashes, and resolve any unexplained differences.

Only after approval: create the exact reviewed version tag (for example v1.0.0),
then a GitHub Release with runtime archive, checksums, complete required source,
notices and audit evidence. Enable/use GitHub's immutable-release protection if
available and verify its behavior; a versioned filename alone does not make an
asset immutable. Never replace assets under an existing version. Fixes require a
new reviewed version. Store the expected SHA-256 independently in the consuming
application's reviewed lock/configuration. Do not rely solely on a checksum
fetched beside a possibly substituted archive.

| Mechanism | Determinism and integrity | Assessment |
| --- | --- | --- |
| A. Exact GitHub Release asset URL plus SHA-256 checked install/build step | Version and archive SHA-256 are committed in the consumer. Download at image/build time, verify before unpacking/execution; reject unsafe paths and install atomically. No runtime package installation. | Recommended for two standalone executables: small, explicit and independently auditable. No dependency on `latest`, redirects to a mutable version, or runtime `apt-get`. A versioned URL still needs the independently pinned hash. |
| B. Composer `package` repository with exact `dist` URL/version | Composer metadata/lock can identify the exact archive, but does not replace independent SHA-256 verification. A reviewed install/build step is still required; do not mistake legacy `dist.shasum` handling for the required SHA-256 policy. | Possible, but adds Composer packaging/installer behavior without simplifying binary provenance. No Packagist needed or proposed. Do not add an unreviewed Composer plugin merely to unpack binaries. |
| C. OCI artifact or a build-image layer pinned by digest | Content digest pins bytes; an application image build can copy verified binaries from a controlled artifact/image. Preserve corresponding source and notices. | Useful if the application later has a controlled OCI build path; adds registry and lifecycle infrastructure, so not justified for Gate 1 and not created here. |

Recommendation: A, performed during the application's deployment build and
committed as exact version + URL + SHA-256. Keep runtime instances free of mutable
downloads and package-manager installs. Execution-path configuration and any
Laravel integration are explicitly deferred.

For updates, create a separate PR: verify authoritative version/tag/commit,
inspect source changes (including configure scripts/license changes), verify
available signatures using reviewed keys, calculate source hashes, and update
all affected package pins and full transitive closure. Retrieve an immutable
ARM64 base digest if changing the base. Review Alpine recipe commits and patches
for static runtime changes. Never auto-accept a changed upstream archive under
the same version. Rerun script validation, two clean compiles, all capabilities,
fixtures and linkage/license audit. Record new evidence and require human review.
GitHub action updates similarly require a verified full commit pin.
