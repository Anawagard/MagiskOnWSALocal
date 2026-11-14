"""Adversarial source-only tests for disconnected ore alpha masks.

No Android build, APK generation or workflow execution.
Run: python3 -m unittest discover -s chatgpt-shahta-v40 -p 'test_raster_ore_connectivity_v98.py'
"""
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from test_raster_audit_contract_v711 import audit_module, fixture


class OreConnectivityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="shahta-ore-connectivity-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        fixture(self.directory)

    @staticmethod
    def textured_pixel(x, y):
        v = (x * 13 + y * 19) % 145
        return (55 + v, 45 + v, 35 + v, 255)

    def test_disconnected_debris_with_valid_coverage_is_rejected(self):
        """Enough textured area, a solid center, and broad bounds must not hide debris."""
        im = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        # Central body: 120x120, connected and containing the image center.
        for y in range(90, 210):
            for x in range(90, 210):
                im.putpixel((x, y), self.textured_pixel(x, y))
        # Isolated opaque points on a 3-pixel grid outside the central body.
        # They cannot connect to each other or to the body by 4-neighbour edges.
        for y in range(18, 282, 3):
            for x in range(18, 282, 3):
                if 88 <= x <= 211 and 88 <= y <= 211:
                    continue
                im.putpixel((x, y), self.textured_pixel(x, y))
        im.save(self.directory / "ore_23.png")
        with self.assertRaisesRegex(RuntimeError, "disconnected opaque fragments"):
            audit_module.audit(self.directory)

    def test_connected_textured_body_is_accepted(self):
        """A contiguous silhouette with texture and clear margins remains valid."""
        im = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
        for y in range(65, 235):
            for x in range(65, 235):
                # Diamond-like silhouette: connected under 4-neighbour adjacency.
                if abs(x - 150) + abs(y - 150) <= 83:
                    im.putpixel((x, y), self.textured_pixel(x, y))
        im.save(self.directory / "ore_23.png")
        audit_module.audit(self.directory)


if __name__ == "__main__":
    unittest.main()
