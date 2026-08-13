import json
import unittest
from pathlib import Path


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "input-v1.schema.json"


class InputSchemaContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_schema_is_draft_2020_12(self):
        self.assertEqual(
            self.schema["$schema"],
            "https://json-schema.org/draft/2020-12/schema",
        )

    def test_schema_is_fail_closed_on_unknown_top_level_fields(self):
        self.assertFalse(self.schema["additionalProperties"])

    def test_required_contract_fields_are_explicit(self):
        self.assertEqual(
            set(self.schema["required"]),
            {"claim", "authority_ref", "required_evidence", "evidence"},
        )

    def test_claim_and_authority_cannot_be_empty(self):
        self.assertEqual(self.schema["properties"]["claim"]["minLength"], 1)
        self.assertEqual(self.schema["properties"]["authority_ref"]["minLength"], 1)

    def test_required_evidence_keys_are_unique(self):
        self.assertTrue(self.schema["properties"]["required_evidence"]["uniqueItems"])


if __name__ == "__main__":
    unittest.main()
