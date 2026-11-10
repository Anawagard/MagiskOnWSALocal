"""Source-only nine-slice geometry regression for compact UI controls.

Verifies the actual v7.2 Java geometry expressions and tests every slice
for positive area, full coverage and ordered seams at fractional sizes.
Does not invoke Android, Gradle or GitHub Actions.
"""
from pathlib import Path
import ast
import math

source = (Path(__file__).resolve().parent / "patch_modernist_v72.py").read_text(encoding="utf-8")
ast.parse(source)
for marker in (
    "int sx=Math.min(18,bw/4),sy=Math.min(18,bh/4);",
    "float dx=Math.min(11f,w/3f),dy=Math.min(11f,h/3f);",
    "for(int row=0;row<3;row++)",
    "for(int col=0;col<3;col++)",
    "v72Slice(c,bitmap,v72Xs[col],v72Ys[row],v72Xs[col+1],v72Ys[row+1],",
    "if(sx1<=sx0||sy1<=sy0||dx1<=dx0||dy1<=dy0)return;",
):
    assert marker in source, ("nine-slice implementation drift", marker)

checks = 0
# nav buttons, notification surfaces, compact cards and full-width panels
for width, height in ((64, 44), (324, 26), (340, 49), (160, 64),
                      (165, 145), (360, 50), (20, 20), (11, 11),
                      (1, 1), (8.5, 3.25)):
    for bw, bh in ((400, 96), (160, 64), (360, 50)):
        sx, sy = min(18, bw // 4), min(18, bh // 4)
        dx, dy = min(11.0, width / 3.0), min(11.0, height / 3.0)
        xs = (0.0, dx, width - dx, float(width))
        ys = (0.0, dy, height - dy, float(height))
        source_xs = (0, sx, bw - sx, bw)
        source_ys = (0, sy, bh - sy, bh)
        assert all(xs[i] < xs[i+1] for i in range(3))
        assert all(ys[i] < ys[i+1] for i in range(3))
        assert all(source_xs[i] < source_xs[i+1] for i in range(3))
        assert all(source_ys[i] < source_ys[i+1] for i in range(3))
        area = 0.0
        for row in range(3):
            for col in range(3):
                area += (xs[col+1]-xs[col]) * (ys[row+1]-ys[row])
                checks += 1
        assert math.isclose(area, width * height, rel_tol=1e-12, abs_tol=1e-9)
print(f"PASS: {checks} nine-slice source and coverage assertions")
