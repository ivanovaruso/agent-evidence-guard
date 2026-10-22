# Changelog

All notable changes to this project will be documented here.

## [Unreleased]

### Security and correctness
- Reject malformed and unexpected contract data at runtime; preserve the existing `BLOCK` decisions for missing or empty claims and authority references.
- Return `ERROR` / exit 64 for structurally invalid inputs in both CLIs.
- Pass composite Action inputs through environment variables and load the Action's own Python package with isolated interpreter startup.
- Normalize repeated whitespace and case when checking prohibited phrases; this does not make string matching a semantic security policy.
- Add negative and local composite-action regression tests for shell injection and repository package shadowing.
- Support `--help` and `--version` in the primary CLI.
- Clarify that declared evidence is not independently verified.
- Reject duplicate JSON keys, NaN/Infinity, overflowing float literals, and excessive nesting in both CLIs.
- Prevent composite Action `input: --help` from bypassing evaluation; treat untrusted input as a literal filename.
- Normalize adapter argument errors to exit 64; handle invalid output targets without emitting an ALLOW success response.
- Add reviewer F1–F5 regressions and live GitHub runner checks, including Python 3.10–3.13 compatibility.
- Publish verdict JSON via same-directory atomic replacement; invalidate previous verdict on each invocation and prefer an ERROR artifact on write failures.
- Reject symlink, special-file and aliasing output paths; document non-transactional summary output and final-step status requirements.
- Add issue #20 regressions for failed sync/replace, stale verdicts, summary failures and reused paths.

## [0.1.1] - 2026-08-20

### Added
- reusable root GitHub Action for downstream repositories
- GitHub Action self-smoke validation
- secure PyPI Trusted Publishing workflow using GitHub OIDC
- package build, metadata, wheel-install, and CLI smoke validation in CI
- publishing security documentation and CODEOWNERS coverage

### Changed
- modernized Python package license metadata to SPDX `Apache-2.0`
- made Python package discovery explicit so repository-only `skills/` and `schemas/` content is not treated as importable packages
- expanded distribution metadata and project links

## [0.1.0] - 2026-08-20

### Added
- deterministic ALLOW/BLOCK evidence guard
- CLI
- versioned Draft 2020-12 JSON Schema for the input contract
- GitHub Actions adapter with step-summary and JSON-artifact output
- unit tests for core, schema-contract, and GitHub CI adapter behavior
- GitHub Actions CI
- Apache-2.0 licensing and contributor/security documentation
- portable `SKILL.md`
