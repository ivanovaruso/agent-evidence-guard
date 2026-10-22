"""GitHub Actions output adapter for declarative evidence contracts."""

import json
import os
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


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_json(value), encoding="utf-8")


def _write_summary(path: Path, summary: str, append: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as handle:
        handle.write(summary)


def _validate_output_destination(path: Path) -> None:
    """Reject directory output paths before printing or writing an ALLOW."""
    if path.is_dir():
        raise IsADirectoryError(f"output destination is a directory: {path}")


def run(input_path: Path, summary_file: Path | None = None, json_output: Path | None = None) -> int:
    try:
        payload = load_strict_json(input_path)
        if not isinstance(payload, dict):
            raise ValueError("input JSON must be an object")
        verdict = evaluate(payload)
        result = verdict.to_dict()
        rendered_result = render_json(result)  # Serialize *before* any output side effects.
        github_summary = os.environ.get("GITHUB_STEP_SUMMARY")
        summary_target = summary_file or (Path(github_summary) if github_summary else None)
        if summary_target is not None:
            _validate_output_destination(summary_target)
        if json_output is not None:
            _validate_output_destination(json_output)

        # The summary is written first. If it fails, no ALLOW artifact is created.
        # Multi-file transactional guarantees are not available for caller-controlled paths.
        if summary_target is not None:
            _write_summary(
                summary_target, render_summary(verdict, str(input_path)),
                append=summary_file is None and github_summary is not None,
            )
        if json_output is not None:
            _write_json(json_output, result)
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        error = {"decision": "ERROR", "reason": str(exc)}
        if json_output is not None:
            try:
                _write_json(json_output, error)
            except (OSError, UnicodeError, ValueError, RecursionError):
                pass  # No valid artifact destination; step still fails closed.
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
