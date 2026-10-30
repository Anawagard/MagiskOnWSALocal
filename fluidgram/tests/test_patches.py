import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from apply_fluidgram import replace_exact, MOTION_CLASS, ICON

class FluidGramTest(unittest.TestCase):
    def test_strict_patch(self):
        self.assertEqual(replace_exact("a", "a", "b", "test"), "b")
        with self.assertRaises(RuntimeError):
            replace_exact("aaa", "a", "b", "test")
    def test_motion(self):
        self.assertIn("PathInterpolator", MOTION_CLASS)
        self.assertIn("440L", MOTION_CLASS)
    def test_branding(self):
        self.assertIn("<vector", ICON)
        self.assertNotIn("paper plane", ICON)

if __name__ == "__main__":
    unittest.main()
