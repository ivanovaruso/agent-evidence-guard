import tomllib
import unittest
from pathlib import Path

from agent_evidence_guard import __version__


class VersionConsistencyTests(unittest.TestCase):
    def test_runtime_version_matches_pyproject(self):
        pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(__version__, pyproject["project"]["version"])


if __name__ == "__main__":
    unittest.main()
