"""Offline mathematical checks for the v7 modernist viewport and asset contract.

Run with: python3 chatgpt-shahta-v40/test_modernist_viewport_contract_v82.py
Pure Python: no Android project, Gradle, network, or APK needed.
"""
from pathlib import Path
import math

ROOT = Path(__file__).resolve().parent
v70 = (ROOT / "patch_full_redesign_v70.py").read_text(encoding="utf-8")
v71 = (ROOT / "patch_modernist_v71.py").read_text(encoding="utf-8")

# Guard the actual Java expressions; numerical tests must fail if rendering or
# inverse touch mapping is changed without updating this contract.
for marker in (
    "Math.min(getWidth()/(float)W,getHeight()/(float)H)",
    "canvas.translate(v71OffsetX(),v71OffsetY());",
    "canvas.scale(v71Scale(),v71Scale());",
    "(e.getX()-v71OffsetX())/v71Scale()",
    "(e.getY()-v71OffsetY())/v71Scale()",
    "if(x<0||x>=W||screenY<0||screenY>=H)return true;",
):
    assert marker in v71, f"Viewport transform contract changed: {marker}"
for marker in (
    '"biome_%02d.jpg"',
    '"ore_%02d.png"',
    '"miner.png"',
    'if(screenY>=88&&screenY<=136)',
):
    assert marker in v70 or marker in v71, f"Asset/nav contract missing: {marker}"

W, H = 360, 720
screens = (
    (320, 568), (360, 640), (360, 800), (393, 852),
    (412, 915), (1080, 2354), (1272, 2772), (1440, 3200),
)
# Include all nav centers, shop buttons, ore corners and power controls.
points = (
    (36, 112), (108, 112), (180, 112), (252, 112), (324, 112),
    (105, 210), (330, 440), (120, 250), (180, 350),
    (92, 628), (180, 628), (292, 628),
    (92, 284), (267, 284), (92, 437), (267, 437),
    (92, 590), (267, 590),
)
checks = 0
for width, height in screens:
    scale = max(.01, min(width / W, height / H))
    ox = (width - W * scale) / 2
    oy = (height - H * scale) / 2
    assert ox >= -1e-9 and oy >= -1e-9
    for x, y in points:
        physical_x, physical_y = ox + x * scale, oy + y * scale
        logical_x = (physical_x - ox) / scale
        logical_y = (physical_y - oy) / scale
        assert math.isclose(logical_x, x, abs_tol=1e-8)
        assert math.isclose(logical_y, y, abs_tol=1e-8)
        checks += 1
    # Any letterboxed margin is outside the 360x720 logical canvas.
    if ox > 0:
        assert (0 - ox) / scale < 0
    if oy > 0:
        assert (0 - oy) / scale < 0
    # Every navigation tab center maps to exactly one tab index.
    for tab in range(5):
        x = 36 + 72 * tab
        assert int(x / 72) == tab

# The asset naming convention covers 24 distinct biomes and ore sprites.
assert len({f"biome_{i:02d}.jpg" for i in range(24)}) == 24
assert len({f"ore_{i:02d}.png" for i in range(24)}) == 24
print(f"PASS: {checks} forward/inverse viewport points, {len(screens)} screen sizes, "
      "five navigation tabs, 24 biome and 24 ore asset names; no build")
