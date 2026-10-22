"""Validate declared agent evidence contracts without granting effect authority.

This is a *declarative* guard. An ALLOW does not independently verify
external evidence, authenticate an authority reference, or permit a merge.
"""

import re
from dataclasses import asdict, dataclass
from typing import Any


_REQUIRED = frozenset({"claim", "authority_ref", "required_evidence", "evidence"})
_ALLOWED = _REQUIRED | {"prohibited_claims"}


@dataclass(frozen=True)
class Verdict:
    decision: str
    reasons: list[str]
    admitted_evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _valid_string_list(value: Any) -> bool:
    if not isinstance(value, list):
        return False
    if any(not isinstance(item, str) or not item for item in value):
        return False
    return len(value) == len(set(value))


def _contract_errors(payload: Any) -> list[str]:
    """Enforce the published input-v1 JSON Schema's structural contract.

    The schema is kept as a public standalone artifact; runtime validation
    uses the Python standard library rather than a network/runtime dependency.
    """
    if not isinstance(payload, dict):
        return ["invalid_input:root_must_be_object"]

    if any(not isinstance(key, str) for key in payload):
        return ["invalid_input:top_level_keys_must_be_strings"]

    problems = []
    for field in sorted({"required_evidence", "evidence"} - payload.keys()):
        problems.append(f"invalid_input:missing_field:{field}")
    for field in sorted(payload.keys() - _ALLOWED):
        problems.append(f"invalid_input:unknown_field:{field}")

    for field in ("claim", "authority_ref"):
        if field in payload:
            val = payload[field]
            if not isinstance(val, str):
                problems.append(f"invalid_input:{field}_must_be_nonempty_string")

    for field in ("required_evidence", "prohibited_claims"):
        if field in payload and not _valid_string_list(payload[field]):
            problems.append(f"invalid_input:{field}_must_be_unique_string_list")

    if "evidence" in payload and (not isinstance(payload["evidence"], dict) or any(not isinstance(k, str) for k in payload["evidence"])):
        problems.append("invalid_input:evidence_must_be_object")
    return problems


def _normalize_phrase(value: str) -> str:
    """Handle case and repeated whitespace, not arbitrary paraphrases."""
    return re.sub(r"\s+", " ", value.casefold()).strip()


def evaluate(payload: Any) -> Verdict:
    errors = _contract_errors(payload)
    if errors:
        return Verdict("ERROR", errors, {})

    # Type invariants are already checked by _contract_errors.
    reasons: list[str] = []
    evidence = payload["evidence"]
    if not payload.get("claim", "").strip():
        reasons.append("missing_claim")
    if not payload.get("authority_ref", "").strip():
        reasons.append("missing_authority_ref")
    for name in payload["required_evidence"]:
        if not evidence.get(name):
            reasons.append(f"missing_evidence:{name}")

    normalized_claim = _normalize_phrase(payload.get("claim", ""))
    for phrase in payload.get("prohibited_claims", []):
        if (needle := _normalize_phrase(phrase)) and needle in normalized_claim:
            reasons.append(f"prohibited_claim:{needle}")

    return Verdict("BLOCK" if reasons else "ALLOW", reasons, {} if reasons else evidence)
