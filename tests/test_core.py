import unittest
from agent_evidence_guard.core import evaluate

class EvaluateTests(unittest.TestCase):
    def test_allows_supported_claim(self):
        r = evaluate({"claim":"implementation complete","authority_ref":"ISSUE-1","required_evidence":["tests","diff"],"evidence":{"tests":"6 passed","diff":"commit abc"},"prohibited_claims":["production deployed"]})
        self.assertEqual(r.decision, "ALLOW")
    def test_blocks_missing_authority(self):
        r = evaluate({"claim":"done","required_evidence":[],"evidence":{}})
        self.assertEqual(r.decision, "BLOCK"); self.assertIn("missing_authority_ref", r.reasons)
    def test_blocks_missing_evidence(self):
        r = evaluate({"claim":"done","authority_ref":"ISSUE-1","required_evidence":["tests"],"evidence":{}})
        self.assertEqual(r.decision, "BLOCK"); self.assertIn("missing_evidence:tests", r.reasons)
    def test_blocks_prohibited_claim(self):
        r = evaluate({"claim":"production deployed successfully","authority_ref":"ISSUE-1","required_evidence":[],"evidence":{},"prohibited_claims":["production deployed"]})
        self.assertEqual(r.decision, "BLOCK")
    def test_blocks_empty_claim(self):
        r = evaluate({"claim":"","authority_ref":"ISSUE-1","required_evidence":[],"evidence":{}})
        self.assertEqual(r.decision, "BLOCK"); self.assertIn("missing_claim", r.reasons)
    def test_preserves_evidence_only_on_allow(self):
        r = evaluate({"claim":"done","authority_ref":"ISSUE-1","required_evidence":["tests"],"evidence":{"tests":"pass"}})
        self.assertEqual(r.admitted_evidence, {"tests":"pass"})

if __name__ == '__main__': unittest.main()
