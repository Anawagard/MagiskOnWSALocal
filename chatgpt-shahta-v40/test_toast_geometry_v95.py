"""Screen-coordinate regression for the final v7.9 notification overlay.

The game uses a 360x720 logical canvas. Page art is translated 60px down,
but the toast is rendered after canvas.restore(), so its coordinates are not.
No Android/Gradle build, emulator, or GitHub Actions.
"""
from pathlib import Path
import ast
import re
import unittest

HERE = Path(__file__).resolve().parent
PATCH = HERE / "patch_modernist_v79.py"
VIEW_W, VIEW_H = 360, 720
TOAST_X, TOAST_W, TOAST_H = 18, 324, 26
PAGE_SHIFT = 60


def toasts(source):
    match = re.search(
        r"int toastY = page==0 \? (\d+) : \(page==1 \? (\d+) : (\d+)\);",
        source,
    )
    if match is None:
        raise AssertionError("Toast Java placement absent")
    mine, shop, feature = map(int, match.groups())
    return (mine, shop, feature, feature, feature)


def rect(x0, y0, x1, y1):
    return (x0, y0, x1, y1)


def overlap(a, b):
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])


def physical(box, width, height):
    scale = min(width / VIEW_W, height / VIEW_H)
    ox, oy = (width - VIEW_W * scale) / 2, (height - VIEW_H * scale) / 2
    return tuple((ox + v * scale) if i % 2 == 0 else (oy + v * scale)
                 for i, v in enumerate(box))


class ToastGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PATCH.read_text(encoding="utf-8")
        ast.parse(cls.source)
        cls.tops = toasts(cls.source)

    def test_five_pages_use_real_screen_space(self):
        self.assertEqual(self.tops, (240, 691, 177, 177, 177))
        v70 = (HERE / "patch_full_redesign_v70.py").read_text(encoding="utf-8")
        self.assertIn("canvas.translate(0,60);", v70)
        self.assertIn("canvas.restore();", v70)
        self.assertIn("canvas.clipRect(0,87,360,653);", v70)

    def test_notices_do_not_cover_active_controls(self):
        mine = rect(18, self.tops[0], 342, self.tops[0] + TOAST_H)
        shop = rect(18, self.tops[1], 342, self.tops[1] + TOAST_H)
        feature = rect(18, self.tops[2], 342, self.tops[2] + TOAST_H)
        telemetry = rect(18, 93 + PAGE_SHIFT, 342, 176 + PAGE_SHIFT)
        ore = rect(105, 210 + PAGE_SHIFT, 330, 440 + PAGE_SHIFT)
        settings_panel = rect(14, 153 + PAGE_SHIFT, 346, 630 + PAGE_SHIFT)
        feature_content = rect(0, 145 + PAGE_SHIFT, 360, 653 + PAGE_SHIFT)
        self.assertFalse(overlap(mine, telemetry))
        self.assertFalse(overlap(mine, ore))
        self.assertFalse(overlap(shop, settings_panel))
        self.assertFalse(overlap(feature, feature_content))
        self.assertGreater(feature[1], 114 + PAGE_SHIFT)

        for row in range(3):
            for col in range(2):
                x, y = 10 + col * 175, 164 + row * 153 + PAGE_SHIFT
                purchase = rect(x + 13, y + 102, x + 152, y + 138)
                self.assertFalse(overlap(shop, purchase))
        navigation = rect(0, 88, 360, 136)
        for notice in (mine, shop, feature):
            self.assertFalse(overlap(notice, navigation))

    def test_narrow_and_wide_displays_fit(self):
        for w, h in ((176, 320), (240, 320), (320, 568), (360, 720),
                     (393, 852), (1080, 2400), (2560, 720)):
            for y in self.tops:
                with self.subTest(size=(w,h), top=y):
                    a,b,c,d = physical(rect(TOAST_X, y, TOAST_X + TOAST_W,
                                            y + TOAST_H), w, h)
                    self.assertGreaterEqual(a, -1e-7)
                    self.assertGreaterEqual(b, -1e-7)
                    self.assertLessEqual(c, w + 1e-7)
                    self.assertLessEqual(d, h + 1e-7)

    def test_patch_changes_only_one_notification_block(self):
        nodes = ast.parse(self.source).body
        values = {}
        for node in nodes:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in ("old","new"):
                        values[target.id] = ast.literal_eval(node.value)
        self.assertEqual(set(values), {"old", "new"})
        before, after = values["old"], values["new"]
        self.assertEqual(before.count("if(System.currentTimeMillis()<toastUntil)"), 1)
        self.assertEqual(after.count("if(System.currentTimeMillis()<toastUntil)"), 1)
        self.assertEqual(after.count('v72NineSlice(canvas,"panel.png",18,toastY,324,26,252);'), 1)
        sentinels = "before\n" + before + "\nafter"
        self.assertEqual(sentinels.replace(before, after, 1),
                         "before\n" + after + "\nafter")
        self.assertNotIn("onTouchEvent", after)
        self.assertNotIn("getSharedPreferences", after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
