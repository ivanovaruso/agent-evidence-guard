# Changelog

All notable changes to this project will be documented here.

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
