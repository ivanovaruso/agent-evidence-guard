# GitHub Actions integration

Agent Evidence Guard can emit both a human-readable GitHub Actions step summary and a machine-readable JSON verdict without changing the provider-neutral deterministic core.

## Example

Assume your workflow or previous step creates `evidence.json`.

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

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install Agent Evidence Guard
        run: python -m pip install .

      - name: Validate completion evidence
        run: |
          agent-evidence-guard-github evidence.json \
            --json-output guard-verdict.json

      - name: Upload verdict artifact
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: agent-evidence-guard-verdict
          path: guard-verdict.json
```

Inside GitHub Actions, the adapter detects `GITHUB_STEP_SUMMARY` and appends a concise verdict automatically.

## Exit codes

- `0` — `ALLOW`
- `2` — `BLOCK`
- `64` — invalid input

A `BLOCK` result intentionally fails the step unless the enclosing workflow explicitly chooses different control flow.

## Authority boundary

An `ALLOW` verdict means only that the declared evidence contract passed. It does **not** authorize merge, release, deployment, spending, production access, or any other state-changing action.

## Provider neutrality

The adapter does not call Claude, Codex, OpenAI, Anthropic, or any other model/provider. Any coding or review agent can produce evidence for the same deterministic contract.
