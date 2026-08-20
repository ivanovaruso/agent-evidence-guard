# Maintainer workflow with coding agents

Agent Evidence Guard is designed to sit between an AI coding/review worker and the point where a repository accepts a completion claim.

The worker may be Claude Code, Codex, GitHub Copilot, another coding agent, or a human contributor. The guard does not call or depend on any of them.

## Example flow

```text
Issue / maintenance task
        ↓
Coding or review worker
        ↓
Pull request + tests + evidence.json
        ↓
Agent Evidence Guard
        ↓
ALLOW / BLOCK evidence claim
        ↓
Independent maintainer review
        ↓
merge / rework / reject
```

The guard validates the declared evidence contract only. It never grants merge, release, deployment, spending, or production authority.

## Example evidence contract

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

A coding agent can produce the PR and supporting evidence, but the repository decides what evidence is required. Agent Evidence Guard then checks the contract deterministically.

## GitHub Actions boundary

A repository can run the reusable Action on a pull request:

```yaml
- name: Validate agent evidence
  uses: ivanovaruso/agent-evidence-guard@v0.1.0
  with:
    input: evidence.json
```

A non-zero result blocks that workflow step. A zero result means only that the declared evidence requirements passed.

## Why this separation matters

A coding agent is good at generating or reviewing changes. A deterministic guard is good at checking explicit, machine-readable conditions. A maintainer remains responsible for deciding whether the change should actually be accepted.

This keeps the roles separate:

```text
WORKER != EVIDENCE GUARD != MERGE AUTHORITY
```

## Provider neutrality

No model account, API key, MCP server, or agent framework is required by the guard itself. Teams can change coding agents without changing the evidence contract or the deterministic acceptance layer.
