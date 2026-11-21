"""Pure Python regression tests for v7.3 settings hitboxes and scaling.

No Android toolchain, network, assets, emulator, Gradle or APK is used.
"""
from math import isclose
from pathlib import Path

W, H = 360, 720
# Drawn clickable rectangles (x0,y0,x1,y1) in translated page coordinates.
controls = {
    "sound": (218,251,323,301),
    "volume": (35,383,325,414),  # 7px finger margin around slider
    "effects": (218,461,323,511),
    "back": (18,548,342,609),
}
settings_button = (241,99,345,141)
cards = {
    "sound": (18,235,342,320),
    "volume": (18,327,342,439),
    "effects": (18,445,342,530),
    "back": (18,548,342,609),
}
screens = [(360,720),(720,1280),(1080,2400),(1272,2772),(1440,3200)]

def physical(x,y,w,h):
    scale = min(w/W,h/H)
    return x*scale+(w-W*scale)/2, y*scale+(h-H*scale)/2

def logical(px,py,w,h):
    scale = min(w/W,h/H)
    return (px-(w-W*scale)/2)/scale, (py-(h-H*scale)/2)/scale

def contains(rect,x,y):
    x0,y0,x1,y1 = rect
    return x0 <= x <= x1 and y0 <= y <= y1

def action(x,y):
    for name,rect in controls.items():
        if contains(rect,x,y):
            return name
    return None

# Verify that the source patch uses the same rectangles as this test.
patch = Path(__file__).with_name("patch_modernist_v73.py").read_text()
for name,(x0,y0,x1,y1) in controls.items():
    needle = f"x>={x0}&&x<={x1}&&y>={y0}&&y<={y1}"
    assert needle in patch,(name,needle)
assert "settingsOpen=false;" in patch
assert "Math.round((x-42f)/276f*20f)*5" in patch

checks = 0
for name,rect in controls.items():
    x0,y0,x1,y1 = rect
    assert contains(cards[name],(x0+x1)/2,(y0+y1)/2)
    for other,other_rect in controls.items():
        if other != name:
            assert not contains(other_rect,(x0+x1)/2,(y0+y1)/2)
    checks += 1

for w,h in screens:
    for name,rect in controls.items():
        x0,y0,x1,y1 = rect
        for x,y in ((x0+1,y0+1),((x0+x1)/2,(y0+y1)/2),(x1-1,y1-1)):
            px,py = physical(x,y+60,w,h)
            rx,ry = logical(px,py,w,h)
            assert isclose(rx,x,abs_tol=1e-4)
            assert isclose(ry-60,y,abs_tol=1e-4)
            assert action(rx,ry-60)==name,(w,h,name,rx,ry)
            checks += 1
    for x,y in ((40,250),(150,285),(40,350),(180,475),(180,535),(180,625)):
        px,py=physical(x,y+60,w,h)
        rx,ry=logical(px,py,w,h)
        assert action(rx,ry-60) is None,(w,h,x,y)
        checks += 1
    # Shop settings entry uses a different rectangle; avoid accidental taps.
    for x,y in ((242,100),(290,120),(344,140)):
        px,py=physical(x,y+60,w,h)
        rx,ry=logical(px,py,w,h)
        assert contains(settings_button,rx,ry-60)
        checks += 1
    # 0-100% slider, 5% steps, and clamping outside the visual track.
    for x,expected in ((35,0),(42,0),(111,25),(180,50),(249,75),(318,100),(325,100)):
        volume=max(0,min(100,round((x-42)/276*20)*5))
        assert volume==expected,(x,volume,expected)
        checks += 1

print(f"PASS: {checks} v7.3 settings geometry checks across {len(screens)} displays")
