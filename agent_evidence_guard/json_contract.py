"""Strict JSON boundary for public CLI inputs and machine-readable verdicts.

Evidence validity is structural only. No external attestations are performed.
"""

import argparse
import json
import math
from pathlib import Path
from typing import Any


class UsageParser(argparse.ArgumentParser):
    """Use exit 64 consistently for argument/usage errors."""

    def error(self, message: str) -> None:
        self.print_usage()
        self.exit(64, f"{self.prog}: error: {message}\n")


def _reject_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant: {value}")


def _parse_finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError("non-finite JSON number")
    return parsed


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def load_strict_json(path: Path) -> Any:
    """Reject nonstandard constants, overflow, duplicate keys and invalid nesting."""
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_constant,
            parse_float=_parse_finite_float,
            object_pairs_hook=_unique_object,
        )
    except RecursionError as exc:
        raise ValueError("JSON input exceeds supported nesting depth") from exc


def render_json(value: Any) -> str:
    try:
        return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    except (RecursionError, OverflowError, TypeError, ValueError) as exc:
        raise ValueError(f"cannot serialize valid JSON: {exc}") from exc
