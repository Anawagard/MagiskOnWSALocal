"""Source-only regression for v7.9's final five-page toast Java template.

Checks actual replacement Java parsed out of the patch, including the +60
translation of the PAGE artwork that is not applied to the global toast.
No Android SDK, emulator, APK, Gradle, or Actions execution.
"""
import ast
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
PATCH = ROOT / "patch_modernist_v79.py"
HEIGHT = 26


def templates(source):
    result = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign):
            for name in node.targets:
                if isinstance(name, ast.Name) and name.id in ("old", "new"):
                    result[name.id] = ast.literal_eval(node.value)
    if set(result) != {"old", "new"}:
        raise AssertionError("Expected exactly one old/new Java replacement")
    return result


def positions(java):
    match = re.search(
        r"int toastY = page==0 \? (\d+) : \(page==1 \? (\d+) : (\d+)\);",
        java,
    )
    if match is None:
        raise AssertionError("Missing five-page Java toast coordinate expression")
    return tuple(map(int, match.groups()))


def validate(java):
    mine, shop, feature = positions(java)
    if not (240 <= mine and mine + HEIGHT <= 266):
        raise AssertionError("Mine toast covers shifted HUD or ore")
    if not (690 < shop and shop + HEIGHT <= 720):
        raise AssertionError("Shop toast covers shifted cards/settings")
    if not (174 < feature and feature + HEIGHT <= 203):
        raise AssertionError("Feature toast covers header title or feature controls")
    for top in (mine, shop, feature):
        if not (136 < top and top + HEIGHT <= 720):
            raise AssertionError("Toast off the 360x720 screen")
    return mine, shop, feature


class ToastSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patch = PATCH.read_text(encoding="utf-8")
        cls.java = templates(cls.patch)["new"]

    def test_real_java_geometry(self):
        self.assertEqual(validate(self.java), (240, 691, 177))
        v70 = (ROOT / "patch_full_redesign_v70.py").read_text(encoding="utf-8")
        self.assertIn("canvas.translate(0,60);", v70)
        self.assertIn("canvas.clipRect(0,87,360,653);", v70)

    def test_single_panel_and_safe_content(self):
        self.assertEqual(self.java.count('v72NineSlice(canvas,"panel.png",18,toastY,324,26,252);'), 1)
        self.assertEqual(self.java.count('leftFittedText(canvas,toast,39,toastY+18,12,0xfff0fffb,251);'), 1)
        self.assertIn('rect(canvas,26,toastY+4,3,18,toastAccent);', self.java)
        self.assertIn('rect(canvas,36,toastY+22,296,1,0xff315d60);', self.java)
        self.assertIn('v70Draw(canvas,String.format(Locale.US,"ore_%02d.png",(page*5)%24)', self.java)
        self.assertLess(39 + 251, 301)  # Text doesn't touch 25px ore badge.
        self.assertLessEqual(301 + 25, 18 + 324)
        self.assertLessEqual(305 + 18, 301 + 25)

    def test_palette_unique_for_all_five_pages(self):
        match = re.search(r"int toastAccent = (.*?);", self.java, re.S)
        self.assertIsNotNone(match)
        colors = re.findall(r"0xff[0-9a-fA-F]{6}", match.group(1))
        self.assertEqual(len(colors), 5)
        self.assertEqual(len(set(colors)), 5)

    def test_patch_has_no_gameplay_or_touch_changes(self):
        original = templates(self.patch)["old"]
        self.assertEqual(original.count("if(System.currentTimeMillis()<toastUntil)"), 1)
        self.assertEqual(self.java.count("if(System.currentTimeMillis()<toastUntil)"), 1)
        for banned in ("onTouchEvent", "getSharedPreferences", "save()", "rebirth()"):
            self.assertNotIn(banned, self.java)
        sentinel = "before\n" + original + "\nafter"
        self.assertEqual(sentinel.replace(original, self.java, 1),
                         "before\n" + self.java + "\nafter")

    def test_screen_space_fits_eleven_device_sizes(self):
        tops = (240, 691, 177, 177, 177)
        sizes = ((176,320),(240,320),(280,560),(320,568),(360,720),
                 (393,873),(720,1280),(1080,2400),(1272,2772),
                 (2560,720),(720,2560))
        for width, height in sizes:
            scale = min(width / 360, height / 720)
            ox, oy = (width - 360 * scale) / 2, (height - 720 * scale) / 2
            for top in tops:
                with self.subTest(device=(width,height), top=top):
                    self.assertGreaterEqual(ox + 18 * scale, 0)
                    self.assertLessEqual(ox + 342 * scale, width)
                    self.assertGreaterEqual(oy + top * scale, 0)
                    self.assertLessEqual(oy + (top + HEIGHT) * scale, height)

    def test_adversarial_old_coordinates_rejected(self):
        for original, changed in (("? 240 :", "? 178 :"),
                                  ("? 691 :", "? 655 :"),
                                  (": 177);", ": 145);")):
            broken = self.java.replace(original, changed)
            self.assertNotEqual(broken, self.java)
            with self.assertRaises(AssertionError):
                validate(broken)


if __name__ == "__main__":
    unittest.main(verbosity=2)
