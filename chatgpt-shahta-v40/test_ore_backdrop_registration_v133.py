"""Source-only regression for exact ore/biome viewport registration.

The Java renderer draws biome at (0,87,360,566) and ore at
(105,210,225,230), both inside the same translated page canvas.
No Android build, SDK, workflow or game state is used.
"""
import ast
from pathlib import Path
import unittest

from PIL import Image
from audit_ore_biome_composites_source_only import (
    BACKGROUND_SIZE, BIOME_DEST, ORE_DEST, ore_backdrop,
)

HERE = Path(__file__).resolve().parent


class BackdropRegistrationTests(unittest.TestCase):
    def test_source_rectangles_match_actual_java_patches(self):
        java = (HERE / "patch_full_redesign_v70.py").read_text(encoding="utf-8")
        mine = (HERE / "patch_modernist_v71.py").read_text(encoding="utf-8")
        audit = (HERE / "audit_ore_biome_composites_source_only.py").read_text(encoding="utf-8")
        for path in ("patch_full_redesign_v70.py", "patch_modernist_v71.py",
                     "audit_ore_biome_composites_source_only.py"):
            ast.parse((HERE / path).read_text(encoding="utf-8"), filename=path)
        self.assertEqual(BIOME_DEST, (0, 87, 360, 566))
        self.assertEqual(ORE_DEST, (105, 210, 225, 230))
        self.assertIn('0,87,360,566,255);', java)
        self.assertIn('105,210,225,230,255);', mine)
        self.assertIn('scenes.append(ore_backdrop(scene))', audit)
        self.assertIn('background = ore_backdrop(scene, sample_size=tile)', audit)

    def test_sampled_backdrop_tracks_real_ore_position(self):
        # Make every source x unique, so a wrong left edge is detected.
        image = Image.new("RGB", BACKGROUND_SIZE)
        pixels = image.load()
        for y in range(image.height):
            for x in range(image.width):
                pixels[x, y] = (x // 2, y // 3, 0)
        for size in (48, 96, 128):
            with self.subTest(size=size):
                sample = ore_backdrop(image, sample_size=size)
                self.assertEqual(sample.size, (size, size))
                left, top = sample.getpixel((0, 0))[:2]
                right, bottom = sample.getpixel((size-1, size-1))[:2]
                self.assertAlmostEqual(left, 105//2, delta=2)
                self.assertAlmostEqual(right, 330//2, delta=2)
                source_top = (210-87)*570/566
                source_bottom = (440-87)*570/566
                self.assertAlmostEqual(top, source_top/3, delta=2)
                self.assertAlmostEqual(bottom, source_bottom/3, delta=2)

    def test_rejects_unexpected_background_dimensions(self):
        with self.assertRaisesRegex(ValueError, "Expected biome size"):
            ore_backdrop(Image.new("RGB", (96, 96)))


if __name__ == "__main__":
    unittest.main()
