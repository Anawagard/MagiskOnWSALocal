"""Guard against accidentally commenting out the real alpha-occupancy check.

This source-only regression uses AST rather than a string marker: an escaped
literal '\\n' inside a Python comment previously hid the assignment and caused
the full 59-asset audit to fail with UnboundLocalError at runtime.
No Android, Gradle, Actions, project restoration, or generated assets needed.
"""
import ast
from pathlib import Path
import unittest

AUDIT = Path(__file__).with_name("verify_generated_art_source_only.py")


class ArtOccupancyAssignmentTest(unittest.TestCase):
    def test_occupancy_is_assigned_before_validation(self):
        source = AUDIT.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(AUDIT))
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                     and node.name == "verify"]
        self.assertEqual(len(functions), 1)
        function = functions[0]
        assignments = [node for node in ast.walk(function)
                       if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Name)
                               and target.id == "actual_occupancy"
                               for target in node.targets)]
        self.assertEqual(len(assignments), 1)
        assignment = assignments[0]
        self.assertIn("np.mean(rgba[:, :, 3] > 16)",
                      ast.get_source_segment(source, assignment.value))
        reads = [node for node in ast.walk(function)
                 if isinstance(node, ast.Name)
                 and node.id == "actual_occupancy"
                 and isinstance(node.ctx, ast.Load)]
        self.assertGreaterEqual(len(reads), 3)
        self.assertTrue(all(assignment.lineno < node.lineno for node in reads))
        # Ensure no accidental escaped line breaks remain in comments near
        # the assignment; Python otherwise parses but silently skips the code.
        lines = source.splitlines()
        self.assertNotIn(r"\\n", lines[assignment.lineno - 2])
        self.assertNotIn(r"\\n", lines[assignment.lineno - 3])


if __name__ == "__main__":
    unittest.main(verbosity=2)
