"""Regression tests for independent reviewer FAIL_SCOPED F1-F5 and duplicate JSON keys."""

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

from agent_evidence_guard.github_ci import run

ROOT = Path(__file__).resolve().parents[1]
VALID = {'claim': 'done', 'authority_ref': 'ISSUE-1', 'required_evidence': ['tests'], 'evidence': {'tests': '7 passed'}}


class ReviewerFindingTests(unittest.TestCase):
    def run_cli(self, content, module='agent_evidence_guard.cli'):
        with tempfile.TemporaryDirectory() as d:
            input_file = Path(d) / 'input.json'
            input_file.write_text(content, encoding='utf-8')
            args = [sys.executable, '-m', module, str(input_file)]
            if module == 'agent_evidence_guard.github_ci':
                args += ['--json-output', str(Path(d) / 'out.json')]
            p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
            return p

    def test_f1_action_does_not_accept_help_as_input(self):
        script = textwrap.dedent((ROOT / 'action.yml').read_text().split('      run: |\n')[1])
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'verdict.json'
            env = {**os.environ, 'AEG_ACTION_PATH': str(ROOT), 'AEG_INPUT_PATH': '--help', 'AEG_JSON_OUTPUT_PATH': str(out)}
            p = subprocess.run(['bash', '-eo', 'pipefail', '-c', script], cwd=d, env=env, capture_output=True, text=True)
            self.assertEqual(p.returncode, 64, p.stdout + p.stderr)
            self.assertEqual(json.loads(out.read_text())['decision'], 'ERROR')
            self.assertNotIn('usage: agent-evidence-guard-github', p.stdout)

    def test_f2_json_nonfinite_rejected_by_both_clis(self):
        for item in ('NaN', 'Infinity', '-Infinity', '1e9999'):
            content = '{"claim":"done","authority_ref":"x","required_evidence":["tests"],"evidence":{"tests":' + item + '}}'
            for module in ('agent_evidence_guard.cli', 'agent_evidence_guard.github_ci'):
                with self.subTest(value=item, module=module):
                    p = self.run_cli(content, module)
                    self.assertEqual(p.returncode, 64, p.stdout + p.stderr)
                    self.assertEqual(json.loads(p.stdout)['decision'], 'ERROR')
                    self.assertNotIn('Traceback', p.stderr)

    def test_f3_excessive_nesting_is_controlled_error(self):
        content = '[' * 20000 + '0' + ']' * 20000
        for module in ('agent_evidence_guard.cli', 'agent_evidence_guard.github_ci'):
            with self.subTest(module=module):
                p = self.run_cli(content, module)
                self.assertEqual(p.returncode, 64, p.stdout + p.stderr)
                self.assertEqual(json.loads(p.stdout)['decision'], 'ERROR')
                self.assertNotIn('Traceback', p.stderr)

    def test_f4_adapter_parser_failures_are_64(self):
        for args in ([], ['--unknown'], ['--json-output']):
            p = subprocess.run([sys.executable, '-m', 'agent_evidence_guard.github_ci'] + args, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(p.returncode, 64, p.stdout + p.stderr)
            self.assertIn('error:', p.stderr)

    def test_f5_directory_output_returns_error_without_allow_stdout(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            input_path = root / 'in.json'
            input_path.write_text(json.dumps(VALID))
            for flag in ('--json-output', '--summary-file'):
                artifact = root / 'verdict.json'
                p = subprocess.run([sys.executable, '-m', 'agent_evidence_guard.github_ci', str(input_path), flag, str(root), '--json-output', str(artifact)] if flag == '--summary-file' else [sys.executable, '-m', 'agent_evidence_guard.github_ci', str(input_path), flag, str(root)], cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(p.returncode, 64, p.stdout + p.stderr)
                self.assertEqual(json.loads(p.stdout)['decision'], 'ERROR')
                self.assertNotIn('Traceback', p.stderr)
                self.assertNotIn('"decision": "ALLOW"', p.stdout)
                if flag == '--summary-file':
                    self.assertEqual(json.loads(artifact.read_text())['decision'], 'ERROR')

    def test_duplicate_json_object_key_rejected_including_nested(self):
        for content in (
            '{"claim":"done","authority_ref":"x","required_evidence":["tests"],"required_evidence":[],"evidence":{}}',
            '{"claim":"done","authority_ref":"x","required_evidence":["tests"],"evidence":{"tests":"pass","tests":"fake"}}',
        ):
            for module in ('agent_evidence_guard.cli', 'agent_evidence_guard.github_ci'):
                p = self.run_cli(content, module)
                self.assertEqual(p.returncode, 64, p.stdout + p.stderr)
                self.assertIn('duplicate JSON object key', p.stdout)

    def test_io_failure_does_not_leave_allow_artifact_if_summary_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            payload = root / 'payload.json'
            payload.write_text(json.dumps(VALID))
            verdict_path = root / 'out.json'
            verdict_path.write_text('{"decision": "ALLOW"}')
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = run(payload, summary_file=root, json_output=verdict_path)
            self.assertEqual(code, 64)
            self.assertEqual(json.loads(output.getvalue())['decision'], 'ERROR')
            self.assertEqual(json.loads(verdict_path.read_text())['decision'], 'ERROR')

    def test_standard_json_and_normal_claim_still_allow(self):
        for module in ('agent_evidence_guard.cli', 'agent_evidence_guard.github_ci'):
            p = self.run_cli(json.dumps(VALID), module)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            self.assertEqual(json.loads(p.stdout)['decision'], 'ALLOW')


if __name__ == '__main__':
    unittest.main()
