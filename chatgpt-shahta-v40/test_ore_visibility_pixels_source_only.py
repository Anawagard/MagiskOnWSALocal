"""Source-only regression tests for raster ore visibility diagnostics.

Run: python -m unittest test_ore_visibility_pixels_source_only.py
Requires numpy and Pillow; does not build or modify Android sources.
"""
import unittest

import numpy as np
from PIL import Image

from audit_ore_biome_composites_source_only import contrast_score, SAMPLE_SIZE


def background(rgb):
    return Image.new("RGB", (SAMPLE_SIZE, SAMPLE_SIZE), rgb)


def ore(rgb, alpha):
    return Image.new("RGBA", (SAMPLE_SIZE, SAMPLE_SIZE), (*rgb, alpha))


class OreVisibilityPixelTests(unittest.TestCase):
    def test_identical_opaque_pixels_have_zero_contrast(self):
        self.assertAlmostEqual(contrast_score(background((20, 40, 60)),
                                              ore((20, 40, 60), 255)), 0.0)

    def test_opposite_opaque_pixels_have_unit_contrast(self):
        self.assertAlmostEqual(contrast_score(background((0, 0, 0)),
                                              ore((255, 255, 255), 255)), 1.0)

    def test_half_alpha_scales_displayed_difference(self):
        score = contrast_score(background((0, 0, 0)),
                               ore((255, 255, 255), 128))
        self.assertAlmostEqual(score, 128 / 255, places=6)

    def test_invisible_ore_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "empty ore"):
            contrast_score(background((0, 0, 0)),
                           ore((255, 255, 255), 0))

    def test_transparent_rgb_does_not_affect_result(self):
        data = np.zeros((SAMPLE_SIZE, SAMPLE_SIZE, 4), dtype=np.uint8)
        data[:, :, :3] = 255
        data[:, :, 3] = 0
        data[0, 0, :3] = (128, 128, 128)
        data[0, 0, 3] = 255
        score = contrast_score(background((0, 0, 0)),
                               Image.fromarray(data, mode="RGBA"))
        self.assertAlmostEqual(score, 128 / 255, places=6)

    def test_partially_transparent_pixels_are_counted(self):
        data = np.zeros((SAMPLE_SIZE, SAMPLE_SIZE, 4), dtype=np.uint8)
        data[0, 0] = (255, 255, 255, 1)
        with self.assertRaisesRegex(ValueError, "empty ore"):
            contrast_score(background((0, 0, 0)),
                           Image.fromarray(data, mode="RGBA"))
        data[0, 0, 3] = 2
        score = contrast_score(background((0, 0, 0)),
                               Image.fromarray(data, mode="RGBA"))
        self.assertAlmostEqual(score, 2 / 255, places=6)


if __name__ == "__main__":
    unittest.main()
