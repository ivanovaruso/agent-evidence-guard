# Agent Evidence Guard 0.2.0 — release and upgrade record

**Status (2026-10-22): PUBLISHED.** [GitHub Release v0.2.0](https://github.com/ivanovaruso/agent-evidence-guard/releases/tag/v0.2.0) and [PyPI 0.2.0](https://pypi.org/project/agent-evidence-guard/0.2.0/) were published from commit `cd29448102cfd3e514a2ddd9ab09d01f5dfd36a3`; the release workflow completed with Trusted Publishing. This document retains the historical pre-publication safety checklist below for audit context.

**Current public installation:** PyPI `agent-evidence-guard==0.2.0` and GitHub Action `@v0.2.0` are available. `v0.1.1` remains a historical version and does not include the hardening described here.

## Purpose and version choice

0.2.0 (rather than 0.1.2) signals an intentional behavior change from 0.1.1 in the handling of invalid input and command-line exit codes. The underlying declared-evidence authority boundary and supported Python floor (3.10) remain unchanged. It is still early-stage OSS, Apache-2.0, with no external runtime dependencies.

## Included since v0.1.1

- Fail-closed structural checks for unexpected fields, wrong field types, duplicate evidence selectors and malformed JSON; duplicate JSON object keys, `NaN`/`Infinity`, nonfinite float overflow and extreme nesting are rejected.
- Consistent `ALLOW/0`, `BLOCK/2`, `ERROR/64` behavior for both CLIs, including usage and output errors; primary CLI gains `--help`/`--version`.
- Composite GitHub Action isolates Python imports from the caller checkout, treats option-looking input paths literally, and avoids direct shell-expression interpolation.
- GitHub adapter writes each verdict via a same-directory temporary file, flush, `fsync` and `os.replace` where supported. Previous output is invalidated before a new evaluation, and output aliases/symlinks/special files are handled conservatively.
- Recovery and adversarial tests, Python 3.10/3.12/3.13 CI matrix, distribution build/installation smoke tests, and a repaired older Action smoke workflow.
- Documentation now explains the hardlink nuance between prior JSON and Markdown output paths (tracked separately as issue #22).

## Upgrade guidance for 0.1.1 consumers

1. **Check error codes.** Consumers that assume all nonzero exit codes are 2 must handle 64 for invalid contracts, malformed data, arguments or output failures.
2. **Provide schema-shaped evidence.** Unknown top-level keys, malformed values and duplicated JSON keys are not accepted. A nonempty-looking evidence string is *not* independent proof that a check ran.
3. **Treat paths as trusted.** Verdict and summary output paths must be separate, trustworthy, and unique to the invocation. Never share the same output path across simultaneous runs.
4. **Use the final step status.** An `ALLOW` artifact or human summary is not an authorization, and JSON/Markdown are not an atomic multi-file transaction. A failed step may leave an ERROR artifact or no artifact.
5. **Update verified references.** `v0.2.0` is now the published release. Pin to the verified release commit SHA `cd29448102cfd3e514a2ddd9ab09d01f5dfd36a3` for high-assurance Action consumers.

## Historical pre-publication verification checklist

- [ ] Exact PR head and `main` base SHA inspected before any decision.
- [ ] All unit/adversarial tests pass on Python 3.10, 3.12, and 3.13.
- [ ] Build wheel + sdist from the proposed source, validate metadata with `twine check`, install the built wheel and confirm *installed* package version == `0.2.0`.
- [ ] Verify the `agent-evidence-guard --version` command reports 0.2.0, and ALLOW/0, BLOCK/2, ERROR/64 paths still behave correctly.
- [ ] Download the CI **candidate** artifact, inspect package filenames and SHA-256 digest; note a PR workflow checks out GitHub's synthetic merge commit, so hashes are tied to the actual build run and checked-out revision.
- [ ] Reviewer independently checks release metadata, CLI behavior and publishing safety. Green CI is insufficient by itself.
- [ ] After an authorized merge, rerun all checks on the final `main` commit and inspect the artifact from that run.
- [ ] Obtain **separate explicit approval** before tag creation, published GitHub Release, PyPI upload or marketplace listing.
- [ ] Confirm `v0.2.0` and PyPI 0.2.0 do not already exist before any release operation; never overwrite a published artifact.
- [ ] Confirm PyPI trusted-publisher environment permissions and release automation ownership. This repository's `.github/workflows/release.yml` triggers when a **GitHub Release is published** and can automatically upload to PyPI.
- [ ] Once the release actually exists and PyPI install is tested, update README/consumer examples from `0.1.1`/`v0.1.1` to the verified new release and date the changelog entry in a separately reviewed change.

**Historical stop condition (satisfied after explicit owner approval):** Publishing a GitHub Release invokes the production PyPI workflow. The approved `v0.2.0` publication has completed; do not recreate the tag, republish this immutable PyPI version, or treat a candidate smoke test as a reason to publish again.

## Unchanged authority boundary

`ALLOW` validates the **declared** evidence contract only. It does not authenticate tests, commit signatures, PR state, identity, approval, deployment status, spending or production permissions. `WORKER != EVIDENCE GUARD != MERGE AUTHORITY`.
