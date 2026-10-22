"""Safe command-line entry point for the declarative evidence guard."""

import json
from pathlib import Path

from . import __version__
from .core import evaluate
from .json_contract import UsageParser, load_strict_json, render_json


def main() -> None:
    parser = UsageParser(prog="agent-evidence-guard", description="Check a declared evidence contract (does not verify external facts).")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("input", type=Path, help="Path to the input JSON contract")
    args = parser.parse_args()

    try:
        payload = load_strict_json(args.input)
        verdict = evaluate(payload)
        result = render_json(verdict.to_dict())
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        print(render_json({"decision": "ERROR", "reason": str(exc)}), end="")
        raise SystemExit(64)

    print(result, end="")
    raise SystemExit({"ALLOW": 0, "BLOCK": 2, "ERROR": 64}[verdict.decision])


if __name__ == "__main__":
    main()
