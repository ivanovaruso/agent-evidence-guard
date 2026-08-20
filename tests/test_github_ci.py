import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_evidence_guard.github_ci import run


class GitHubCIAdapterTests(unittest.TestCase):
    def _write_payload(self, directory: Path, payload: dict) -> Path:
        path = directory / "input.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_allow_writes_summary_and_json_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = self._write_payload(
                root,
                {
                    "claim": "implementation complete",
                    "authority_ref": "ISSUE-2",
                    "required_evidence": ["tests", "diff"],
                    "evidence": {"tests": "7 passed", "diff": "commit abc"},
                    "prohibited_claims": ["production deployed"],
                },
            )
            summary = root / "summary.md"
            artifact = root / "verdict.json"

            code = run(input_path, summary_file=summary, json_output=artifact)

            self.assertEqual(code, 0)
            self.assertIn("`ALLOW`", summary.read_text(encoding="utf-8"))
            self.assertEqual(json.loads(artifact.read_text(encoding="utf-8"))["decision"], "ALLOW")

    def test_block_preserves_fail_closed_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = self._write_payload(
                root,
                {
                    "claim": "implementation complete",
                    "authority_ref": "ISSUE-2",
                    "required_evidence": ["tests"],
                    "evidence": {},
                    "prohibited_claims": [],
                },
            )
            summary = root / "summary.md"

            code = run(input_path, summary_file=summary)

            self.assertEqual(code, 2)
            self.assertIn("missing_evidence:tests", summary.read_text(encoding="utf-8"))

    def test_uses_github_step_summary_when_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = self._write_payload(
                root,
                {
                    "claim": "done",
                    "authority_ref": "ISSUE-2",
                    "required_evidence": [],
                    "evidence": {},
                    "prohibited_claims": [],
                },
            )
            github_summary = root / "github-summary.md"

            with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(github_summary)}):
                code = run(input_path)

            self.assertEqual(code, 0)
            self.assertIn("Agent Evidence Guard", github_summary.read_text(encoding="utf-8"))

    def test_invalid_json_returns_64_and_error_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "bad.json"
            input_path.write_text("{bad json", encoding="utf-8")
            artifact = root / "verdict.json"

            code = run(input_path, json_output=artifact)

            self.assertEqual(code, 64)
            self.assertEqual(json.loads(artifact.read_text(encoding="utf-8"))["decision"], "ERROR")


if __name__ == "__main__":
    unittest.main()
