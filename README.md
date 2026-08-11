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

## Quick start

Requires Python 3.10+ and no third-party runtime dependencies.

```bash
python -m agent_evidence_guard.cli examples/supported.json
python -m agent_evidence_guard.cli examples/unsupported.json
```

Exit codes:

- `0` — ALLOW
- `2` — BLOCK
- `64` — invalid input

Run tests:

```bash
python -m unittest discover -s tests -v
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
