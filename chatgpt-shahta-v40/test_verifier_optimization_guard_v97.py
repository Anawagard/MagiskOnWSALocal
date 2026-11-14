"""Regression: optimized Python must never bypass release-critical assertions.

Source-only test; no Android SDK, Gradle, APK, or Actions.
Run: python3 chatgpt-shahta-v40/test_verifier_optimization_guard_v97.py
"""
from pathlib import Path
import os
import subprocess
import sys
import unittest

VERIFIER = Path(__file__).with_name("verify_modernist_patch_chain.py")


class OptimizedVerifierTests(unittest.TestCase):
    def test_optimized_interpreter_fails_before_project_discovery(self):
        env = os.environ.copy()
        env.pop("SHAHTA_BASELINE_PROJECT", None)
        env.pop("PYTHONOPTIMIZE", None)
        result = subprocess.run(
            [sys.executable, "-O", str(VERIFIER)],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("BLOCKED: source-only verification requires Python assertions", result.stderr + result.stdout)
        self.assertNotIn("APPLY source-only", result.stdout)
        self.assertNotIn("PASS:", result.stdout)


if __name__ == "__main__":
    unittest.main()
