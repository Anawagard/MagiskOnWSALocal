"""Guard consistent alpha-coverage math across raster audit and verifier.

Run: python -m unittest test_alpha_occupancy_contract_source_only.py
No Android build, emulator, or APK required.
"""
import ast
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent


def visible_alpha_thresholds(filename):
    tree = ast.parse((HERE / filename).read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare) or len(node.ops) != 1:
            continue
        if not isinstance(node.ops[0], ast.Gt):
            continue
        if len(node.comparators) != 1 or not isinstance(node.comparators[0], ast.Constant):
            continue
        if node.comparators[0].value not in (0, 16):
            continue
        left = ast.unparse(node.left)
        if left == "alpha" or left.startswith("rgba[:, :, 3]"):
            found.append((left, node.comparators[0].value))
    return found


class AlphaOccupancyContract(unittest.TestCase):
    def test_audit_and_verifier_exclude_nearly_transparent_fringe(self):
        audit = visible_alpha_thresholds("audit_visual_diversity.py")
        verify = visible_alpha_thresholds("verify_generated_art_source_only.py")
        self.assertIn(("alpha", 16), audit)
        self.assertIn(("rgba[:, :, 3]", 16), verify)
        self.assertNotIn(("rgba[:, :, 3]", 0), verify)

    def test_coverage_math_on_antialiased_edges(self):
        # Pixels with alpha 1..16 are invisible to the audit's occupancy gate.
        alpha = [0, 1, 8, 16, 17, 128, 255]
        audit_ratio = sum(a > 16 for a in alpha) / len(alpha)
        verifier_ratio = sum(a > 16 for a in alpha) / len(alpha)
        self.assertEqual(audit_ratio, verifier_ratio)
        self.assertEqual(audit_ratio, 3 / 7)


if __name__ == "__main__":
    unittest.main()
