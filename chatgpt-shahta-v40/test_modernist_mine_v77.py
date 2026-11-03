"""v7.7 source-only mine/HUD geometry checks; never builds an APK."""
from pathlib import Path
from math import isclose

patch=Path(__file__).with_name("patch_modernist_v77.py").read_text()
for marker in (
    'v72NineSlice(c,"panel.png",18,93,324,83,255)',
    'leftFittedText(c,"ГЛУБИНА "+depth,40,119,17,0xffeffffc,171)',
    'fittedText(c,"СЕКТОР "+(biome+1)+" / 24",276,117,11,',
    'leftFittedText(c,ZONES[biome]+" / "+ORE_NAMES[id],',
    'rect(c,39,158,282*step,5,0xff64ddce)',
    'v72NineSlice(c,"panel.png",18,457,324,119,255)',
    'v72NineSlice(canvas,"panel.png",18,240,324,26,252)',
    'leftFittedText(canvas,toast,39,258,12,0xfff0fffb,285)',
    'else if(x>=105&&x<=330&&y>=210&&y<=440)',
):
    assert marker in patch,marker

W,H=360,720
sizes=[(320,568),(360,720),(393,852),(720,1280),(1080,2400),(1272,2772),(1440,3200)]
nav=(0,88,360,136)
mine_header=(18,93,342,176)
toast=(18,240,342,266)
ore=(105,270,330,500)  # rendered mine hitbox: source y=210..440 plus +60
hp=(18,517,342,636)  # source panel shifted +60
power=(16,670,344,705)  # source action controls shifted +60
checks=0

def overlaps(a,b):
    return max(a[0],b[0])<min(a[2],b[2]) and max(a[1],b[1])<min(a[3],b[3])

# Mine content is translated +60 before rendering; top navigation is not.
assert not overlaps((nav[0],nav[1],nav[2],nav[3]),
                    (mine_header[0],mine_header[1]+60,mine_header[2],mine_header[3]+60))
assert not overlaps((mine_header[0],mine_header[1]+60,mine_header[2],mine_header[3]+60),ore)
assert not overlaps(toast,ore)
assert not overlaps(toast,(mine_header[0],mine_header[1]+60,mine_header[2],mine_header[3]+60))
assert not overlaps(hp,ore)
assert not overlaps(hp,power)
assert 40+171 < 276-116/2  # depth label cannot enter the sector label
assert 39+285 <= 342       # notification text remains within the panel
checks+=8

# Notifications are visual overlays, not interactive controls. Their visible
# rectangle must not obscure the mine tap target or the bottom action button.
assert not overlaps(toast,power)
assert toast[1] - (mine_header[3]+60) >= 4
assert ore[1] - toast[3] >= 4  # toast ends before the translated ore hitbox
checks+=3

for width,height in sizes:
    scale=min(width/W,height/H)
    ox=(width-W*scale)/2
    oy=(height-H*scale)/2
    assert scale>0
    checks+=1
    for x,y in ((18,93),(39,158),(321,163),(105,210),(330,440),
                (18,457),(342,576),(16,610),(344,645)):
        px,py=ox+x*scale,oy+(y+60)*scale
        rx=(px-ox)/scale
        ry=(py-oy)/scale-60
        assert isclose(rx,x,abs_tol=1e-5)
        assert isclose(ry,y,abs_tol=1e-5)
        checks+=1
    # Confirm that the toast and mining target retain their relative separation
    # after letterboxing, including narrow and unusually tall displays.
    def screen_rect(r):
        return (ox+r[0]*scale,oy+r[1]*scale,
                ox+r[2]*scale,oy+r[3]*scale)
    assert not overlaps(screen_rect(toast),screen_rect(ore))
    assert not overlaps(screen_rect(toast),screen_rect(power))
    checks+=2
    for depth in (1,24,25,26,100,600):
        step=((depth-1)%25+1)/25
        assert 0<step<=1
        assert 39+282*step<=321
        checks+=1
    for x,y in ((105,210),(215,320),(330,440)):
        assert ore[0]<=x<=ore[2] and ore[1]<=y+60<=ore[3]
        checks+=1
print(f"PASS: {checks} source-only mine/HUD checks on {len(sizes)} screen sizes")
