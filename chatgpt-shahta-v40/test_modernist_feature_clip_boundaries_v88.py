"""Source-only regression for feature-page clipping and touch mapping.

No Android SDK, Gradle or APK required. Run from repository root.
"""
from pathlib import Path
from math import isclose

patch = Path("chatgpt-shahta-v40/patch_modernist_v72.py").read_text(encoding="utf-8")
geometry = Path("chatgpt-shahta-v40/test_modernist_geometry_v72.py").read_text(encoding="utf-8")

# The canvas clip is applied before the content transform; screen coordinates
# therefore use the 60px game header offset, but NOT the content scale.
assert 'c.clipRect(0,145,360,653);' in patch
assert patch.count('c.translate(13f,18f);') >= 2
assert patch.count('c.scale(.93f,.94f);') >= 2
assert 'if(screenY<205f||screenY>713f)return true;' in patch
assert 'x=(x-13f)/.93f;' in patch
assert 'y=(y-18f)/.94f;' in patch
assert 'if(screenY>=88&&screenY<=136)' in patch
assert 'for name in ("drawForge","drawGuild","drawCollection"):' in patch
assert 'screens=[(360,720),(320,720),(320,568)' in geometry

W,H = 360,720
sizes = ((320,568),(320,720),(360,640),(393,873),(720,1280),
         (1080,2400),(1272,2772),(1440,3200))
checks = 0

def viewport(w,h):
    scale = min(w/W,h/H)
    return scale,(w-W*scale)/2,(h-H*scale)/2

def map_to_screen(x,y,w,h):
    s,ox,oy = viewport(w,h)
    return x*s+ox,y*s+oy

def map_to_logical(px,py,w,h):
    s,ox,oy = viewport(w,h)
    return (px-ox)/s,(py-oy)/s

def hit_feature(px,py,w,h):
    x,screen_y = map_to_logical(px,py,w,h)
    if not (0 <= x <= W and 205 <= screen_y <= 713):
        return None
    return (x-13)/.93,((screen_y-60)-18)/.94

for w,h in sizes:
    for sy in (0,88,136,145,174,192,204,204.999,713.001,714,719,720):
        px,py = map_to_screen(180,sy,w,h)
        assert hit_feature(px,py,w,h) is None,(w,h,sy)
        checks += 1
    for sy in (205,205.001,340,712.999,713):
        px,py = map_to_screen(180,sy,w,h)
        xy = hit_feature(px,py,w,h)
        assert xy is not None,(w,h,sy)
        assert isclose(xy[0],(180-13)/.93,abs_tol=1e-6)
        assert isclose(xy[1],((sy-60)-18)/.94,abs_tol=1e-6)
        checks += 1
    # Letterboxed regions must not accidentally activate invisible controls.
    s,ox,oy = viewport(w,h)
    if ox > 0:
        assert hit_feature(ox/2,h/2,w,h) is None
        checks += 1
    if oy > 0:
        assert hit_feature(w/2,oy/2,w,h) is None
        checks += 1

# Horizontal viewport bounds matter as much as the vertical header clip.
# Test near-edge and subpixel out-of-bounds coordinates after letterboxing.
# Avoid the exact right edge: float roundtrips can yield 360 + one ULP.
for w,h in sizes:
    for sx in (-1,-.001,360.001,361):
        px,py = map_to_screen(sx,340,w,h)
        assert hit_feature(px,py,w,h) is None,(w,h,sx)
        checks += 1
    for sx in (0,.001,13,180,359.999):
        px,py = map_to_screen(sx,340,w,h)
        xy = hit_feature(px,py,w,h)
        assert xy is not None,(w,h,sx)
        assert isclose(xy[0],(sx-13)/.93,abs_tol=1e-5),(w,h,sx,xy)
        assert isclose(xy[1],(340-78)/.94,abs_tol=1e-5),(w,h,sx,xy)
        checks += 1

# Exercise corners near both boundaries, not just the horizontal midline.
for w,h in sizes:
    for sx in (-.001, 360.001):
        for sy in (205.001, 340, 712.999):
            px,py = map_to_screen(sx,sy,w,h)
            assert hit_feature(px,py,w,h) is None,(w,h,sx,sy)
            checks += 1

print(f"PASS: {checks} clip/touch boundary assertions on {len(sizes)} sizes")
