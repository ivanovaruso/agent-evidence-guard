"""GitHub Actions output adapter for declarative evidence contracts.

The machine verdict file is published by same-directory atomic replacement where
supported. Workflow-run exit status, not the human summary alone, is definitive.
"""

import os
import stat
import tempfile
from pathlib import Path
from typing import Any

from .core import Verdict, evaluate
from .json_contract import UsageParser, load_strict_json, render_json


def render_summary(verdict: Verdict, input_path: str) -> str:
    """Render a concise GitHub Actions step summary."""
    lines = [
        "## Agent Evidence Guard",
        "",
        f"- **Decision:** `{verdict.decision}`",
        f"- **Input:** `{input_path}`",
    ]
    if verdict.reasons:
        lines.extend(["", "### Reasons"])
        lines.extend(f"- `{reason}`" for reason in verdict.reasons)
    else:
        lines.extend(["", "All declared evidence contract checks passed (external facts not verified)."])
    lines.extend([
        "",
        "> This verdict validates the declared evidence contract only. "
        "It does not grant merge, deployment, release, spending, or production authority.",
        "",
    ])
    return "\n".join(lines)


def _validate_output_destination(path: Path) -> None:
    """Existing outputs must be regular files, not directories/devices/symlinks."""
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return
    if not stat.S_ISREG(mode):
        raise ValueError(f"output destination must be a regular file: {path}")


def _remove_old_verdict(path: Path) -> None:
    """Fail closed rather than leave an earlier ALLOW for a new invocation."""
    _validate_output_destination(path)
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _write_json(path: Path, value: dict[str, Any]) -> None:
    """Write and fsync a temp file, then atomically replace within one directory."""
    rendered = render_json(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    _validate_output_destination(path)
    fd, name = tempfile.mkstemp(prefix=".aeg-verdict-", suffix=".tmp", dir=path.parent)
    temp_path = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def _write_summary(path: Path, summary: str, append: bool) -> None:
    _validate_output_destination(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as handle:
        handle.write(summary)


def _same_destination(a: Path, b: Path) -> bool:
    """Detect identical paths, symlink aliases and existing hardlinks."""
    try:
        if a.resolve() == b.resolve():
            return True
    except RuntimeError:
        # Python 3.10-3.12 may raise RuntimeError for circular symlinks.
        # Such paths are unusable: input opening or output lstat will reject
        # them below. Do not leak an uncaught traceback during alias checks.
        pass
    try:
        return a.samefile(b)
    except (OSError, RuntimeError):
        return False


def _reject_aliases(input_path: Path, json_output: Path | None, summary_target: Path | None) -> None:
    """Keep output configuration from overwriting the input or each other."""
    if json_output is not None and _same_destination(json_output, input_path):
        raise ValueError("JSON output must not overwrite the input contract")
    if summary_target is not None and _same_destination(summary_target, input_path):
        raise ValueError("summary must not overwrite the input contract")
    if json_output is not None and summary_target is not None and _same_destination(json_output, summary_target):
        raise ValueError("JSON verdict and Markdown summary must use different paths")


def run(input_path: Path, summary_file: Path | None = None, json_output: Path | None = None) -> int:
    artifact_ready = False
    try:
        github_summary = os.environ.get("GITHUB_STEP_SUMMARY")
        summary_target = summary_file or (Path(github_summary) if github_summary else None)
        # Protect the input contract *before* invalidating any output. All
        # other configuration errors must be checked *after* the previous
        # machine verdict has been removed, so an old ALLOW cannot survive.
        if json_output is not None and _same_destination(json_output, input_path):
            raise ValueError("JSON output must not overwrite the input contract")
        if json_output is not None:
            _remove_old_verdict(json_output)
            artifact_ready = True
        _reject_aliases(input_path, json_output, summary_target)
        if summary_target is not None:
            _validate_output_destination(summary_target)

        payload = load_strict_json(input_path)
        if not isinstance(payload, dict):
            raise ValueError("input JSON must be an object")
        verdict = evaluate(payload)
        result = verdict.to_dict()
        rendered_result = render_json(result)

        # JSON publication precedes the human summary. If the summary fails,
        # replace the JSON verdict with ERROR (or remove it, failing closed).
        if json_output is not None:
            _write_json(json_output, result)
        if summary_target is not None:
            _write_summary(
                summary_target, render_summary(verdict, str(input_path)),
                append=summary_file is None and github_summary is not None,
            )
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        error = {"decision": "ERROR", "reason": str(exc)}
        if json_output is not None and artifact_ready:
            try:
                _write_json(json_output, error)
            except (OSError, UnicodeError, ValueError, RecursionError):
                try:
                    _remove_old_verdict(json_output)
                except (OSError, ValueError):
                    pass  # If destination cannot be cleaned, exit 64 still applies.
        print(render_json(error), end="")
        return 64

    print(rendered_result, end="")
    return {"ALLOW": 0, "BLOCK": 2, "ERROR": 64}[verdict.decision]


def main() -> None:
    parser = UsageParser(
        prog="agent-evidence-guard-github",
        description="Evaluate a declared evidence contract and emit GitHub Actions-friendly output.",
    )
    parser.add_argument("input", type=Path, help="Path to the evidence-contract JSON file")
    parser.add_argument("--summary-file", type=Path, help="Optional Markdown summary path; defaults to GITHUB_STEP_SUMMARY inside Actions")
    parser.add_argument("--json-output", type=Path, help="Optional path for a machine-readable verdict")
    args = parser.parse_args()
    raise SystemExit(run(args.input, args.summary_file, args.json_output))


if __name__ == "__main__":
    main()
