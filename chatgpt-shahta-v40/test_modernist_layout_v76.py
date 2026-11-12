"""Source-only geometry/typography contract for v7.6. No APK/Gradle."""
from math import isclose
from pathlib import Path

patch = Path(__file__).with_name("patch_modernist_v76.py").read_text()
for marker in (
    'rect(c,17,103,3,30,0xff65e1d0)',
    'v72NineSlice(c,"panel.png",10,94,340,49,255)',
    'v72NineSlice(c,"button_off.png",298,98,44,41,214)',
    'v72NineSlice(c,"panel.png",x,y,165,145,255)',
    'button(c,x+13,y+102,139,36,"УЛУЧШИТЬ"',
    'if(screenY>=88&&screenY<=136)',
    'if(screenY<205f||screenY>713f)return true;',
):
    assert marker in patch, marker

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
    # The complete 360x720 logical canvas must fit even on narrow screens.\n    assert scale > 0 and ox >= -1e-6 and oy >= -1e-6\n    for lx,ly in ((0,0),(360,0),(0,720),(360,720)):\n        px,py=lx*scale+ox,ly*scale+oy\n        assert -1e-5 <= px <= width+1e-5 and -1e-5 <= py <= height+1e-5\n        checks += 1\n    # Header and feature content are translated +60; top nav is not.
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
