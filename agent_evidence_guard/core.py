from dataclasses import dataclass, asdict
from typing import Any

@dataclass(frozen=True)
class Verdict:
    decision: str
    reasons: list[str]
    admitted_evidence: dict[str, Any]
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def evaluate(payload: dict[str, Any]) -> Verdict:
    reasons: list[str] = []
    evidence = payload.get("evidence") or {}
    required = payload.get("required_evidence") or []
    authority_ref = payload.get("authority_ref")
    claim = str(payload.get("claim") or "").strip()
    prohibited = [str(x).strip().lower() for x in (payload.get("prohibited_claims") or [])]
    if not claim:
        reasons.append("missing_claim")
    if not authority_ref:
        reasons.append("missing_authority_ref")
    if not isinstance(evidence, dict):
        reasons.append("evidence_must_be_object")
        evidence = {}
    if not isinstance(required, list):
        reasons.append("required_evidence_must_be_list")
        required = []
    for name in [name for name in required if not evidence.get(name)]:
        reasons.append(f"missing_evidence:{name}")
    lower_claim = claim.lower()
    for phrase in prohibited:
        if phrase and phrase in lower_claim:
            reasons.append(f"prohibited_claim:{phrase}")
    return Verdict("ALLOW" if not reasons else "BLOCK", reasons, evidence if not reasons else {})
