"""Source-only geometry regression for peripheral cave motifs.

No Android build or image generation. Mirrors the four bounded drawing
ranges in generate_art_v70.py and checks stroke/ellipse extents.
"""
from pathlib import Path
import random
import unittest

SOURCE = Path(__file__).with_name("generate_art_v70.py")


class CaveMotifClearance(unittest.TestCase):
    def test_source_uses_bounded_ranges(self):
        source = SOURCE.read_text(encoding="utf-8")
        for marker in (
            "r.integers(15,60),r.integers(w-60,w-15)",
            "span=int(r.integers(34,min(70,w//5)+1))",
            "r.integers(14,59),r.integers(w-59,w-14)",
            "r.integers(16,59),r.integers(w-59,w-16)",
        ):
            self.assertIn(marker, source)

    def test_decorative_shapes_clear_center(self):
        rng = random.Random(8214)
        for width in (360, 480, 720):
            # At 360px the protected lane is x=85..275.
            left_limit = 85
            right_limit = width - 85
            for _ in range(1000):
                # Circular crystals in the index%6 branches: radius <15.
                left = rng.randrange(15, 60)
                right = rng.randrange(width - 60, width - 15)
                radius = rng.randrange(4, 15)
                self.assertLess(left + radius, left_limit)
                self.assertGreater(right - radius, right_limit)
                # Rounded nodules: radius <11.
                left = rng.randrange(14, 59)
                right = rng.randrange(width - 59, width - 14)
                radius = rng.randrange(3, 11)
                self.assertLess(left + radius, left_limit)
                self.assertGreater(right - radius, right_limit)
                # Sedimentary ledges, including stroke width=4.
                span = rng.randrange(34, min(70, width // 5) + 1)
                self.assertLess(span + 2, left_limit)
                self.assertGreater(width - span - 2, right_limit)
                # Volcanic fissures have up to 16px horizontal excursion.
                left = rng.randrange(16, 59)
                right = rng.randrange(width - 59, width - 16)
                self.assertLess(left + 16 + 2, left_limit)
                self.assertGreater(right - 16 - 2, right_limit)


if __name__ == "__main__":
    unittest.main()
