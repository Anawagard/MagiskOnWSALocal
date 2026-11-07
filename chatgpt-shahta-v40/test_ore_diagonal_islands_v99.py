"""Source-only regression: diagonal pixels do not join a 4-connected ore body.

Run: python3 -m unittest discover -s chatgpt-shahta-v40 -p 'test_ore_diagonal_islands_v99.py'
No Gradle, emulator, APK or Actions invocation.
"""
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from test_raster_audit_contract_v711 import audit_module, fixture


class DiagonalOreIslandTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="shahta-diagonal-ore-")
        self.addCleanup(temp.cleanup)
        self.directory = Path(temp.name)
        fixture(self.directory)

    @staticmethod
    def pigment(x, y):
        shade = (x * 17 + y * 23) % 130
        return (60 + shade, 48 + shade, 35 + shade, 255)

    def test_diagonally_touching_islands_are_not_one_silhouette(self):
        image = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        # Centered 110x110 block (12,100 opaque pixels).
        for y in range(95, 205):
            for x in range(95, 205):
                image.putpixel((x, y), self.pigment(x, y))
        # A diagonally adjacent 55x55 block (3,025 opaque pixels):
        # (204,204) and (205,205) touch at a corner only.
        for y in range(205, 260):
            for x in range(205, 260):
                image.putpixel((x, y), self.pigment(x, y))
        image.save(self.directory / "ore_23.png")
        with self.assertRaisesRegex(RuntimeError, "disconnected opaque fragments"):
            audit_module.audit(self.directory)

    def test_one_pixel_cardinal_bridge_joins_islands(self):
        image = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        for y in range(95, 205):
            for x in range(95, 205):
                image.putpixel((x, y), self.pigment(x, y))
        for y in range(205, 260):
            for x in range(205, 260):
                image.putpixel((x, y), self.pigment(x, y))
        # This pixel connects to (204,204) and (205,205) by shared edges.
        image.putpixel((205, 204), self.pigment(205, 204))
        image.save(self.directory / "ore_23.png")
        audit_module.audit(self.directory)


if __name__ == "__main__":
    unittest.main()
