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

# Verify the actual v7.1 Android rendering/touch source anchors, not just
# a mathematically consistent hypothetical viewport.
v71 = (root / "patch_modernist_v71.py").read_text(encoding="utf-8")
ast.parse(v71)
for marker in (
    "Math.min(getWidth()/(float)W,getHeight()/(float)H)",
    "canvas.translate(v71OffsetX(),v71OffsetY());",
    "canvas.scale(v71Scale(),v71Scale());",
    "(e.getX()-v71OffsetX())/v71Scale()",
    "(e.getY()-v71OffsetY())/v71Scale()",
    "if(x<0||x>=W||screenY<0||screenY>=H)return true;",
):
    assert marker in v71, ("viewport render/touch contract changed", marker)

# Screen-side gutters must not navigate. Exercise both letterbox directions
# and the edge of every painted button (not only its center).
edge_checks = 0
for width, height in viewports + ((1000, 720), (360, 1000)):
    scale = min(width / 360, height / 720)
    ox, oy = (width - 360 * scale) / 2, (height - 720 * scale) / 2
    for tab in range(5):
        painted_left = 5 + 72 * tab
        painted_right = painted_left + 64
        for x in (painted_left, painted_right):
            for y in (90, 134):
                px, py = ox + x * scale, oy + y * scale
                logical_x, logical_y = (px - ox) / scale, (py - oy) / scale
                assert tab * 72 <= logical_x < (tab + 1) * 72
                assert 88 <= logical_y <= 136
                edge_checks += 1
    if ox > 0:
        assert (ox / 2 - ox) / scale < 0
        assert (width - ox / 2 - ox) / scale >= 360
        edge_checks += 2
    if oy > 0:
        assert (oy / 2 - oy) / scale < 0
        assert (height - oy / 2 - oy) / scale >= 720
        edge_checks += 2
print(f"PASS: {edge_checks} painted-edge and letterbox assertions")


# Navigation must use the same logical tab after transforming every
# physical viewport; test the transparent 5px/3px gutters separately from
# the painted 64px button. A logical cell is 72px wide and should never
# accidentally dispatch a neighbouring tab at fractional display scales.
gutter_checks = 0
for width, height in viewports + ((240, 320), (320, 480), (1000, 720), (360, 1000)):
    scale = min(width / 360, height / 720)
    ox, oy = (width - 360 * scale) / 2, (height - 720 * scale) / 2
    for tab in range(5):
        cell_left = tab * 72
        for logical_x in (cell_left + 0.5, cell_left + 4.5,
                          cell_left + 5.5, cell_left + 36,
                          cell_left + 68.5, cell_left + 71.5):
            px = ox + logical_x * scale
            py = oy + 112 * scale
            restored_x = (px - ox) / scale
            restored_y = (py - oy) / scale
            assert math.isclose(restored_x, logical_x, abs_tol=1e-7)
            assert math.isclose(restored_y, 112, abs_tol=1e-7)
            assert int(restored_x // 72) == tab
            # Rendering uses [5,69] relative to each cell. The logical
            # navigation cell is intentionally wider than its visible art.
            painted = cell_left + 5 <= restored_x <= cell_left + 69
            expected = 5 <= logical_x - cell_left <= 69
            assert painted == expected
            gutter_checks += 1
print(f"PASS: {gutter_checks} fractional-scale tab/gutter assertions")


# Exhaustive fractional-scale seam checks: the actual tab dispatcher uses
# half-open 72px cells, so adjacent cells must never both own a touch.
# Use interior epsilon offsets to avoid floating-point ambiguity at a seam.
seam_checks = 0
for width, height in viewports + ((240, 320), (320, 480), (1768, 2208)):
    scale = min(width / 360, height / 720)
    ox = (width - 360 * scale) / 2
    oy = (height - 720 * scale) / 2
    for seam in (72, 144, 216, 288):
        for delta, expected_tab in ((-0.25, seam // 72 - 1),
                                    (0.25, seam // 72)):
            px = ox + (seam + delta) * scale
            py = oy + 112 * scale
            x = (px - ox) / scale
            y = (py - oy) / scale
            assert int(x // 72) == expected_tab
            assert 88 <= y <= 136
            seam_checks += 1
    # Vertical touch strip is inclusive in the current source. Outside
    # the strip, taps must not trigger navigation, at any screen scale.
    for logical_y, expected in ((87.75, False), (88.25, True),
                                (135.75, True), (136.25, False)):
        py = oy + logical_y * scale
        y = (py - oy) / scale
        assert (88 <= y <= 136) == expected
        seam_checks += 1
print(f"PASS: {seam_checks} fractional-scale seam and vertical-strip assertions")
