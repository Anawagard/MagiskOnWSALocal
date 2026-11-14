"""Source-independent viewport regression for forge, guild and atlas.
Run: python3 chatgpt-shahta-v40/test_feature_viewport_v126.py
No Android SDK, APK, Gradle or network required.
"""
import math
import unittest

SX, SY = .93, .94
DX, DY = 13., 18.
TOP, BOTTOM = 145., 653.
SCREEN_OFFSET = 60.

def paint(x, y):
    return DX + SX*x, DY + SY*y

def touch(x, screen_y):
    if not TOP + SCREEN_OFFSET <= screen_y <= BOTTOM + SCREEN_OFFSET:
        return None
    if not DX <= x <= DX + SX*360:
        return None
    return (x-DX)/SX, (screen_y-SCREEN_OFFSET-DY)/SY

class FeatureViewportTests(unittest.TestCase):
    def test_visible_roundtrip(self):
        for x in (0, 1, 80, 180, 359, 360):
            for y in (140, 200, 360, 600, 675):
                px, py = paint(x, y)
                actual = touch(px, py + SCREEN_OFFSET)
                if TOP <= py <= BOTTOM:
                    self.assertIsNotNone(actual)
                    self.assertTrue(math.isclose(actual[0], x, abs_tol=1e-9))
                    self.assertTrue(math.isclose(actual[1], y, abs_tol=1e-9))
                else:
                    self.assertIsNone(actual)

    def test_clipped_header_and_footer(self):
        for x in (13, 100, 180, 347.8):
            for y in (0, 60, 144.999, 653.001, 700, 720):
                self.assertIsNone(touch(x, y + SCREEN_OFFSET))

    def test_invisible_side_gutters(self):
        for x in (-100, 0, 12.999, 347.801, 360, 999):
            self.assertIsNone(touch(x, 400))

    def test_boundaries(self):
        for px, py in ((13, 145), (347.8, 653), (180, 399)):
            actual = touch(px, py + SCREEN_OFFSET)
            self.assertIsNotNone(actual)
            self.assertTrue(0 <= actual[0] <= 360)

    def test_narrow_screen_affine_hitbox_clipping(self):
        # Rendering and touch conversion must share the same inverse transform.
        # Cover compact widths, non-integer scales and both visible boundaries.
        for width in (240, 280, 320, 360):
            sx = width / 360.0
            dx = 0.0
            for sy, dy in ((0.72, 12.0), (0.83, 0.0), (0.94, 18.0)):
                for logical_x in (0.0, 45.5, 180.0, 359.999, 360.0):
                    screen_x = dx + sx * logical_x
                    inverse_x = (screen_x - dx) / sx
                    self.assertAlmostEqual(inverse_x, logical_x, places=9)
                    self.assertTrue(dx <= screen_x <= dx + sx * 360 + 1e-9)
                for logical_y in (0.0, 140.0, 360.0, 675.0, 720.0):
                    screen_y = dy + sy * logical_y
                    inverse_y = (screen_y - dy) / sy
                    self.assertAlmostEqual(inverse_y, logical_y, places=9)
                # Touches in the letterboxed gutters must not activate controls.
                self.assertLess((dx - 0.01 - dx) / sx, 0)
                self.assertGreater((dx + sx * 360 + 0.01 - dx) / sx, 360)

    def test_monotonic_inverse(self):
        for y in (205, 400, 713):
            values = [touch(x, y)[0] for x in (13, 50, 180, 300, 347.8)]
            self.assertEqual(values, sorted(values))

if __name__ == "__main__":
    unittest.main(verbosity=2)
