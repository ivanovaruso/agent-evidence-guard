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

**Currently published distribution: 0.1.1.** The strengthened behavior described later in this README belongs to the source candidate **0.2.0** and is **not available in the 0.1.1 PyPI package or v0.1.1 Action tag** until a separate 0.2.0 release is approved and published. See [0.2.0 release candidate notes](docs/RELEASE_0.2.0_CANDIDATE.md).

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

The versioned JSON Schema for this contract is available at [`schemas/input-v1.schema.json`](schemas/input-v1.schema.json). The core now rejects structurally invalid contract values at runtime using only the Python standard library; unknown top-level fields, invalid field types and duplicate evidence names produce `ERROR` (exit 64). Missing or empty claim and authority references retain `BLOCK` (exit 2) for compatibility with existing consumers. A separate JSON Schema validator is optional.

`agent-evidence-guard --help` and `agent-evidence-guard --version` are supported.

CLI JSON parsing rejects duplicate object keys (including nested duplicates), nonstandard values `NaN`/`Infinity`, finite-number overflow, and overly nested JSON with `ERROR` / exit 64. The composite Action treats a filename starting with `-` (for example `--help`) as a literal path, not a command-line option. Use **trusted workflow configuration** for verdict and summary output paths; the two output files are not a transactional unit. IO failures produce an error exit rather than claiming success on stdout.


**Artifact publication:** The GitHub CI adapter writes a machine-readable verdict through a same-directory temporary file and atomic replacement where the filesystem supports it, after flushing and syncing the temporary file. An existing verdict at the configured output path is removed at the start of each invocation to reduce stale `ALLOW` artifacts. Existing symlinks, directories, and special-file destinations are rejected. A file may be absent after an unrecoverable I/O error; consumers **must check the final step exit status** and the originating workflow run, not an artifact or GitHub step summary in isolation. JSON and Markdown summary updates are not a multi-file transaction. Use a unique, trusted output path per invocation.

**Security and trust limit:** `ALLOW` checks only the declared contract. A text value such as `"tests": "9999 passed"` is not proof that CI ran; an `authority_ref` value is not independently authenticated. The guard never authorizes merge, release, deployment or access.

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
