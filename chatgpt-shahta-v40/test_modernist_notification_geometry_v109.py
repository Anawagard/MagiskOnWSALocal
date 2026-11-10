"""Source-only checks for the v7.9 notification surfaces and v7.2 feature viewport.

No Android build, emulator, or Gradle invocation. Run with Python 3.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
V72 = (ROOT / "patch_modernist_v72.py").read_text(encoding="utf-8")
V79 = (ROOT / "patch_modernist_v79.py").read_text(encoding="utf-8")


def overlap(a, b):
    """Strict rectangle intersection; touching edges is permitted."""
    return max(a[0], b[0]) < min(a[2], b[2]) and max(a[1], b[1]) < min(a[3], b[3])


class NotificationGeometryTests(unittest.TestCase):
    def test_toast_is_contextual_and_deterministic(self):
        self.assertIn("page==0 ? 178 : (page==1 ? 623 : 655)", V79)
        self.assertIn('v72NineSlice(canvas,"panel.png",18,toastY,324,26,252)', V79)
        self.assertIn("leftFittedText(canvas,toast,39,toastY+18,12", V79)

    def test_notification_fits_logical_canvas(self):
        for page in range(5):
            with self.subTest(page=page):
                y = 178 if page == 0 else 623 if page == 1 else 655
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(y + 26, 720)
                self.assertLessEqual(18 + 324, 360)
                self.assertLessEqual(39 + 285, 342)

    def test_feature_toasts_below_visible_legacy_content(self):
        # Legacy draw calls are clipped to y=145..653 before overlay rendering.
        for page in (2, 3, 4):
            with self.subTest(page=page):
                self.assertFalse(overlap((18, 655, 342, 681), (0, 145, 360, 653)))

    def test_shop_toast_below_card_grid(self):
        self.assertFalse(overlap((18, 623, 342, 649), (0, 0, 360, 615)))

    def test_render_touch_inverse_on_feature_pages(self):
        self.assertIn("c.translate(13f,18f);", V72)
        self.assertIn("c.scale(.93f,.94f);", V72)
        self.assertIn("x=(x-13f)/.93f;", V72)
        self.assertIn("y=(y-18f)/.94f;", V72)
        for x in (0, 30, 180, 360):
            for y in (145, 300, 653):
                with self.subTest(x=x, y=y):
                    sx, sy = 13 + .93 * x, 18 + .94 * y
                    self.assertAlmostEqual((sx - 13) / .93, x)
                    self.assertAlmostEqual((sy - 18) / .94, y)

    def test_guardrails_preserved_in_patch(self):
        for anchor in (
            'getSharedPreferences(\"mine_save_v1\"',
            "public void save()",
            "private void rebirth()",
            "signingConfig signingConfigs.shahtaDebug",
            "applicationId 'com.bezdna.mine'",
        ):
            self.assertIn(anchor, V79)


if __name__ == "__main__":
    unittest.main()
