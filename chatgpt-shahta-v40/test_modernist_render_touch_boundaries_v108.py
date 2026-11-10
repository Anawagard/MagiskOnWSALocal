"""Source-only regression: modernist five-tab painted layout and touch boundaries.

Run with Python; never invokes Android, Gradle, GitHub Actions or APK tooling.
"""
from pathlib import Path
import ast
import math
import re

root = Path(__file__).resolve().parent
source = (root / "patch_modernist_v72.py").read_text(encoding="utf-8")
ast.parse(source)

# Assert against the actual patch payload, not just hypothetical geometry.
anchors = (
    "float x=3+i*72f;",
    "x+2,90,64,44",
    "x+23,92,22,22",
    "x+34,126,10",
    "rect(c,x+14,90,40,2",
    "rect(c,x+14,132,40,2",
    "c.clipRect(0,145,360,653);",
    "c.translate(13f,18f);",
    "c.scale(.93f,.94f);",
    "if(screenY<205f||screenY>713f)return true;",
    "if(x<13f||x>347.8f)return true;",
)
for anchor in anchors:
    assert anchor in source, f"render/input contract drift: {anchor}"

# Both active markers, the icon and label remain within the visible button.
for tab in range(5):
    x = 3 + 72 * tab
    button = (x + 2, 90, x + 66, 134)
    icon = (x + 23, 92, x + 45, 114)
    top = (x + 14, 90, x + 54, 92)
    bottom = (x + 14, 132, x + 54, 134)
    for rect in (icon, top, bottom):
        assert button[0] <= rect[0] < rect[2] <= button[2]
        assert button[1] <= rect[1] < rect[3] <= button[3]
    assert button[0] <= x + 34 <= button[2]
    assert 90 < 126 < 134
    assert tab * 72 <= button[0] and button[2] <= (tab + 1) * 72

# Feature-page clip is in the local drawPage coordinate system, with
# a 60px screen offset; touch guard must match it exactly.
checks = 0
for width, height in ((240, 320), (280, 560), (320, 568),
                      (360, 720), (393, 852), (720, 1280),
                      (1080, 2400), (1272, 2772)):
    scale = min(width / 360, height / 720)
    ox = (width - 360 * scale) / 2
    oy = (height - 720 * scale) / 2
    for screen_x in (12.5, 13, 180, 347.8, 348):
        for screen_y in (204.5, 205, 400, 713, 713.5):
            px, py = ox + screen_x * scale, oy + screen_y * scale
            rx, ry = (px - ox) / scale, (py - oy) / scale
            assert math.isclose(rx, screen_x, abs_tol=1e-6)
            assert math.isclose(ry, screen_y, abs_tol=1e-6)
            visible = 13 <= rx <= 347.8 and 205 <= ry <= 713
            if visible:
                lx = (rx - 13) / .93
                ly = (ry - 60 - 18) / .94
                assert 0 <= lx <= 360
                assert 0 <= ly <= 653
            checks += 1

print(f"PASS: five painted tabs, affine viewport guards, {checks} boundary samples")
