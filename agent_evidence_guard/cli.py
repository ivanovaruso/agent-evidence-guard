"""Safe command-line entry point for the declarative evidence guard."""

import argparse
import json
from pathlib import Path

from . import __version__
from .core import evaluate


class _UsageParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_usage()
        self.exit(64, f"{self.prog}: error: {message}\n")


def main() -> None:
    parser = _UsageParser(prog="agent-evidence-guard", description="Check a declared evidence contract (does not verify external facts).")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("input", type=Path, help="Path to the input JSON contract")
    args = parser.parse_args()

    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(json.dumps({"decision": "ERROR", "reason": str(exc)}))
        raise SystemExit(64)

    verdict = evaluate(payload)
    print(json.dumps(verdict.to_dict(), indent=2, sort_keys=True))
    raise SystemExit({"ALLOW": 0, "BLOCK": 2, "ERROR": 64}[verdict.decision])


if __name__ == "__main__":
    main()
