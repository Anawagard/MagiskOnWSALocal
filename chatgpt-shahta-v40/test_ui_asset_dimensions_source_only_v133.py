"""Regression for exact-size UI raster inventory; Python-only, no APK."""
import ast
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
VERIFY = HERE / "verify_generated_art_source_only.py"
EXPECTED = {
    "panel.png": (400, 96),
    "button.png": (160, 64),
    "button_off.png": (160, 64),
    "header.png": (360, 88),
    "nav.png": (360, 50),
    "fractures.png": (300, 300),
    "miner.png": (240, 340),
}


class UiRasterDimensions(unittest.TestCase):
    def test_manifest_and_guard(self):
        source = VERIFY.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(VERIFY))
        verify = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                      and n.name == "verify")
        assignments = [
            n for n in ast.walk(verify)
            if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "ui_dimensions"
                    for t in n.targets)
        ]
        self.assertEqual(len(assignments), 1)
        actual = ast.literal_eval(assignments[0].value)
        self.assertEqual(actual, EXPECTED)
        self.assertEqual(len(actual), 7)
        self.assertEqual(len(set(actual)), 7)
        for name, size in actual.items():
            self.assertTrue(name.endswith(".png"))
            self.assertEqual(len(size), 2)
            self.assertTrue(all(isinstance(x, int) and x >= 18 for x in size))
        self.assertIn(
            "if filename in ui_dimensions and img.size != ui_dimensions[filename]:",
            source,
        )
        self.assertIn("f\"{ui_dimensions[filename]}, got {img.size}\"", source)
        self.assertLess(
            source.index("if filename in ui_dimensions and img.size"),
            source.index('if filename.startswith("menu_")'),
        )

    def test_all_mismatched_dimensions_rejected(self):
        # Mirror the pure size predicate to cover wrong aspect ratios and
        # otherwise decodable but incorrectly sized PNGs.
        for name, size in EXPECTED.items():
            self.assertFalse(size != EXPECTED[name])
            for bad in ((size[0] + 1, size[1]),
                        (size[0], size[1] + 1),
                        (size[1], size[0]),
                        (16, 16)):
                if bad != size:
                    self.assertTrue(bad != EXPECTED[name], (name, bad))


if __name__ == "__main__":
    unittest.main()
