"""Source-only checks for coverage and weak-region ore visibility metrics."""
import unittest
import numpy as np
from PIL import Image
from audit_ore_biome_composites_source_only import visibility_details, SAMPLE_SIZE


class VisibilityDetailsTests(unittest.TestCase):
    def test_uniform_opaque_ore(self):
        bg = Image.new("RGB", (SAMPLE_SIZE, SAMPLE_SIZE), (0, 0, 0))
        fg = Image.new("RGBA", (SAMPLE_SIZE, SAMPLE_SIZE), (255, 255, 255, 255))
        result = visibility_details(bg, fg)
        self.assertEqual(result["visible_coverage"], 1.0)
        self.assertEqual(result["weakest_decile"], 1.0)

    def test_weak_region_is_not_hidden_by_bright_average(self):
        bg = Image.new("RGB", (SAMPLE_SIZE, SAMPLE_SIZE), (0, 0, 0))
        data = np.full((SAMPLE_SIZE, SAMPLE_SIZE, 4), 255, dtype=np.uint8)
        data[:SAMPLE_SIZE // 4, :, :3] = 0
        result = visibility_details(bg, Image.fromarray(data, mode="RGBA"))
        self.assertEqual(result["visible_coverage"], 1.0)
        self.assertEqual(result["weakest_decile"], 0.0)

    def test_transparent_pixels_do_not_pollute_weak_decile(self):
        bg = Image.new("RGB", (SAMPLE_SIZE, SAMPLE_SIZE), (0, 0, 0))
        data = np.zeros((SAMPLE_SIZE, SAMPLE_SIZE, 4), dtype=np.uint8)
        data[:SAMPLE_SIZE // 2, :, :] = 255
        result = visibility_details(bg, Image.fromarray(data, mode="RGBA"))
        self.assertEqual(result["visible_coverage"], 0.5)
        self.assertEqual(result["weakest_decile"], 1.0)

    def test_empty_sprite_rejected(self):
        bg = Image.new("RGB", (SAMPLE_SIZE, SAMPLE_SIZE), (0, 0, 0))
        fg = Image.new("RGBA", (SAMPLE_SIZE, SAMPLE_SIZE), (255, 255, 255, 0))
        with self.assertRaisesRegex(ValueError, "empty ore"):
            visibility_details(bg, fg)

    def test_mismatched_sizes_rejected(self):
        bg = Image.new("RGB", (SAMPLE_SIZE, SAMPLE_SIZE), (0, 0, 0))
        fg = Image.new("RGBA", (SAMPLE_SIZE - 1, SAMPLE_SIZE), (255, 255, 255, 255))
        with self.assertRaisesRegex(ValueError, "matching"):
            visibility_details(bg, fg)


if __name__ == "__main__":
    unittest.main()
