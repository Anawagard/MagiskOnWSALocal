"""Pure-math/source contract for v7.5 header and top navigation.

No Android toolchain, Gradle, emulator or APK is involved.
"""
from math import isclose
from pathlib import Path

W,H=360,720
screens=[(360,720),(720,1280),(1080,2400),(1272,2772),(1440,3200)]
cards=[(10,39,176,79),(184,39,350,79)]
tabs=[(i*72,88,(i+1)*72,136) for i in range(5)]
patch=Path(__file__).with_name("patch_modernist_v75.py").read_text()
assert 'float left=i*72f;' in patch
assert 'left+4,90,64,44' in patch
assert 'left+36,126,10' in patch
assert 'if(screenY>=88&&screenY<=136)' in patch
assert 'int next=clamp((int)(x/72f),0,4);' in patch
assert 'v72NineSlice(c,"panel.png",10,39,166,40,255);' in patch
assert 'v72NineSlice(c,"panel.png",184,39,166,40,255);' in patch

def contains(rect,x,y):
    a,b,c,d=rect
    return a<=x<c and b<=y<=d

checks=0
assert cards[0][2]<cards[1][0]
assert all(card[3]<88 for card in cards)
for width,height in screens:
    scale=min(width/W,height/H)
    ox=(width-W*scale)/2
    oy=(height-H*scale)/2
    for i,tab in enumerate(tabs):
        for x,y in ((i*72+5,92),(i*72+36,112),(i*72+67,132)):
            px,py=x*scale+ox,y*scale+oy
            rx,ry=(px-ox)/scale,(py-oy)/scale
            assert isclose(rx,x,abs_tol=1e-5)
            assert isclose(ry,y,abs_tol=1e-5)
            assert contains(tab,rx,ry)
            assert int(rx/72)==i
            checks+=1
    for card in cards:
        x=(card[0]+card[2])/2
        y=(card[1]+card[3])/2
        px,py=x*scale+ox,y*scale+oy
        rx,ry=(px-ox)/scale,(py-oy)/scale
        assert isclose(rx,x,abs_tol=1e-5)
        assert isclose(ry,y,abs_tol=1e-5)
        assert not any(contains(tab,rx,ry) for tab in tabs)
        checks+=1
print(f"PASS: {checks} HUD/navigation geometry checks on {len(screens)} displays")
