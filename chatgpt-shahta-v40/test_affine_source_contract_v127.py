"""Source-only regression: v7.1 renderer and touch must use identical viewport math.

Run: python3 chatgpt-shahta-v40/test_affine_source_contract_v127.py
Does not invoke Android, Gradle, APK or Actions.
"""
from pathlib import Path
import math
import unittest

PATCH = Path(__file__).with_name("patch_modernist_v71.py").read_text(encoding="utf-8")

class AffineSourceContractTests(unittest.TestCase):
    def test_actual_java_render_and_touch_anchors(self):
        required = (
            "Math.min(getWidth()/(float)W,getHeight()/(float)H)",
            "canvas.translate(v71OffsetX(),v71OffsetY());",
            "canvas.scale(v71Scale(),v71Scale());",
            "float x=(e.getX()-v71OffsetX())/v71Scale();",
            "float screenY=(e.getY()-v71OffsetY())/v71Scale();",
            "if(x<0||x>=W||screenY<0||screenY>=H)return true;",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, PATCH)

    def test_realistic_aspect_ratios_and_gutters(self):
        # Independent reference model of the Java affine mapping.
        for width, height in ((240, 960), (280, 560), (320, 720),
                              (360, 720), (1080, 2354), (1272, 2772),
                              (1440, 2560), (720, 1600)):
            scale = max(.01, min(width / 360, height / 720))
            ox = (width - 360 * scale) / 2
            oy = (height - 720 * scale) / 2
            self.assertGreater(scale, 0)
            self.assertGreaterEqual(ox, -1e-8)
            self.assertGreaterEqual(oy, -1e-8)
            for x, y in ((0, 0), (180, 360), (359.99, 719.99),
                         (105, 210), (330, 440)):
                px, py = ox + scale*x, oy + scale*y
                self.assertTrue(math.isclose((px-ox)/scale, x, abs_tol=1e-7))
                self.assertTrue(math.isclose((py-oy)/scale, y, abs_tol=1e-7))
            for px, py in ((ox-.01, height/2), (ox+360*scale+.01, height/2),
                           (width/2, oy-.01), (width/2, oy+720*scale+.01)):
                lx, ly = (px-ox)/scale, (py-oy)/scale
                self.assertTrue(lx < 0 or lx >= 360 or ly < 0 or ly >= 720)

if __name__ == "__main__":
    unittest.main(verbosity=2)
