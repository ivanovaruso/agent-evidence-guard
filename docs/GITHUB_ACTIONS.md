# GitHub Actions integration

Agent Evidence Guard can be consumed directly as a reusable GitHub Action. It emits a human-readable GitHub Actions step summary and a machine-readable JSON verdict without changing the provider-neutral deterministic core.

## Fastest downstream integration

Assume your workflow or a previous step creates `evidence.json`.

```yaml
name: evidence-guard

on:
  pull_request:

permissions:
  contents: read

jobs:
  guard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate completion evidence
        uses: ivanovaruso/agent-evidence-guard@v0.1.0
        with:
          input: evidence.json
          json-output: guard-verdict.json

      - name: Upload verdict artifact
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: agent-evidence-guard-verdict
          path: guard-verdict.json
```

The reusable Action executes the repository's deterministic GitHub adapter and automatically writes to `GITHUB_STEP_SUMMARY` when that environment variable is available.

For higher-assurance workflows, pin third-party Actions to a full commit SHA according to your organization's supply-chain policy rather than relying only on a mutable version tag.

## CLI integration

If you prefer to install the package in a Python workflow rather than use the composite Action:

```bash
agent-evidence-guard-github evidence.json --json-output guard-verdict.json
```

## Exit codes

- `0` — `ALLOW`
- `2` — `BLOCK`
- `64` — invalid input

A `BLOCK` result intentionally fails the step unless the enclosing workflow explicitly chooses different control flow.

## Authority boundary

An `ALLOW` verdict means only that the declared evidence contract passed. It does **not** authorize merge, release, deployment, spending, production access, or any other state-changing action.

## Provider neutrality

The adapter does not call Claude, Codex, OpenAI, Anthropic, or any other model/provider. Any coding or review agent can produce evidence for the same deterministic contract.
