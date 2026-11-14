"""Regression tests for ordered visual patch execution in the manual release workflow.

Source-only; no Android build, patch execution or Actions dispatch.
"""
import unittest
from audit_release_patch_order_v93 import MODERN, TESTS, audit


class ReleasePatchOrderTests(unittest.TestCase):
    def setUp(self):
        self.existing = set(MODERN + TESTS)
        self.commands = MODERN + TESTS

    @staticmethod
    def workflow(commands):
        return "on:\n  workflow_dispatch:\njobs:\n  android:\n    steps:\n      - run: |\n" + "".join(
            "          python3 chatgpt-shahta-v40/" + cmd + "\n" for cmd in commands
        )

    def test_complete_order_passes(self):
        _, problems = audit(self.workflow(self.commands), self.existing)
        self.assertEqual([], problems)

    def test_missing_visual_patch_fails(self):
        _, problems = audit(self.workflow(self.commands[1:]), self.existing)
        self.assertTrue(problems)

    def test_reordered_visual_patch_fails(self):
        commands = self.commands.copy()
        commands[2], commands[3] = commands[3], commands[2]
        _, problems = audit(self.workflow(commands), self.existing)
        self.assertIn("visual patches absent or out of order", problems)

    def test_duplicate_visual_patch_fails(self):
        _, problems = audit(self.workflow(self.commands + [MODERN[-1]]), self.existing)
        self.assertTrue(problems)

    def test_missing_test_script_fails(self):
        _, problems = audit(self.workflow(self.commands), self.existing - {TESTS[-1]})
        self.assertIn(TESTS[-1], problems)

    def test_tests_must_follow_last_patch(self):
        commands = [TESTS[0]] + MODERN + TESTS[1:]
        _, problems = audit(self.workflow(commands), self.existing)
        self.assertIn("source tests must run after visual patches", problems)

    def test_tests_must_preserve_order(self):
        commands = MODERN + list(reversed(TESTS))
        _, problems = audit(self.workflow(commands), self.existing)
        self.assertIn("source tests absent or out of order", problems)


if __name__ == "__main__":
    unittest.main()
