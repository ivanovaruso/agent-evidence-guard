import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agent_evidence_guard.core import evaluate
from agent_evidence_guard.github_ci import run

ROOT = Path(__file__).resolve().parents[1]

VALID = {"claim": "implementation complete", "authority_ref": "ISSUE-1", "required_evidence": ["tests"], "evidence": {"tests": "6 passed"}}


class ContractSafetyTests(unittest.TestCase):
    def assert_error(self, payload):
        verdict = evaluate(payload)
        self.assertEqual(verdict.decision, "ERROR", payload)
        self.assertEqual(verdict.admitted_evidence, {})

    def test_missing_or_empty_legacy_claim_blocks(self):
        self.assertEqual(evaluate({**VALID, "claim": " "}).decision, "BLOCK")
        self.assertEqual(evaluate({**VALID, "authority_ref": ""}).decision, "BLOCK")

    def test_declared_happy_path(self):
        self.assertEqual(evaluate(VALID).decision, "ALLOW")

    def test_existing_missing_evidence_blocks(self):
        self.assertEqual(evaluate({**VALID, "evidence": {}}).decision, "BLOCK")

    def test_invalid_contracts_never_allow(self):
        cases = [
            None, [], 3, "string", {**VALID, "claim": 7}, {**VALID, "claim": True},
            {**VALID, "authority_ref": {"fake": "auth"}},
            {**VALID, "required_evidence": {}}, {**VALID, "evidence": []},
            {**VALID, "surprise": "field"},
            {**VALID, "required_evidence": ["tests", "tests"]},
            {**VALID, "required_evidence": [{"name": "tests"}]},
            {**VALID, "prohibited_claims": 7},
            {**VALID, "prohibited_claims": "done"},
            {**VALID, "prohibited_claims": ["x", "x"]},
            {**VALID, "prohibited_claims": None},
            {**VALID, "required_evidence": [True]},
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                self.assert_error(payload)

    def test_extra_whitespace_prohibited_phrase_blocks(self):
        payload = {**VALID, "claim": "production  \tDeployed", "prohibited_claims": ["production deployed"]}
        self.assertEqual(evaluate(payload).decision, "BLOCK")

    def test_false_evidence_remains_block(self):
        self.assertEqual(evaluate({**VALID, "evidence": {"tests": False}}).decision, "BLOCK")

    def test_declared_evidence_does_not_verify_truth(self):
        self.assertEqual(evaluate({**VALID, "evidence": {"tests": "9999 passed"}}).decision, "ALLOW")

    def test_cli_rejects_nonobject_and_malformed_input(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/"payload.json"
            for content in ('[]', '{garbled', json.dumps({**VALID, "required_evidence": [{"name": "tests"}]})):
                path.write_text(content)
                result = subprocess.run([sys.executable, "-m", "agent_evidence_guard.cli", str(path)], cwd=ROOT, text=True, capture_output=True)
                self.assertEqual(result.returncode, 64, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertIn('"decision": "ERROR"', result.stdout)

    def test_cli_help_version(self):
        for flag in ("--help", "--version"):
            result = subprocess.run([sys.executable, "-m", "agent_evidence_guard.cli", flag], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0)
            self.assertTrue(result.stdout.strip())

    def test_github_adapter_errors_are_exit_64(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            path = root/"payload.json"
            out = root/"verdict.json"
            path.write_text(json.dumps({**VALID, "prohibited_claims": 7}))
            with contextlib.redirect_stdout(io.StringIO()):
                exit_code = run(path, json_output=out)
            self.assertEqual(exit_code, 64)
            self.assertEqual(json.loads(out.read_text())["decision"], "ERROR")


class ActionBoundaryTests(unittest.TestCase):
    def test_action_uses_env_and_isolated_python(self):
        text = (ROOT/"action.yml").read_text()
        self.assertIn("AEG_INPUT_PATH: ${{ inputs.input }}", text)
        self.assertIn('"$AEG_INPUT_PATH"', text)
        self.assertIn("python -I -c", text)
        self.assertNotIn('"${{ inputs.input }}"', text)
        self.assertNotIn('"${{ inputs.json-output }}"', text)

    def test_isolated_action_import_resists_checkout_shadowing(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root/"agent_evidence_guard").mkdir()
            marker = root/"shadow-marker.txt"
            (root/"agent_evidence_guard"/"__init__.py").write_text("raise RuntimeError('checkout shadowed')")
            (root/"agent_evidence_guard"/"github_ci.py").write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('BAD')\n")
            payload = root/"in.json"
            payload.write_text(json.dumps(VALID))
            code = "import sys; sys.path.insert(0, sys.argv.pop(1)); from agent_evidence_guard.github_ci import main; main()"
            process = subprocess.run([sys.executable, "-I", "-c", code, str(ROOT), str(payload), "--json-output", str(root/"out.json")], cwd=root, capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertFalse(marker.exists())
            self.assertEqual(json.loads((root/"out.json").read_text())["decision"], "ALLOW")

    def test_real_composite_run_script_from_untrusted_checkout(self):
        # Execute the exact Bash script read from the action definition,
        # with GitHub-supplied env values, without installing a runner.
        import textwrap
        action = (ROOT / "action.yml").read_text()
        script = textwrap.dedent(action.split("      run: |\n", 1)[1])
        with tempfile.TemporaryDirectory() as d:
            checkout = Path(d)
            marker = checkout / "MUST_NOT_EXECUTE"
            (checkout / "agent_evidence_guard").mkdir()
            (checkout / "agent_evidence_guard" / "__init__.py").write_text(f"from pathlib import Path\nPath({str(marker)!r}).write_text('shadow')\n")
            payload = checkout / "input.json"
            payload.write_text(json.dumps(VALID))
            def invoke(input_path):
                env = {**os.environ,
                       "AEG_ACTION_PATH": str(ROOT),
                       "AEG_INPUT_PATH": input_path,
                       "AEG_JSON_OUTPUT_PATH": str(checkout / "verdict.json")}
                return subprocess.run(["bash", "-eo", "pipefail", "-c", script], cwd=checkout, env=env,
                                      text=True, capture_output=True)
            ok = invoke(str(payload))
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertFalse(marker.exists())
            self.assertEqual(json.loads((checkout / "verdict.json").read_text())["decision"], "ALLOW")
            malicious = f"$(touch {marker})"
            denied = invoke(malicious)
            self.assertEqual(denied.returncode, 64, denied.stderr)
            self.assertFalse(marker.exists())

    def test_shell_values_remain_literal_under_env(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            marker=root/"unwanted.txt"
            attack=f'$(touch {marker})'
            result=subprocess.run(["bash", "-c", 'printf "%s" "$AEG_INPUT_PATH"'], env={**os.environ, "AEG_INPUT_PATH": attack}, text=True, capture_output=True)
            self.assertEqual(result.stdout, attack)
            self.assertFalse(marker.exists())
