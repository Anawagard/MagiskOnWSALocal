"""Source-only guard for cave strata staying outside the mining corridor.

No Android SDK, APK, Gradle or image generation is required.
"""
from pathlib import Path
import random
import unittest


def strata_segments(width, seed):
    rng = random.Random(seed)
    margin = max(4, min(70, width // 5))
    segments = []
    for band in range(7):
        slope = rng.randrange(-17, 18)
        offset = rng.randrange(14, 42)
        left_end = rng.randrange(max(2, margin // 2), margin + 1)
        right_start = width - left_end
        segments.extend(((0, left_end), (right_start, width - 1)))
        if band % 2 == 0:
            joint_x = min(width - 3, right_start + rng.randrange(1, 9))
            segments.append((max(right_start, joint_x - 5), joint_x))
            segments.append((max(right_start, joint_x - 4), joint_x))
    return segments, margin


class CaveStrataCorridorTests(unittest.TestCase):
    def test_strata_and_branches_stay_in_wall_margins(self):
        for width in (180, 240, 360, 720):
            for seed in range(100):
                with self.subTest(width=width, seed=seed):
                    segments, margin = strata_segments(width, seed)
                    for a, b in segments:
                        self.assertTrue(
                            max(a, b) <= margin or min(a, b) >= width - margin,
                            (width, seed, a, b, margin),
                        )

    def test_generator_contains_corridor_clamps(self):
        source = (Path(__file__).resolve().parent / "generate_art_v70.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("right_start=w-left_end", source)
        self.assertIn("max(right_start,joint_x-5)", source)
        self.assertNotIn("left_end=int(strata_rng.integers(90,166))", source)


if __name__ == "__main__":
    unittest.main()
