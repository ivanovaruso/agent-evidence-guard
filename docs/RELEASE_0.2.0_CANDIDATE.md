# Agent Evidence Guard 0.2.0 — release candidate (NOT PUBLISHED)

**Status:** candidate in source control. This document is not a GitHub Release, a PyPI upload, a Marketplace listing, or permission to create any of those artifacts.

**Current public installation:** v0.1.1 remains the released PyPI package and GitHub Action tag. Do not substitute `v0.2.0` in a downstream `uses:` declaration, or recommend `pip install agent-evidence-guard==0.2.0` as published, before publication has actually been verified.

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
5. **Update references only after publication.** The existing `v0.1.1` Action and PyPI wheel remain the released behavior until a separately authorized `v0.2.0` release exists. Pin to a verified commit SHA for high-assurance Action consumers.

## Candidate verification checklist

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

**Stop condition:** Do not create a tag or publish a GitHub Release as a candidate smoke test; doing so could invoke the production PyPI publishing workflow. This document alone does not authorize release.

## Unchanged authority boundary

`ALLOW` validates the **declared** evidence contract only. It does not authenticate tests, commit signatures, PR state, identity, approval, deployment status, spending or production permissions. `WORKER != EVIDENCE GUARD != MERGE AUTHORITY`.
