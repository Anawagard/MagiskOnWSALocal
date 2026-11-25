"""Source-only geometry/typography contract for v7.6. No APK/Gradle."""
from math import isclose
from pathlib import Path

patch = Path(__file__).with_name("patch_modernist_v76.py").read_text()
for marker in (
    'rect(c,17,103,3,30,identity)',
    'v72NineSlice(c,"panel.png",10,94,340,49,255)',
    'v72NineSlice(c,"button_off.png",298,98,44,41,214)',
    'v72NineSlice(c,"panel.png",x,y,165,145,255)',
    'button(c,x+13,y+102,139,36,"УЛУЧШИТЬ"',
    'if(screenY>=88&&screenY<=136)',
    'if(screenY<205f||screenY>713f)return true;',
):
    assert marker in patch, marker

# Verify per-destination accents against the actual toast palette, not merely
# the presence of arbitrary color literals. All three need high contrast on
# graphite, and decorative strokes must stay away from localized headings.
feature_accents = {2: 0xffffa77a, 3: 0xffc4a7ff, 4: 0xff82bfff}
identity_expression = (
    'int identity=tab==2 ? 0xffffa77a : '
    '(tab==3 ? 0xffc4a7ff : 0xff82bfff);'
)
assert identity_expression in patch
assert len(set(feature_accents.values())) == 3
assert "rect(c,12,103,2,12,identity);" in patch
assert "rect(c,12,118,2,7,0xff315d60);" in patch
assert "rect(c,28,139,72,1,identity);" in patch

def luminance(argb):
    rgb = [(argb >> shift & 255) / 255.0 for shift in (16, 8, 0)]
    linear = [v / 12.92 if v <= 0.04045
              else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    return sum(value * weight for value, weight in
               zip(linear, (0.2126, 0.7152, 0.0722)))

graphite = 0xff17202f  # panel.png base is (23, 32, 47)
for tab, accent in feature_accents.items():
    ratio = (luminance(accent) + 0.05) / (luminance(graphite) + 0.05)
    assert ratio >= 7.0, ("Low-contrast feature accent", tab, ratio)
    assert 12 + 2 < 28  # Tiny registration marks are left of the title.
    assert 94 <= 103 < 115 <= 143
    assert 94 <= 118 < 125 <= 143

# A five-page toast is drawn outside the translated page Canvas. When a
# feature-page toast occupies screen y=177..203, its header must hide
# the subtitle and ore badge rather than painting invisible overlapping text.
v79 = Path(__file__).with_name("patch_modernist_v79.py").read_text()
assert "int toastY = page==0 ? 240 : (page==1 ? 691 : 177);" in v79
for color in feature_accents.values():
    assert f"0x{color:08x}" in v79, ("Feature accent disagrees with toast", color)
assert "boolean toastInHeader=System.currentTimeMillis()<toastUntil;" in patch
assert "leftFittedText(c,title,28,toastInHeader?110:114,16,0xfff0fffd,253);" in patch
block_start = patch.index("        if(!toastInHeader){")
block_end = patch.index("        }", block_start)
decorations = patch[block_start:block_end]
for token in (
    'leftFittedText(c,subtitle,28,132,10,0xffb3d2d4,253);',
    'v72NineSlice(c,"button_off.png",298,98,44,41,214);',
    'v70Draw(c,String.format(Locale.US,"ore_%02d.png",(tab*5)%24),',
):
    assert token in decorations, ("feature decoration not hidden during toast",token)
assert patch.index("leftFittedText(c,title,28,toastInHeader?110:114") < block_start
# Title baseline y=170 during toast leaves 7px before notification top y=177.
# Hidden subtitle baseline (132+60=192) and icon (102..134+60)
# would both collide with notification.
assert 110 + 60 <= 177 - 7
assert 132 + 60 >= 177
assert 102 + 60 < 177 < 134 + 60

screens = [(320,568),(360,640),(360,720),(720,1280),(1080,2400),(1272,2772),(1440,3200)]
header = (10,94,350,143)
content_clip = (0,145,360,653)
nav = (0,88,360,136)
shop_tiles = [(10+(i%2)*175,164+(i//2)*153,165,145) for i in range(6)]
checks = 0
assert header[3] < content_clip[1]  # no header over interactive content
assert len(shop_tiles) == 6
for i,(x,y,w,h) in enumerate(shop_tiles):
    buy = (x+13,y+102,x+152,y+138)
    assert buy[2] <= x+w and buy[3] <= y+h
    assert buy[3] <= 653, ("clipped button",i,buy)
    checks += 1

for width,height in screens:
    scale = min(width/360,height/720)
    ox,oy = (width-360*scale)/2,(height-720*scale)/2
    def roundtrip(x,y):
        px,py = x*scale+ox,y*scale+oy
        return (px-ox)/scale,(py-oy)/scale
    # The complete 360x720 logical canvas must fit even on narrow screens.
    assert scale > 0 and ox >= -1e-6 and oy >= -1e-6
    for lx,ly in ((0,0),(360,0),(0,720),(360,720)):
        px,py=lx*scale+ox,ly*scale+oy
        assert -1e-5 <= px <= width+1e-5 and -1e-5 <= py <= height+1e-5
        checks += 1
    # Header and feature content are translated +60; top nav is not.
    header_top = (header[1]+60)*scale+oy
    nav_bottom = nav[3]*scale+oy
    assert header_top > nav_bottom, (width,height)
    checks += 1
    for x,y in ((17,103),(28,114),(304,102),(335,133)):
        rx,ry = roundtrip(x,y+60)
        assert isclose(rx,x,abs_tol=1e-5)
        assert isclose(ry-60,y,abs_tol=1e-5)
        assert header[0] <= rx <= header[2]
        assert header[1] <= ry-60 <= header[3]
        checks += 1
    for x,y,w,h in shop_tiles:
        for bx,by in ((x+14,y+103),(x+82,y+120),(x+151,y+137)):
            rx,ry = roundtrip(bx,by+60)
            assert isclose(rx,bx,abs_tol=1e-5)
            assert isclose(ry-60,by,abs_tol=1e-5)
            assert x+13 <= rx <= x+152 and y+102 <= ry-60 <= y+138
            checks += 1
print(f"PASS: {checks} source-only v7.6 layout assertions across {len(screens)} screens")
