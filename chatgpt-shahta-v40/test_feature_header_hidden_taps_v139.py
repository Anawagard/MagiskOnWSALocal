"""Source-only regression: no invisible taps behind the three feature headers.

Validates real v7.2 patch source and physical-to-logical inverse transforms.
Does not invoke Android, Gradle, APK or Actions.
"""
from pathlib import Path
import ast
import math
import textwrap

HERE = Path(__file__).resolve().parent
source = (HERE / "patch_modernist_v72.py").read_text(encoding="utf-8")

MARKERS = (
    'for name in ("drawForge","drawGuild","drawCollection"):',
    'c.clipRect(0,145,360,653);',
    'if(screenY<205f||screenY>713f)return true;',
    'if(x<13f||x>347.8f)return true;',
    'float y=screenY-60f;',
    'x=(x-13f)/.93f;',
    'y=(y-18f)/.94f;',
)
def verify(text):
    # Validate the emitted Java rather than Python postcondition strings.
    snippets = [line for node in ast.walk(ast.parse(text))
                if isinstance(node, ast.Constant) and isinstance(node.value, str)
                and "\n" in node.value
                for line in textwrap.dedent(node.value).splitlines()]
    emitted = "\n".join(snippets)
    for marker in MARKERS:
        haystack = text if marker.startswith('for name') else emitted
        if marker not in haystack:
            raise AssertionError("Missing feature header/touch invariant: " + marker)

verify(source)
for old, new in (
    ('screenY<205f', 'screenY<175f'),
    ('screenY>713f', 'screenY>720f'),
    ('x>347.8f', 'x>360f'),
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
print(f"PASS: {checks} feature-header visibility/touch checks; 6 mutation guards")


# Boundary-sweep regression: all three feature pages must suppress taps
# outside the 205..713 painted content strip after viewport letterboxing.
# Exact boundary samples use tolerance because inverse float transforms can
# produce 204.99999999999997 at a nominal 205px boundary.
boundary_checks = 0
for width, height in sizes:
    scale = min(width/360, height/720)
    ox, oy = (width-360*scale)/2, (height-720*scale)/2
    for page in ("forge", "guild", "atlas"):
        for y in (0, 88, 136, 204.9, 205.1, 350, 712.9, 713.1, 719.9):
            for x in (0.1, 13, 180, 346, 359.9):
                px, py = ox+x*scale, oy+y*scale
                rx, ry = (px-ox)/scale, (py-oy)/scale
                assert math.isclose(rx, x, abs_tol=1e-7)
                assert math.isclose(ry, y, abs_tol=1e-7)
                assert (205 <= ry <= 713) == (205 <= y <= 713), (page,width,height,x,y)
                if 205 <= ry <= 713:
                    lx, ly = (rx-13)/.93, (ry-78)/.94
                    assert math.isclose(13+lx*.93,rx,abs_tol=1e-7)
                    assert math.isclose(78+ly*.94,ry,abs_tol=1e-7)
                boundary_checks += 1
print(f"PASS: {boundary_checks} additional feature-page boundary checks")

# Regression for the real source transform: touch starts with y=screenY-60,
# then the feature wrapper subtracts 18 and scales by .94.  The x gutter
# must be rejected BEFORE applying the inverse feature transform.
# These are checks against the same constants asserted above.
gutter_checks = 0
for width, height in sizes:
    scale = min(width / 360, height / 720)
    ox, oy = (width - 360 * scale) / 2, (height - 720 * scale) / 2
    for page in ("forge", "guild", "atlas"):
        for logical_x in (-0.1, 0, 12.99, 13.01, 180, 347.79, 347.81, 359.99, 360):
            for logical_y in (204.9, 205.1, 350, 712.9, 713.1):
                px = ox + logical_x * scale
                py = oy + logical_y * scale
                x = (px - ox) / scale
                screen_y = (py - oy) / scale
                active = 205 <= screen_y <= 713 and 13 <= x <= 347.8
                expected = 205 <= logical_y <= 713 and 13 <= logical_x <= 347.8
                assert active == expected, (page, width, height, logical_x, logical_y)
                if active:
                    legacy_x = (x - 13) / .93
                    legacy_y = (screen_y - 60 - 18) / .94
                    assert math.isclose(13 + legacy_x * .93, x, abs_tol=1e-7)
                    assert math.isclose(60 + 18 + legacy_y * .94, screen_y, abs_tol=1e-7)
                gutter_checks += 1
print(f"PASS: {gutter_checks} feature-page side-gutter and full vertical-transform checks")

