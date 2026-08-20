import argparse
import json
import os
from pathlib import Path
from typing import Any

from .core import Verdict, evaluate


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
        lines.extend(["", "All required evidence and authority checks passed."])

    lines.extend(
        [
            "",
            "> This verdict validates the declared evidence contract only. "
            "It does not grant merge, deployment, release, spending, or production authority.",
            "",
        ]
    )
    return "\n".join(lines)


def _load_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("input JSON must be an object")
    return payload


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_summary(path: Path, summary: str, append: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as handle:
        handle.write(summary)


def run(input_path: Path, summary_file: Path | None = None, json_output: Path | None = None) -> int:
    try:
        payload = _load_payload(input_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = {"decision": "ERROR", "reason": str(exc)}
        print(json.dumps(result, indent=2, sort_keys=True))
        if json_output is not None:
            _write_json(json_output, result)
        return 64

    verdict = evaluate(payload)
    result = verdict.to_dict()
    print(json.dumps(result, indent=2, sort_keys=True))

    if json_output is not None:
        _write_json(json_output, result)

    github_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    target = summary_file or (Path(github_summary) if github_summary else None)
    if target is not None:
        _write_summary(
            target,
            render_summary(verdict, str(input_path)),
            append=summary_file is None and github_summary is not None,
        )

    return 0 if verdict.decision == "ALLOW" else 2


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agent-evidence-guard-github",
        description="Evaluate an evidence contract and emit GitHub Actions-friendly output.",
    )
    parser.add_argument("input", type=Path, help="Path to the evidence-contract JSON file")
    parser.add_argument(
        "--summary-file",
        type=Path,
        help="Optional Markdown summary path. Defaults to GITHUB_STEP_SUMMARY inside GitHub Actions.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional path for the machine-readable verdict artifact.",
    )
    args = parser.parse_args()
    raise SystemExit(run(args.input, args.summary_file, args.json_output))


if __name__ == "__main__":
    main()
