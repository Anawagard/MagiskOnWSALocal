"""Source-only regression: inspect actual Java replacement template from v7.9.

No Gradle, APK, emulator, or Actions execution.
"""
import ast
from pathlib import Path
import re
import unittest

PATCH = Path(__file__).with_name("patch_modernist_v79.py")


def replacement_java(source):
    module = ast.parse(source)
    values = [node.value for node in module.body if isinstance(node, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == "new" for t in node.targets)]
    if len(values) != 1:
        raise AssertionError("Expected exactly one Java replacement template")
    return ast.literal_eval(values[0])


def positions(java):
    match = re.search(
        r"int\s+toastY\s*=\s*page\s*==\s*0\s*\?\s*(\d+)\s*:\s*"
        r"\(page\s*==\s*1\s*\?\s*(\d+)\s*:\s*(\d+)\);", java)
    if match is None:
        raise AssertionError("Missing contextual toast expression")
    return tuple(map(int, match.groups()))


class ToastSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.java = replacement_java(PATCH.read_text(encoding="utf-8"))

    def test_single_surface(self):
        self.assertEqual(self.java.count('v72NineSlice(canvas,"panel.png",18,toastY,324,26,252);'), 1)
        self.assertEqual(self.java.count('leftFittedText(canvas,toast,39,toastY+18,12,0xfff0fffb,285);'), 1)

    def test_geometry_from_java(self):
        mine, shop, feature = positions(self.java)
        for page in range(5):
            y = mine if page == 0 else shop if page == 1 else feature
            with self.subTest(page=page):
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(y + 26, 690)
                if page == 0:
                    self.assertLessEqual(y + 26, 205)
                elif page == 1:
                    self.assertGreaterEqual(y, 615)
                    self.assertLessEqual(y + 26, 653)
                else:
                    self.assertGreaterEqual(y, 653)

    def test_decorations_inside_panel(self):
        self.assertIn('rect(canvas,26,toastY+4,3,18,0xff65e1d0);', self.java)
        self.assertIn('rect(canvas,36,toastY+22,296,1,0xff315d60);', self.java)

    def test_mutation_detection(self):
        original = positions(self.java)
        self.assertNotEqual(positions(self.java.replace("? 623 :", "? 610 :")), original)
        with self.assertRaises(AssertionError):
            positions(self.java.replace("int toastY", "int removedY"))


if __name__ == "__main__":
    unittest.main()
