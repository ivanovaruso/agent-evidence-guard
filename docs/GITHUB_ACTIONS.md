# GitHub Actions integration

Agent Evidence Guard can be consumed directly as a reusable GitHub Action. It emits a human-readable GitHub Actions step summary and a machine-readable JSON verdict without changing the provider-neutral deterministic core.

**Release availability:** `v0.2.0` is published on [GitHub](https://github.com/ivanovaruso/agent-evidence-guard/releases/tag/v0.2.0) and [PyPI](https://pypi.org/project/agent-evidence-guard/0.2.0/). The older `v0.1.1` release does **not** include the strict JSON or atomic-verdict protections. Consumers upgrading should handle `ERROR` / exit 64.

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
        uses: ivanovaruso/agent-evidence-guard@v0.2.0
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

For higher-assurance workflows, pin this Action to the released commit `cd29448102cfd3e514a2ddd9ab09d01f5dfd36a3` according to your organization's supply-chain policy rather than relying only on a mutable version tag.

## CLI integration from PyPI

Install the public distribution:

```bash
python -m pip install agent-evidence-guard==0.2.0
```

Then run:

```bash
agent-evidence-guard-github evidence.json --json-output guard-verdict.json
```

## Exit codes

- `0` — `ALLOW`
- `2` — `BLOCK`
- `64` — invalid input

A `BLOCK` result intentionally fails the step unless the enclosing workflow explicitly chooses different control flow.

## Verdict artifact consistency

The GitHub adapter publishes the JSON verdict using a same-directory temporary file, `fsync`, and `os.replace` where supported. Existing output verdict files are invalidated **before** the input is evaluated. If the guard cannot publish a new verdict or a later summary write fails, it exits `64` and attempts to write an `ERROR` verdict; on irrecoverable failure the JSON file may be absent. Directories, symlinks, and device files are not supported JSON output destinations.

**Consume the final step result and the workflow run identity**, not an artifact containing `ALLOW` on its own. The human GitHub step summary is not transactional with the JSON file and may contain a partial or earlier line if an I/O failure occurs. The Action's `0`, `2`, and `64` exit codes are the final signals for that invocation.

- Treat `input`, `json-output`, `--summary-file`, and `GITHUB_STEP_SUMMARY` paths as **trusted workflow configuration**. Do not supply arbitrary untrusted filesystem destinations. Output aliases to the input and direct aliases between output paths that remain after prior JSON invalidation are rejected. **Hardlink nuance:** if the JSON verdict and Markdown summary were already hardlinks to the same inode, unlinking the old JSON can break that link *before* alias checks, and both destinations can then be written independently. Do not rely on hardlink identity between outputs; choose separate trusted paths from the outset.
- Use a **unique destination per run and step**. Do not run multiple Guard instances concurrently against the same output path.
- When using `if: always()` to upload the verdict, the upload is only a diagnostic artifact. It must not grant permission for a failed Guard step or be reused as a fresh verdict by a later run.
- `ALLOW` means only that **declared** evidence satisfied the contract; it is not independent verification of CI results or authority.

## Authority boundary

An `ALLOW` verdict means only that the declared evidence contract passed. It does **not** authorize merge, release, deployment, spending, production access, or any other state-changing action.

## Provider neutrality

The adapter does not call Claude, Codex, OpenAI, Anthropic, or any other model/provider. Any coding or review agent can produce evidence for the same deterministic contract.
