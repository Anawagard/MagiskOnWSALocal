"""Source-only mine sprite/touch regression across compact Android viewports.

Checks the actual patch anchors and inverse letterbox mapping; no APK/Gradle.
"""
from pathlib import Path
import ast
import math
import re

HERE = Path(__file__).resolve().parent
source = (HERE / "patch_modernist_v71.py").read_text(encoding="utf-8")
ast.parse(source)

ORE = (105, 210, 225, 230)
MINER = (15, 293, 113, 160)
HIT = (105, 210, 330, 440)
VIEW = (360, 720)

def verify_patch(text):
    for anchor in (
        'v70Draw(c,"miner.png",15,293,113,160,255)',
        '105,210,225,230,255',
        'if(x>=105&&x<=330&&y>=210&&y<=440)',
        'canvas.translate(v71OffsetX(),v71OffsetY());',
        'canvas.scale(v71Scale(),v71Scale());',
        '(e.getX()-v71OffsetX())/v71Scale()',
        '(e.getY()-v71OffsetY())/v71Scale()',
        'if(x<0||x>=W||screenY<0||screenY>=H)return true;',
    ):
        if text.count(anchor) != 1:
            raise AssertionError("Missing or duplicated mine geometry: " + anchor)
    ox, oy, ow, oh = ORE
    hx0, hy0, hx1, hy1 = HIT
    if (ox, oy, ox + ow, oy + oh) != HIT:
        raise AssertionError("Ore touch bounds differ from rendered sprite")
    mx, my, mw, mh = MINER
    if not (mx >= 0 and my >= 0 and mx + mw <= VIEW[0] and my + mh <= VIEW[1]):
        raise AssertionError("Miner outside logical canvas")
    if not (hx0 >= 0 and hy0 > 136 and hx1 <= VIEW[0] and hy1 < 653):
        raise AssertionError("Ore touch region overlaps navigation or footer")

verify_patch(source)
for replacement in (
    source.replace("x<=330&&y>=210", "x<=340&&y>=210", 1),
    source.replace("105,210,225,230,255", "105,210,235,230,255", 1),
    source.replace("(e.getX()-v71OffsetX())/v71Scale()",
                   "e.getX()/v71Scale()", 1),
):
    try:
        verify_patch(replacement)
    except AssertionError:
        pass
    else:
        raise AssertionError("Mutated mine hitbox/transform was accepted")

count = 0
for width, height in ((176, 320), (200, 400), (240, 1080),
                      (280, 560), (320, 568), (360, 720),
                      (393, 852), (720, 1280), (1080, 2400),
                      (1272, 2772), (1440, 320), (2560, 720)):
    scale = min(width / VIEW[0], height / VIEW[1])
    left = (width - VIEW[0] * scale) / 2
    top = (height - VIEW[1] * scale) / 2
    for x, y, inside in (
        (105.1, 210.1, True), (329.9, 439.9, True),
        (217.5, 325, True), (104.9, 325, False),
        (330.1, 325, False), (217.5, 209.9, False),
        (217.5, 440.1, False), (36, 112, False),
    ):
        physical_x = left + x * scale
        physical_y = top + y * scale
        inverse_x = (physical_x - left) / scale
        inverse_y = (physical_y - top) / scale
        assert math.isclose(inverse_x, x, abs_tol=1e-7)
        assert math.isclose(inverse_y, y, abs_tol=1e-7)
        assert (HIT[0] <= inverse_x <= HIT[2] and
                HIT[1] <= inverse_y <= HIT[3]) == inside
        count += 1
    # Letterbox gutters cannot be interpreted as mine taps.
    if left > 0:
        assert (left / 2 - left) / scale < 0
    if top > 0:
        assert (top / 2 - top) / scale < 0

print(f"PASS: mine art/hitbox identity and {count} viewport touch assertions")
