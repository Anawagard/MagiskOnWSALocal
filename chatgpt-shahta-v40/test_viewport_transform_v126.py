"""Source-only mathematical regression of v7.1 viewport and v7.4 shop geometry.

Run: python3 chatgpt-shahta-v40/test_viewport_transform_v126.py
No Android SDK, Gradle, network, APK or workflow invocation.
"""
import unittest

# Mirrors Java Float.MIN_NORMAL in patch_modernist_v71.py.
JAVA_FLOAT_MIN_NORMAL = 1.1754943508222875e-38

W, H = 360, 720

def transform(width, height):
    if width <= 0 or height <= 0:
        raise ValueError("Viewport must have positive dimensions")
    scale = max(JAVA_FLOAT_MIN_NORMAL, min(width / W, height / H))
    return scale, (width - W * scale) / 2, (height - H * scale) / 2

def screen_to_logical(px, py, width, height):
    scale, ox, oy = transform(width, height)
    x, y = (px - ox) / scale, (py - oy) / scale
    return (x, y) if 0 <= x < W and 0 <= y < H else None

class ViewportTransformTests(unittest.TestCase):
    def test_round_trip_on_narrow_and_wide_displays(self):
        for width, height in ((360,720),(1080,2354),(1272,2772),
                              (720,1600),(320,640),(240,960),(1440,2560)):
            scale, ox, oy = transform(width, height)
            for x, y in ((0,0),(180,360),(359,719),(105,210),(330,440)):
                with self.subTest(viewport=(width,height), point=(x,y)):
                    actual = screen_to_logical(ox+x*scale, oy+y*scale, width, height)
                    self.assertIsNotNone(actual)
                    self.assertAlmostEqual(actual[0], x, places=6)
                    self.assertAlmostEqual(actual[1], y, places=6)

    def test_tiny_surfaces_have_nonnegative_gutters(self):
        for width, height in ((1, 1), (2, 3), (3, 2), (4, 8), (9, 1)):
            with self.subTest(viewport=(width, height)):
                scale, ox, oy = transform(width, height)
                self.assertGreater(scale, 0)
                self.assertGreaterEqual(ox, -1e-12)
                self.assertGreaterEqual(oy, -1e-12)
                self.assertLessEqual(W * scale, width + 1e-12)
                self.assertLessEqual(H * scale, height + 1e-12)
                point = screen_to_logical(ox + 180 * scale, oy + 360 * scale, width, height)
                self.assertIsNotNone(point)
                self.assertAlmostEqual(point[0], 180, places=6)
                self.assertAlmostEqual(point[1], 360, places=6)

    def test_zero_dimensions_are_rejected(self):
        for width, height in ((0, 720), (360, 0), (0, 0), (-1, 720)):
            with self.assertRaises(ValueError):
                transform(width, height)

    def test_letterbox_is_not_clickable(self):
        for width, height in ((1272,2772),(1080,2354),(1440,2560),(240,960)):
            scale, ox, oy = transform(width, height)
            if oy > 0:
                self.assertIsNone(screen_to_logical(width/2, oy/2, width, height))
            if ox > 0:
                self.assertIsNone(screen_to_logical(ox/2, height/2, width, height))

    def test_ore_hitbox_round_trip(self):
        ore = (105,210,330,440)
        self.assertTrue(0 <= ore[0] < ore[2] < W)
        self.assertTrue(0 <= ore[1] < ore[3] < H)
        for width, height in ((360,720),(1080,2354),(1272,2772),(240,960)):
            scale, ox, oy = transform(width, height)
            cx, cy = (ore[0]+ore[2])/2, (ore[1]+ore[3])/2
            actual = screen_to_logical(ox+cx*scale, oy+cy*scale, width, height)
            self.assertAlmostEqual(actual[0], cx)
            self.assertAlmostEqual(actual[1], cy)

    def test_shop_purchase_hitboxes_do_not_overlap(self):
        rects = []
        for i in range(6):
            x, y = 10+(i%2)*175, 164+(i//2)*153
            rects.append((x+13,y+102,x+152,y+138))
        for i, a in enumerate(rects):
            self.assertLessEqual(a[2], W)
            self.assertLessEqual(a[3], H)
            for b in rects[i+1:]:
                self.assertTrue(a[2]<b[0] or b[2]<a[0] or a[3]<b[1] or b[3]<a[1])

if __name__ == "__main__":
    unittest.main()
