"""Source-only v7.9 overlay geometry regression (no Android build).

The game draws in a 360x800 logical viewport. Check notification panels against
interactive regions for all five pages, including simulated narrow displays.
"""
from pathlib import Path
import ast
import re
import unittest

HERE = Path(__file__).resolve().parent
PATCH = HERE / "patch_modernist_v79.py"
VIEW_W, VIEW_H = 360, 800
TOAST_X, TOAST_W, TOAST_H = 18, 324, 26
ORE = (105, 210, 330, 440)
FEATURE_CARDS_BOTTOM = 615
BOTTOM_INTERACTION_START = 653


def intersects(a, b):
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])


def fitted_rect(rect, width, height):
    """Uniform aspect-fit, with letterboxing and no coordinate distortion."""
    scale = min(width / VIEW_W, height / VIEW_H)
    ox, oy = (width - VIEW_W * scale) / 2, (height - VIEW_H * scale) / 2
    return tuple((ox + v * scale) if i % 2 == 0 else (oy + v * scale)
                 for i, v in enumerate(rect))


class ToastGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PATCH.read_text(encoding="utf-8")
        ast.parse(cls.source, filename=str(PATCH))
        cls.mine_y, cls.feature_y = map(int, re.search(
            r"int toastY = page==0 \? (\d+) : (\d+);", cls.source
        ).groups())

    def test_all_five_pages_have_clear_overlay_regions(self):
        for page in range(5):
            with self.subTest(page=page):
                y = self.mine_y if page == 0 else self.feature_y
                panel = (TOAST_X, y, TOAST_X + TOAST_W, y + TOAST_H)
                self.assertGreaterEqual(panel[0], 0)
                self.assertLessEqual(panel[2], VIEW_W)
                if page == 0:
                    self.assertFalse(intersects(panel, ORE))
                    self.assertLessEqual(panel[3], 205)
                else:
                    self.assertGreaterEqual(panel[1], FEATURE_CARDS_BOTTOM)
                    self.assertLessEqual(panel[3], BOTTOM_INTERACTION_START)

    def test_aspect_fit_preserves_separation_on_narrow_screens(self):
        for width, height in ((280, 800), (320, 720), (360, 800), (412, 915)):
            with self.subTest(screen=(width, height)):
                mine = fitted_rect((TOAST_X, self.mine_y, TOAST_X + TOAST_W,
                                    self.mine_y + TOAST_H), width, height)
                ore = fitted_rect(ORE, width, height)
                self.assertFalse(intersects(mine, ore))
                feature = fitted_rect((TOAST_X, self.feature_y, TOAST_X + TOAST_W,
                                       self.feature_y + TOAST_H), width, height)
                bottom_y = fitted_rect((0, BOTTOM_INTERACTION_START, VIEW_W, VIEW_H),
                                       width, height)[1]
                self.assertLessEqual(feature[3], bottom_y)

    def test_patch_changes_only_toast_drawing_not_touch_handlers(self):
        tree = ast.parse(self.source)
        old = new = None
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in ("old", "new"):
                        value = ast.literal_eval(node.value)
                        if target.id == "old":
                            old = value
                        else:
                            new = value
        self.assertIsNotNone(old)
        self.assertIsNotNone(new)
        self.assertIn("int toastY = page==0 ? 178 : 623;", new)
        self.assertNotIn("onTouchEvent", old + new)
        self.assertEqual(old.count("v72NineSlice("), new.count("v72NineSlice("))


if __name__ == "__main__":
    unittest.main()
