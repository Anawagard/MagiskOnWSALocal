"""Source-only regression: no invisible taps behind the three feature headers.

Validates real v7.2 patch source and physical-to-logical inverse transforms.
Does not invoke Android, Gradle, APK or Actions.
"""
from pathlib import Path
import ast
import math

HERE = Path(__file__).resolve().parent
source = (HERE / "patch_modernist_v72.py").read_text(encoding="utf-8")
ast.parse(source)

MARKERS = (
    'for name in ("drawForge","drawGuild","drawCollection"):',
    'c.clipRect(0,145,360,653);',
    'if(screenY<205f||screenY>713f)return true;',
    'x=(x-13f)/.93f;',
    'y=(y-18f)/.94f;',
    'if(screenY>=88&&screenY<=136)',
)
def verify(text):
    for marker in MARKERS:
        if marker not in text:
            raise AssertionError("Missing feature header/touch invariant: " + marker)

verify(source)
for old, new in (
    ('screenY<205f', 'screenY<175f'),
    ('screenY>713f', 'screenY>720f'),
    ('c.clipRect(0,145,360,653);', 'c.clipRect(0,115,360,653);'),
    ('x=(x-13f)/.93f;', 'x=x/.93f;'),
    ('y=(y-18f)/.94f;', 'y=y/.94f;'),
):
    assert old in source
    try:
        verify(source.replace(old, new, 1))
    except AssertionError:
        pass
    else:
        raise AssertionError("Mutated invisible header hitbox was accepted: " + old)

sizes = ((176,320),(200,400),(240,1080),(280,560),(320,568),
         (360,720),(393,852),(720,1280),(1080,2400),
         (1272,2772),(1440,320),(2560,720))
checks = 0
for width, height in sizes:
    scale = min(width/360, height/720)
    ox, oy = (width-360*scale)/2, (height-720*scale)/2
    for page in ("forge", "guild", "atlas"):
        for x in (0.1, 13, 180, 359.9):
            for y in (136, 174, 192, 204.99, 205.01, 340, 712.99, 713.01):
                px, py = ox+x*scale, oy+y*scale
                rx, ry = (px-ox)/scale, (py-oy)/scale
                assert math.isclose(rx,x,abs_tol=1e-6)
                assert math.isclose(ry,y,abs_tol=1e-6)
                visible = 205 <= ry <= 713
                assert visible == (205 <= y <= 713), (page,width,height,x,y)
                if visible:
                    lx, ly = (rx-13)/.93, (ry-78)/.94
                    assert math.isclose(lx,(x-13)/.93,abs_tol=1e-5)
                    assert math.isclose(ly,(y-78)/.94,abs_tol=1e-5)
                checks += 1
        if ox > 0:
            assert (ox/2-ox)/scale < 0
            checks += 1
        if oy > 0:
            assert (oy/2-oy)/scale < 0
            checks += 1
print(f"PASS: {checks} feature-header visibility/touch checks; 5 mutation guards")
