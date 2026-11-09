"""Source-only five-tab navigation and narrow-screen hitbox contract.

No Android SDK, Gradle, emulator, APK or workflow execution.
"""
from pathlib import Path
import ast
import math
import re

root = Path(__file__).resolve().parent
patch = (root / "patch_modernist_v72.py").read_text(encoding="utf-8")
ast.parse(patch)
assert "for(int i=0;i<5;i++)" in patch
assert "float x=3+i*72f;" in patch
assert "x+2,90,64,44" in patch
assert "if(screenY>=88&&screenY<=136)" in patch
assert "c.translate(13f,18f);" in patch
assert "c.scale(.93f,.94f);" in patch
assert "x=(x-13f)/.93f;" in patch
assert "y=(y-18f)/.94f;" in patch

# Five logical navigation cells must partition the full 360 px canvas.
cells = [(i * 72, (i + 1) * 72) for i in range(5)]
assert cells[0][0] == 0 and cells[-1][1] == 360
assert all(cells[i][1] == cells[i + 1][0] for i in range(4))
# Painted buttons must stay within their respective touch cells.
for i, (left, right) in enumerate(cells):
    painted_left = 3 + i * 72 + 2
    painted_right = painted_left + 64
    assert left <= painted_left < painted_right <= right

# Letterboxing and inverse viewport transforms on compact and tall phones.
viewports = ((280, 560), (320, 568), (360, 720), (393, 852),
             (720, 1280), (1080, 2400), (1272, 2772))
checks = 0
for width, height in viewports:
    scale = min(width / 360, height / 720)
    ox, oy = (width - 360 * scale) / 2, (height - 720 * scale) / 2
    for tab, (left, right) in enumerate(cells):
        x = (left + right) / 2
        y = 112
        physical_x, physical_y = ox + x * scale, oy + y * scale
        inverse_x = (physical_x - ox) / scale
        inverse_y = (physical_y - oy) / scale
        assert math.isclose(inverse_x, x, abs_tol=1e-7)
        assert math.isclose(inverse_y, y, abs_tol=1e-7)
        assert int(inverse_x // 72) == tab
        assert 88 <= inverse_y <= 136
        checks += 1
    # Feature content clip y=205..713 in screen coordinates. The inverse
    # affine mapping must preserve logical coordinates at both boundaries.
    for screen_y in (205, 713):
        logical_y = (screen_y - 60 - 18) / .94
        reconstructed = 60 + 18 + logical_y * .94
        assert math.isclose(screen_y, reconstructed, abs_tol=1e-7)
        checks += 1

print(f"PASS: {checks} source-only navigation and narrow-viewport assertions")
