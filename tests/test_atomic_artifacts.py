"""Issue #20: prevent partial/stale machine verdicts on output failures."""

import contextlib
import io
import json
import os
import subprocess
import sys
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
        self.assertEqual(self.artifact()["decision"], "ERROR")

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

    def test_f1_circular_symlink_as_json_output_returns_error64(self):
        self.output.symlink_to(self.output)
        code, stdout = self.invoke()
        self.assertEqual(code, 64)
        self.assertEqual(stdout["decision"], "ERROR")
        self.assertTrue(self.output.is_symlink())
        self.assert_no_temp_files()

    def test_f1_circular_symlink_as_summary_returns_error64(self):
        self.summary.symlink_to(self.summary)
        self.output.write_text('{"decision":"ALLOW","old":true}')
        code, stdout = self.invoke(summary_file=self.summary)
        self.assertEqual(code, 64)
        self.assertEqual(stdout["decision"], "ERROR")
        self.assertEqual(self.artifact()["decision"], "ERROR")
        self.assertNotIn("old", self.artifact())
        self.assertTrue(self.summary.is_symlink())
        self.assert_no_temp_files()

    def test_f1_circular_symlink_as_input_returns_error64(self):
        self.input.unlink()
        self.input.symlink_to(self.input)
        self.output.write_text('{"decision":"ALLOW","old":true}')
        code, stdout = self.invoke()
        self.assertEqual(code, 64)
        self.assertEqual(stdout["decision"], "ERROR")
        self.assertEqual(self.artifact()["decision"], "ERROR")
        self.assertTrue(self.input.is_symlink())
        self.assert_no_temp_files()

    def test_f1_runtimeerror_during_path_resolve_never_escapes(self):
        # Python 3.10-3.12 can raise RuntimeError while resolving a loop.
        # Test the compatibility branch on a runner that handles it differently.
        with patch("pathlib.Path.resolve", side_effect=RuntimeError("symlink loop")):
            code, stdout = self.invoke(summary_file=self.summary)
        self.assertEqual(code, 0)
        self.assertEqual(stdout["decision"], "ALLOW")
        self.assertEqual(self.artifact()["decision"], "ALLOW")

    def test_f1_circular_paths_cli_no_traceback(self):
        for target in ("input", "output", "summary"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / "input.json"
                source.write_text(json.dumps(VALID))
                json_dest = root / "output.json"
                summary = root / "summary.md"
                dest = {"input": source, "output": json_dest, "summary": summary}[target]
                dest.unlink(missing_ok=True)
                dest.symlink_to(dest)
                process = subprocess.run(
                    [sys.executable, "-m", "agent_evidence_guard.github_ci", str(source),
                     "--json-output", str(json_dest), "--summary-file", str(summary)],
                    capture_output=True, text=True,
                )
                self.assertEqual(process.returncode, 64, process.stderr)
                self.assertEqual(json.loads(process.stdout)["decision"], "ERROR")
                self.assertNotIn("Traceback", process.stderr)

    def test_f2_summary_same_as_input_invalidates_old_allow(self):
        self.output.write_text('{"decision":"ALLOW","old":true}')
        original = self.input.read_text()
        code, stdout = self.invoke(summary_file=self.input)
        self.assertEqual(code, 64)
        self.assertEqual(stdout["decision"], "ERROR")
        self.assertEqual(self.input.read_text(), original)
        self.assertEqual(self.artifact()["decision"], "ERROR")
        self.assertNotIn("old", self.artifact())
        self.assert_no_temp_files()

    def test_f2_hardlinked_summary_input_invalidates_old_allow(self):
        self.summary.hardlink_to(self.input)
        self.output.write_text('{"decision":"ALLOW","old":true}')
        original = self.input.read_text()
        code, stdout = self.invoke(summary_file=self.summary)
        self.assertEqual(code, 64)
        self.assertEqual(stdout["decision"], "ERROR")
        self.assertEqual(self.input.read_text(), original)
        self.assertEqual(self.artifact()["decision"], "ERROR")

    def test_f2_json_alias_input_protected_without_mutation(self):
        original = self.input.read_text()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = run(self.input, summary_file=self.summary, json_output=self.input)
        self.assertEqual(status, 64)
        self.assertEqual(json.loads(output.getvalue())["decision"], "ERROR")
        self.assertEqual(self.input.read_text(), original)
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
