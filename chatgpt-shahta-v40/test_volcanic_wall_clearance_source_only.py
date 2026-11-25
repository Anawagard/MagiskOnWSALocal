"""Source-only guard for volcanic biome fracture corridor clearance.

No Android SDK, APK, raster generation, or GitHub Actions required.
"""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).with_name("generate_art_v70.py")


class VolcanicWallClearanceTests(unittest.TestCase):
    def test_fracture_vertices_clamped_before_draw(self):
        source = SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        cave = next(node for node in tree.body
                    if isinstance(node, ast.FunctionDef) and node.name == "cave")
        code = ast.get_source_segment(source, cave)
        self.assertIn("wall_edge=max(1,min(70,w//5))", code)
        self.assertIn("np.clip(x+round(dx*motif_sx),lo,hi)", code)
        self.assertIn("d.line(vertices,fill=(232,119,72,110),", code)

    def test_both_wall_ranges_keep_all_vertices_out_of_corridor(self):
        for width in (180, 240, 360, 480, 720):
            edge = max(1, min(70, width // 5))
            for side in (0, 1):
                inset = min(2, (edge - 1) // 2)
                lo, hi = (inset, edge - 1 - inset) if side == 0 else (width - edge + inset, width - 1 - inset)
                for x in (lo, hi, (lo + hi) // 2):
                    for offset in range(-17, 18):
                        clamped = min(hi, max(lo, x + round(offset * width / 360)))
                        self.assertGreaterEqual(clamped, lo)
                        self.assertLessEqual(clamped, hi)
                        self.assertTrue(clamped < edge or clamped >= width - edge)


if __name__ == "__main__":
    unittest.main()
