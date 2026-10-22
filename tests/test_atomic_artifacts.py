"""Issue #20: prevent partial/stale machine verdicts on output failures."""

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_evidence_guard.github_ci import run


VALID = {
    "claim": "done", "authority_ref": "ISSUE-20",
    "required_evidence": ["tests"], "evidence": {"tests": "pass"},
}


class AtomicArtifactsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.input = self.root / "input.json"
        self.output = self.root / "verdict.json"
        self.summary = self.root / "summary.md"
        self.input.write_text(json.dumps(VALID), encoding="utf-8")

    def invoke(self, **kwargs):
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            code = run(self.input, json_output=self.output, **kwargs)
        return code, json.loads(captured.getvalue())

    def artifact(self):
        return json.loads(self.output.read_text(encoding="utf-8"))

    def assert_no_temp_files(self):
        self.assertEqual(list(self.root.glob(".aeg-verdict-*.tmp")), [])

    def test_atomic_success_creates_valid_json_and_no_leftover_temp(self):
        code, stdout = self.invoke(summary_file=self.summary)
        self.assertEqual(code, 0)
        self.assertEqual(stdout["decision"], "ALLOW")
        self.assertEqual(self.artifact()["decision"], "ALLOW")
        self.assertIn("`ALLOW`", self.summary.read_text())
        self.assert_no_temp_files()

    def test_reused_destination_does_not_retain_old_allow_for_block(self):
        self.output.write_text('{"decision": "ALLOW", "obsolete": true}')
        self.input.write_text(json.dumps({**VALID, "evidence": {}}))
        code, stdout = self.invoke()
        self.assertEqual(code, 2)
        self.assertEqual(stdout["decision"], "BLOCK")
        self.assertEqual(self.artifact()["decision"], "BLOCK")
        self.assertNotIn("obsolete", self.artifact())
        self.assert_no_temp_files()

    def test_reused_destination_does_not_retain_allow_for_invalid_input(self):
        self.output.write_text('{"decision": "ALLOW"}')
        self.input.write_text("{not valid JSON")
        code, stdout = self.invoke()
        self.assertEqual(code, 64)
        self.assertEqual(stdout["decision"], "ERROR")
        self.assertEqual(self.artifact()["decision"], "ERROR")
        self.assert_no_temp_files()

    def test_partial_write_simulation_fails_closed_and_cleans_temp(self):
        self.output.write_text('{"decision": "ALLOW"}')
        with patch("agent_evidence_guard.github_ci.os.fsync", side_effect=[OSError("injected fsync error"), None]):
            code, stdout = self.invoke(summary_file=self.summary)
        self.assertEqual(code, 64)
        self.assertEqual(stdout["decision"], "ERROR")
        self.assertEqual(self.artifact()["decision"], "ERROR")
        self.assertFalse(self.summary.exists())
        self.assert_no_temp_files()

    def test_replace_failure_retries_error_artifact(self):
        self.output.write_text('{"decision": "ALLOW"}')
        actual_replace = os.replace
        attempts = [0]

        def fail_once_then_replace(src, dst):
            attempts[0] += 1
            if attempts[0] == 1:
                raise OSError("injected replace error")
            return actual_replace(src, dst)

        with patch("agent_evidence_guard.github_ci.os.replace", side_effect=fail_once_then_replace) as replace:
            code, stdout = self.invoke(summary_file=self.summary)
        self.assertEqual(code, 64)
        self.assertEqual(stdout["decision"], "ERROR")
        self.assertEqual(self.artifact()["decision"], "ERROR")
        self.assertEqual(replace.call_count, 2)
        self.assertFalse(self.summary.exists())
        self.assert_no_temp_files()

    def test_unrecoverable_replace_failure_removes_stale_artifact(self):
        self.output.write_text('{"decision": "ALLOW"}')
        with patch("agent_evidence_guard.github_ci.os.replace", side_effect=OSError("injected persistent error")):
            code, stdout = self.invoke(summary_file=self.summary)
        self.assertEqual(code, 64)
        self.assertEqual(stdout["decision"], "ERROR")
        self.assertFalse(self.output.exists())
        self.assertFalse(self.summary.exists())
        self.assert_no_temp_files()

    def test_summary_failure_replaces_published_allow_with_error(self):
        def write_summary_fails(path, content, append):
            self.assertEqual(self.artifact()["decision"], "ALLOW")
            raise OSError("injected summary failure")
        with patch("agent_evidence_guard.github_ci._write_summary", side_effect=write_summary_fails):
            code, stdout = self.invoke(summary_file=self.summary)
        self.assertEqual(code, 64)
        self.assertEqual(stdout["decision"], "ERROR")
        self.assertEqual(self.artifact()["decision"], "ERROR")
        self.assert_no_temp_files()

    def test_summary_failure_and_second_replace_failure_removes_allow(self):
        original_replace = os.replace
        counter = [0]

        def replace_once_then_fail(src, dst):
            counter[0] += 1
            if counter[0] > 1:
                raise OSError("cannot replace error artifact")
            return original_replace(src, dst)

        with patch("agent_evidence_guard.github_ci.os.replace", side_effect=replace_once_then_fail), patch(
            "agent_evidence_guard.github_ci._write_summary", side_effect=OSError("summary failed")
        ):
            code, stdout = self.invoke(summary_file=self.summary)
        self.assertEqual(code, 64)
        self.assertEqual(stdout["decision"], "ERROR")
        self.assertFalse(self.output.exists(), "Prior ALLOW must be removed when error write fails")
        self.assert_no_temp_files()

    def test_input_and_json_output_cannot_alias(self):
        original = self.input.read_text()
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            status = run(self.input, json_output=self.input)
        self.assertEqual(status, 64)
        self.assertEqual(json.loads(stdout.getvalue())["decision"], "ERROR")
        self.assertEqual(self.input.read_text(), original)

    def test_existing_hardlink_alias_to_input_is_rejected(self):
        self.output.hardlink_to(self.input)
        original = self.input.read_text()
        code, stdout = self.invoke()
        self.assertEqual(code, 64)
        self.assertEqual(stdout["decision"], "ERROR")
        self.assertEqual(self.input.read_text(), original)

    def test_summary_hardlink_to_input_is_rejected(self):
        self.summary.hardlink_to(self.input)
        original = self.input.read_text()
        code, stdout = self.invoke(summary_file=self.summary)
        self.assertEqual(code, 64)
        self.assertEqual(stdout["decision"], "ERROR")
        self.assertEqual(self.input.read_text(), original)

    def test_summary_and_verdict_cannot_alias(self):
        code, stdout = self.invoke(summary_file=self.output)
        self.assertEqual(code, 64)
        self.assertEqual(stdout["decision"], "ERROR")
        self.assertFalse(self.output.exists())

    def test_directory_destination_does_not_produce_allow(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = run(self.input, json_output=self.root)
        self.assertEqual(code, 64)
        self.assertEqual(json.loads(stdout.getvalue())["decision"], "ERROR")

    def test_symlink_destination_rejected_without_overwriting_target(self):
        target = self.root / "do-not-touch.txt"
        target.write_text("original")
        self.output.symlink_to(target)
        code, stdout = self.invoke()
        self.assertEqual(code, 64)
        self.assertEqual(stdout["decision"], "ERROR")
        self.assertEqual(target.read_text(), "original")
        self.assertTrue(self.output.is_symlink())

    def test_special_device_rejected_if_available(self):
        special = Path("/dev/full")
        if not special.exists():
            self.skipTest("POSIX /dev/full unavailable")
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = run(self.input, summary_file=self.summary, json_output=special)
        self.assertEqual(code, 64)
        self.assertEqual(json.loads(stdout.getvalue())["decision"], "ERROR")
        self.assertFalse(self.summary.exists())

    def test_block_contract_summary_and_artifact_are_consistent(self):
        self.input.write_text(json.dumps({**VALID, "evidence": {}}))
        code, stdout = self.invoke(summary_file=self.summary)
        self.assertEqual(code, 2)
        self.assertEqual(stdout["decision"], "BLOCK")
        self.assertEqual(self.artifact()["decision"], "BLOCK")
        self.assertIn("`BLOCK`", self.summary.read_text())


if __name__ == "__main__":
    unittest.main()
