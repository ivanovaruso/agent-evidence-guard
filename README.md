# Agent Evidence Guard

A small, deterministic guardrail for AI-agent completion claims.

AI coding and automation agents often say things like:

- "tests passed"
- "the fix is complete"
- "deployment succeeded"
- "the requested change is done"

Agent Evidence Guard checks whether a completion claim is backed by the evidence and authority the task contract requires.

## Why

The project is intentionally simple: **claims should not become accepted state without evidence**.

Example:

```text
Agent output
    ↓
Completion claim
    ↓
Agent Evidence Guard
    ├─ authority present?
    ├─ required evidence present?
    ├─ tests reported?
    └─ prohibited claims?
    ↓
ALLOW / BLOCK
```

## Install from PyPI

Requires Python 3.10+ and has no third-party runtime dependencies.

```bash
python -m pip install agent-evidence-guard==0.1.1
```

The public PyPI distribution has been clean-install verified on GitHub-hosted Python 3.12.

## Quick start

```bash
agent-evidence-guard examples/supported.json
agent-evidence-guard examples/unsupported.json
```

Exit codes:

- `0` — ALLOW
- `2` — BLOCK
- `64` — invalid input

For source development, run tests with:

```bash
python -m unittest discover -s tests -v
```

## Reusable GitHub Action

Another repository can consume the released Action directly:

```yaml
- name: Validate agent evidence
  uses: ivanovaruso/agent-evidence-guard@v0.1.1
  with:
    input: evidence.json
    json-output: guard-verdict.json
```

The Action writes a GitHub Actions step summary, emits a machine-readable verdict file, and preserves the fail-closed exit codes. It does not need an API key or model-provider account.

For higher-assurance workflows, pin the Action to the immutable release commit SHA rather than relying only on a mutable version tag.

## GitHub Actions CLI adapter

The underlying adapter can also be invoked directly:

```bash
agent-evidence-guard-github evidence.json --json-output guard-verdict.json
```

Inside GitHub Actions, the adapter automatically uses `GITHUB_STEP_SUMMARY` when available. See [`docs/GITHUB_ACTIONS.md`](docs/GITHUB_ACTIONS.md) for a complete workflow example.

The adapter is provider-neutral: it does not require Claude, Codex, OpenAI, Anthropic, or any other model provider.

## Maintainer workflow with coding agents

See [`docs/MAINTAINER_AGENT_WORKFLOW.md`](docs/MAINTAINER_AGENT_WORKFLOW.md) for a concrete provider-neutral flow showing how Claude Code, Codex, GitHub Copilot, another coding agent, or a human contributor can produce changes and evidence while Agent Evidence Guard remains a separate deterministic validation layer.

The key boundary is:

```text
WORKER != EVIDENCE GUARD != MERGE AUTHORITY
```

## Input contract

A JSON document contains:

```json
{
  "claim": "implementation complete",
  "authority_ref": "ISSUE-123",
  "required_evidence": ["tests", "diff"],
  "evidence": {
    "tests": "18 passed",
    "diff": "commit abc123"
  },
  "prohibited_claims": ["production deployed"]
}
```

The versioned JSON Schema for this contract is available at [`schemas/input-v1.schema.json`](schemas/input-v1.schema.json). The schema is intentionally strict at the top level so misspelled or unexpected contract fields fail validation in downstream tooling instead of being silently ignored.

The guard itself remains dependency-free: consumers may validate against the schema with any Draft 2020-12 compatible JSON Schema implementation, while the core evaluator continues to use only the Python standard library.

The guard does not decide whether the code is good. It decides whether the **claim is admissible given the declared contract**.

## Design principles

- deterministic by default
- zero external runtime dependencies
- fail closed
- evidence over narrative
- authority is explicit
- machine-readable result
- easy to embed in CI or agent workflows
- portable `SKILL.md` guidance included

## Project status

Early-stage, experimental OSS. The core policy is intentionally narrow so it can be reviewed, tested, and extended safely.

## License

Apache-2.0.
