"""Regression: baseline prerequisites remain enforced with python -O.

Source-only test; does not invoke Gradle, Android SDK or Actions.
"""
import ast
from pathlib import Path
import unittest

SCRIPT = Path(__file__).with_name("audit_archived_baseline_v83.py")


class BaselineOptimizedContract(unittest.TestCase):
    def test_prerequisites_do_not_depend_on_assert_statements(self):
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        audit = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                     and n.name == "audit")
        self.assertFalse(any(isinstance(n, ast.Assert) for n in ast.walk(audit)),
                         "Python -O removes assert statements from audit()")
        source = ast.get_source_segment(SCRIPT.read_text(encoding="utf-8"), audit)
        self.assertIn("ARCHIVE.is_file()", source)
        self.assertIn("WORKFLOW.is_file()", source)
        self.assertIn("raise FileNotFoundError", source)


if __name__ == "__main__":
    unittest.main()
