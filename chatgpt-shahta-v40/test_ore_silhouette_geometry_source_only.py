"""Source-only geometry regression for all 24 textured ore silhouettes.

No Android SDK, Gradle, APK, or third-party image libraries required.
Mirrors the contour equations in generate_art_v70.py and guards their
pixel-space bounds, non-degenerate area, and family differentiation.
"""
import math
import random
import unittest


def contour(index, perturbations):
    points = []
    for a in range(64):
        angle = a * math.tau / 64
        family = index % 4
        if family == 0:
            shape = 9 * math.cos(angle * 5 + index * .37) + 4 * math.sin(angle * 11)
            aspect = .86
        elif family == 1:
            shape = 4 * math.cos(angle * 3 + index * .41) + 3 * math.sin(angle * 9)
            aspect = .94
        elif family == 2:
            shape = 7 * math.cos(angle * 4 + index * .29) + 3 * math.sin(angle * 13)
            aspect = .72
        else:
            shape = 11 * math.cos(angle * 6 + index * .23) + 5 * math.sin(angle * 12)
            aspect = .82
        distance = min(126, max(65, 109 + perturbations[a] * .75 + shape))
        points.append((150 + math.cos(angle) * distance,
                       149 + math.sin(angle) * distance * aspect))
    return points


def area(points):
    return abs(sum(x * points[(i + 1) % len(points)][1] -
                   points[(i + 1) % len(points)][0] * y
                   for i, (x, y) in enumerate(points))) / 2


class OreSilhouetteGeometryTests(unittest.TestCase):
    def test_all_24_ores_fit_bitmap_under_extreme_noise(self):
        for index in range(24):
            for noise in (-40, 0, 40):
                with self.subTest(index=index, noise=noise):
                    vertices = contour(index, [noise] * 64)
                    self.assertEqual(len(vertices), 64)
                    self.assertTrue(all(0 <= x < 300 and 0 <= y < 300
                                        for x, y in vertices))
                    self.assertGreater(area(vertices), 9000)

    def test_four_families_are_not_identical(self):
        perturbations = [0] * 64
        shapes = [contour(index, perturbations) for index in range(4)]
        for left in range(4):
            for right in range(left + 1, 4):
                distance = sum(math.dist(a, b) for a, b in
                               zip(shapes[left], shapes[right])) / 64
                self.assertGreater(distance, 4.0)

    def test_repeated_geometry_is_deterministic(self):
        for index in range(24):
            noise = [random.Random(index * 1000 + i).uniform(-15, 15)
                     for i in range(64)]
            self.assertEqual(contour(index, noise), contour(index, noise))


if __name__ == "__main__":
    unittest.main()
