"""Source-only deterministic pointer fuzz for five modernist navigation cells.

Checks actual Java patch anchors and rejects transparent gutters and letterbox
touches. No Android SDK, Gradle, APK, or Actions required.
"""
from pathlib import Path
import ast
import math
import random

ROOT = Path(__file__).resolve().parent
V70 = (ROOT / "patch_full_redesign_v70.py").read_text(encoding="utf-8")
V71 = (ROOT / "patch_modernist_v71.py").read_text(encoding="utf-8")
V72 = (ROOT / "patch_modernist_v72.py").read_text(encoding="utf-8")
for src in (V70, V71, V72):
    ast.parse(src)

def verify_source(v70, v71, v72):
    required = (
        (v70, "float tabX=x-next*72f;"),
        (v70, "if(screenY<90f||screenY>134f||tabX<5f||tabX>69f)"),
        (v71, "(e.getX()-v71OffsetX())/v71Scale()"),
        (v71, "(e.getY()-v71OffsetY())/v71Scale()"),
        (v71, "if(x<0||x>=W||screenY<0||screenY>=H)return true;"),
        (v72, "float x=3+i*72f;"),
        (v72, "x+2,90,64,44"),
    )
    for source, marker in required:
        assert source.count(marker) == 1, ("navigation source drift", marker)

verify_source(V70, V71, V72)
for mutated in (
    (V70.replace("tabX<5f", "tabX<3f", 1), V71, V72),
    (V70, V71.replace("e.getX()-v71OffsetX()", "e.getX()", 1), V72),
    (V70, V71, V72.replace("x+2,90,64,44", "x+2,90,68,44", 1)),
):
    try:
        verify_source(*mutated)
    except AssertionError:
        pass
    else:
        raise AssertionError("Mutated render/touch contract accepted")

def target(x, y):
    if not (0 <= x < 360 and 0 <= y < 720):
        return None
    if not (90 <= y <= 134):
        return None
    tab = min(4, int(x // 72))
    local = x - tab * 72
    return tab if 5 <= local <= 69 else None

rng = random.Random(139)
viewports = (
    (176, 320), (200, 400), (240, 1080), (280, 560),
    (320, 568), (360, 720), (393, 852), (720, 1280),
    (1080, 2400), (1272, 2772), (1440, 320), (2560, 720),
)
checks = 0
for width, height in viewports:
    scale = min(width / 360, height / 720)
    ox, oy = (width - 360 * scale) / 2, (height - 720 * scale) / 2
    assert scale > 0
    for _ in range(1000):
        logical_x = rng.uniform(-12, 372)
        logical_y = rng.uniform(78, 146)
        px, py = ox + logical_x * scale, oy + logical_y * scale
        restored_x, restored_y = (px - ox) / scale, (py - oy) / scale
        assert math.isclose(restored_x, logical_x, abs_tol=1e-8)
        assert math.isclose(restored_y, logical_y, abs_tol=1e-8)
        assert target(restored_x, restored_y) == target(logical_x, logical_y)
        checks += 1
    # Screen-space letterbox gutters must be rejected even when y hits nav.
    if ox > 0:
        for px in (0, ox / 2, width - ox / 2, width):
            assert target((px - ox) / scale, 112) is None
            checks += 1
    if oy > 0:
        for py in (0, oy / 2, height - oy / 2, height):
            assert target(180, (py - oy) / scale) is None
            checks += 1
    # Boundary probes must be just inside/outside painted targets.
    for tab in range(5):
        for local, inside in ((4.75, False), (5.25, True),
                              (68.75, True), (69.25, False)):
            assert (target(tab * 72 + local, 112) == tab) == inside
            checks += 1

print(f"PASS: {checks} deterministic navigation/letterbox pointer assertions")


# Exhaustive quarter-pixel sweep across all five navigation cells.
# This catches narrow transparent seams that random sampling can miss.
grid_checks = 0
for quarter_x in range(360 * 4):
    x = quarter_x / 4
    tab = int(x // 72)
    local = x - tab * 72
    expected = tab if 5 <= local <= 69 else None
    for y in (89.75, 90, 90.25, 112, 133.75, 134, 134.25):
        expected_at_y = expected if 90 <= y <= 134 else None
        assert target(x, y) == expected_at_y, (x, y, expected_at_y)
        grid_checks += 1

# Painted cells are x=5..69 in each 72-unit slot. The logical
# viewport boundary at x=360 must never wrap into the final cell.
for x in (-0.01, 0, 4.99, 5, 69, 69.01, 71.99,
          72, 76.99, 77, 141, 141.01, 359.99, 360, 360.01):
    for y in (89.99, 90, 134, 134.01):
        expected = None
        if 0 <= x < 360 and 90 <= y <= 134:
            slot = min(4, int(x // 72))
            local = x - slot * 72
            if 5 <= local <= 69:
                expected = slot
        assert target(x, y) == expected, (x, y, expected)
        grid_checks += 1

print(f"PASS: {grid_checks} exhaustive quarter-pixel navigation seam checks")
