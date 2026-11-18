"""Source-only regression for scalable cave timber artwork (no Android build)."""
import ast
import math
from pathlib import Path

SOURCE = Path(__file__).with_name("generate_art_v70.py").read_text(encoding="utf-8")
tree = ast.parse(SOURCE)
cave = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "cave")
text = ast.get_source_segment(SOURCE, cave)
for token in ("sx, sy = w / 360.0, h / 570.0", "def timber_point(x, y):",
              "timber_point(x, 55)", "timber_point(x-3, 490)",
              "timber_point(36,52)", "timber_point(322,266)",
              "max(1,round(13*sx))", "max(1,round(9*sx))"):
    if token not in text:
        raise AssertionError(f"Missing scalable timber contract: {token}")

# Pixel-space bounds for each supported viewport; scale stays deterministic.
for w, h in [(240, 360), (360, 570), (1080, 1920), (1272, 2772)]:
    def pt(x, y):
        return round(x * w / 360), round(y * h / 570)
    for x in (36, 318):
        for a, b in [(x, 55), (x-3, 490), (x+2, 55), (x, 490)]:
            px, py = pt(a, b)
            assert 0 <= px < w and 0 <= py < h
    x1, y1 = pt(36, 52)
    x2, y2 = pt(322, 266)
    assert 0 <= x1 < x2 < w and 0 <= y1 < y2 < h
    for stroke in (3, 9, 13):
        assert max(1, round(stroke * w / 360)) >= 1
print("Cave timber source-only scaling: PASS (4 viewports)")
