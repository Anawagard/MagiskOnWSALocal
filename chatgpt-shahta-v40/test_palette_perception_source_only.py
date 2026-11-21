"""Source-only regression tests for perceptual palette validation.

No Android restoration, image generation, APK build, or external processes.
"""
import unittest

from audit_palette_perception_source_only import (
    GRAPHITE, contrast, oklab, palettes, validate_palette,
)


class PaletteAuditTests(unittest.TestCase):
    def setUp(self):
        self.colors = [(i, 80, 160) for i in range(24)]

    def test_actual_generator_palettes(self):
        data = palettes()
        self.assertEqual(set(data), {"SCENES", "ORES"})
        for name, colors in data.items():
            validate_palette(name, colors)
            self.assertEqual(len(colors), 24)
            self.assertTrue(all(contrast(c, GRAPHITE) > 0 for c in colors))
            self.assertTrue(all(len(oklab(c)) == 3 for c in colors))

    def test_invalid_entry_types_fail_cleanly(self):
        for invalid in (None, 42, "red", (1, 2), (1, 2, 3, 4),
                        (True, 2, 3), (-1, 2, 3), (256, 2, 3),
                        (1.5, 2, 3), ([1], 2, 3)):
            with self.subTest(invalid=invalid):
                colors = self.colors.copy()
                colors[7] = invalid
                with self.assertRaises(ValueError):
                    validate_palette("ORES", colors)

    def test_duplicates_and_wrong_counts_fail(self):
        with self.assertRaises(ValueError):
            validate_palette("ORES", self.colors[:23])
        colors = self.colors.copy()
        colors[9] = colors[0]
        with self.assertRaises(ValueError):
            validate_palette("ORES", colors)

    def test_color_distance_and_contrast_invariants(self):
        black, white = (0, 0, 0), (255, 255, 255)
        self.assertAlmostEqual(contrast(black, white), 21.0, places=6)
        self.assertAlmostEqual(contrast(white, black), 21.0, places=6)
        self.assertAlmostEqual(oklab(black)[0], 0.0, places=6)
        self.assertAlmostEqual(oklab(white)[0], 1.0, places=5)


if __name__ == "__main__":
    unittest.main()
