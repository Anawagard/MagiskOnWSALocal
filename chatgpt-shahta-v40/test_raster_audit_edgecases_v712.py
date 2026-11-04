"""Additional source-only adversarial tests for raster silhouette and texture checks.

No Android SDK, Gradle, or build workflow is invoked.
Run: python3 -m unittest discover -s chatgpt-shahta-v40 -p 'test_raster_audit_edgecases_v712.py'
"""
import unittest
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw

from test_raster_audit_contract_v711 import audit_module, fixture


class RasterAuditEdgeCases(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="shahta-raster-edge-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        fixture(self.root)

    def test_few_bright_speckles_do_not_mask_flat_stone(self):
        path = self.root / "ore_23.png"
        im = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        draw = ImageDraw.Draw(im)
        draw.ellipse((45, 45, 255, 255), fill=(105, 110, 115, 255))
        # Less than five percent of visible pixels vary. The robust
        # percentile spread should still identify a flat placeholder.
        for y in range(90, 210, 19):
            for x in range(90, 210, 19):
                im.putpixel((x, y), (245, 240, 230, 255))
        im.save(path)
        with self.assertRaisesRegex(RuntimeError, "texture"):
            audit_module.audit(self.root)

    def test_tiny_stone_silhouette_is_rejected(self):
        path = self.root / "ore_23.png"
        im = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        # Keep the center opaque and introduce strong interior variation.
        for y in range(125, 175):
            for x in range(125, 175):
                value = (x * 13 + y * 19) % 160
                im.putpixel((x, y), (50 + value, 40 + value, 30 + value, 255))
        im.save(path)
        with self.assertRaisesRegex(RuntimeError, "too few visible pixels"):
            audit_module.audit(self.root)

    def test_fully_opaque_stone_is_rejected(self):
        path = self.root / "ore_23.png"
        im = Image.new("RGBA", (300, 300))
        for y in range(300):
            for x in range(300):
                value = (x * 13 + y * 19) % 160
                im.putpixel((x, y), (50 + value, 40 + value, 30 + value, 255))
        im.save(path)
        with self.assertRaisesRegex(RuntimeError, "transparent pixels"):
            audit_module.audit(self.root)

    def test_wrong_background_encoding_is_rejected(self):
        path = self.root / "biome_23.jpg"
        with Image.open(path) as image:
            image.save(path, format="PNG")
        with self.assertRaisesRegex(RuntimeError, "Unexpected encoding"):
            audit_module.audit(self.root)


if __name__ == "__main__":
    unittest.main()
