"""Check release-version consistency on every supported Python (>=3.10).

tomllib is only in the standard library from Python 3.11 onward. A narrow,
anchored parse of our single [project] version field keeps this test
dependency-free on 3.10 rather than silently skipping coverage.
"""

import re
import unittest
from pathlib import Path

from agent_evidence_guard import __version__


class VersionConsistencyTests(unittest.TestCase):
    def test_runtime_version_matches_pyproject(self):
        text = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
        project_section = text.split("[project]\n", 1)
        self.assertEqual(len(project_section), 2, "Missing [project] table")
        values = project_section[1].split("\n[", 1)[0]
        versions = re.findall(r'(?m)^version\s*=\s*"([^"]+)"\s*$', values)
        self.assertEqual(len(versions), 1, "Expected exactly one [project] version")
        self.assertEqual(__version__, versions[0])


if __name__ == "__main__":
    unittest.main()
