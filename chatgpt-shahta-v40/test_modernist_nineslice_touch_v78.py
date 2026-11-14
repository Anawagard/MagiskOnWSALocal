"""Source-only numerical contract for nine-slice panels and feature-page input.

No Android build, Gradle, emulator, or GitHub Actions dispatch.
"""
from pathlib import Path
from math import isclose

patch = Path(__file__).with_name("patch_modernist_v72.py").read_text()
for token in (
    "int sx=Math.min(18,bw/4),sy=Math.min(18,bh/4);",
    "float dx=Math.min(11f,w/3f),dy=Math.min(11f,h/3f);",
    "c.clipRect(0,145,360,653);",
    "c.translate(13f,18f);",
    "c.scale(.93f,.94f);",
    "if(screenY<205f||screenY>713f)return true;",
    "x=(x-13f)/.93f;",
    "y=(y-18f)/.94f;",
):
    assert token in patch, token

checks = 0
for bw,bh in ((36,36),(96,48),(400,96),(512,512)):
    for w,h in ((26,26),(64,44),(165,145),(324,26),(340,49)):
        sx,sy = min(18,bw//4),min(18,bh//4)
        dx,dy = min(11.,w/3.),min(11.,h/3.)
        src_x=(0,sx,bw-sx,bw)
        src_y=(0,sy,bh-sy,bh)
        dst_x=(0,dx,w-dx,w)
        dst_y=(0,dy,h-dy,h)
        assert all(b>a for a,b in zip(src_x,src_x[1:]))
        assert all(b>a for a,b in zip(src_y,src_y[1:]))
        assert all(b>a for a,b in zip(dst_x,dst_x[1:]))
        assert all(b>a for a,b in zip(dst_y,dst_y[1:]))
        checks += 4

for width,height in ((320,568),(360,720),(393,852),(720,1280),
                     (1080,2400),(1272,2772),(1440,3200)):
    scale=min(width/360,height/720)
    ox=(width-360*scale)/2
    oy=(height-720*scale)/2
    for x,y in ((0,145),(13,205),(180,300),(347,653),(360,713)):
        # Feature page: base screen translate +60; local translation +13,+18,
        # then scaling .93,.94. The clipping bounds are in screen space.
        logical_x=13+.93*x
        logical_y=60+18+.94*y
        px,py=ox+logical_x*scale,oy+logical_y*scale
        back_x=((px-ox)/scale-13)/.93
        back_y=(((py-oy)/scale-60)-18)/.94
        assert isclose(back_x,x,abs_tol=1e-5)
        assert isclose(back_y,y,abs_tol=1e-5)
        checks += 2
    for y in (204.99,205,400,713,713.01):
        permitted=205<=y<=713
        assert permitted == (not (y<205 or y>713))
        checks += 1

print(f"PASS: {checks} nine-slice and feature-page touch geometry checks")
