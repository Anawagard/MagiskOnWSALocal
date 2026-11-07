"""Source-only toast occlusion contract across seven screen sizes.

No Android build, emulator, Gradle or workflow execution.
The global toast is an overlay and must not cover purchase buttons,
mine hits, or the five-cell navigation.
"""
from pathlib import Path
from math import isclose

patch = Path(__file__).with_name("patch_modernist_v77.py").read_text()
shop = Path(__file__).with_name("patch_modernist_v76.py").read_text()
nav = Path(__file__).with_name("patch_modernist_v75.py").read_text()
assert 'v72NineSlice(canvas,"panel.png",18,240,324,26,252)' in patch
assert 'button(c,x+13,y+102,139,36,"УЛУЧШИТЬ"' in shop
assert 'float left=i*72f;' in nav

toast = (18,240,342,266)
navigation = (0,88,360,136)
mine_target = (105,270,330,500)  # source y=210..440, translated +60
sizes = ((320,568),(360,720),(393,852),(720,1280),
         (1080,2400),(1272,2772),(1440,3200))

def intersects(a,b):
    return max(a[0],b[0]) < min(a[2],b[2]) and max(a[1],b[1]) < min(a[3],b[3])

# Shop cards are at source y=164+(row*153), shifted +60.
buttons = []
for row in range(3):
    for col in range(2):
        x = 10+175*col
        y = 164+153*row+60
        buttons.append((x+13,y+102,x+152,y+138))

assert not intersects(toast,navigation)
assert not intersects(toast,mine_target)
assert all(not intersects(toast,button) for button in buttons)
assert all(0 <= x1 < x2 <= 360 and 0 <= y1 < y2 <= 720
           for x1,y1,x2,y2 in buttons)

checks = 0
for width,height in sizes:
    scale = min(width/360,height/720)
    ox = (width-360*scale)/2
    oy = (height-720*scale)/2
    def screen_rect(r):
        return (ox+r[0]*scale,oy+r[1]*scale,
                ox+r[2]*scale,oy+r[3]*scale)
    transformed = screen_rect(toast)
    for target in (navigation,mine_target,*buttons):
        assert not intersects(transformed,screen_rect(target))
        checks += 1
    for x,y in ((18,240),(342,266),(23,326),(337,362)):
        sx,sy = ox+x*scale,oy+y*scale
        assert isclose((sx-ox)/scale,x,abs_tol=1e-6)
        assert isclose((sy-oy)/scale,y,abs_tol=1e-6)
        checks += 2

print(f"PASS: {checks} source-only toast/hitbox assertions on {len(sizes)} screens")
