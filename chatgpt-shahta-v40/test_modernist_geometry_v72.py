"""Pure-math v7.2 input geometry regression checks. No APK build required."""
from math import isclose

W,H=360,720

def viewport(width,height):
    scale=min(width/W,height/H)
    return scale,(width-W*scale)/2,(height-H*scale)/2

def physical(x,y,width,height):
    s,ox,oy=viewport(width,height)
    return x*s+ox,y*s+oy

def logical(px,py,width,height):
    s,ox,oy=viewport(width,height)
    return (px-ox)/s,(py-oy)/s

def feature_screen(x,y):
    return 13+.93*x,60+18+.94*y

def feature_input(x,screen_y):
    return (x-13)/.93,((screen_y-60)-18)/.94

screens=[(360,720),(720,1280),(1080,2400),(1272,2772),(1440,3200)]
checks=0
for width,height in screens:
    for tab in range(5):
        x=36+72*tab
        px,py=physical(x,111,width,height)
        rx,ry=logical(px,py,width,height)
        assert isclose(rx,x,abs_tol=1e-5)
        assert 88<=ry<=136 and int(rx/72)==tab
        checks+=1
    for i in range(6):
        xx=10+(i%2)*175
        yy=164+(i//2)*153
        for x,y in [(xx+13,yy+102),(xx+82,yy+119),(xx+152,yy+138)]:
            px,py=physical(x,y+60,width,height)
            rx,ry=logical(px,py,width,height)
            ry-=60
            assert xx+13-1e-5<=rx<=xx+152+1e-5
            assert yy+102-1e-5<=ry<=yy+138+1e-5
            checks+=1
    for x,y in [(105,210),(220,325),(330,440)]:
        px,py=physical(x,y+60,width,height)
        rx,ry=logical(px,py,width,height)
        ry-=60
        assert 105-1e-5<=rx<=330+1e-5 and 210-1e-5<=ry<=440+1e-5
        checks+=1
    for i,x in enumerate((68,180,292)):
        px,py=physical(x,627+60,width,height)
        rx,ry=logical(px,py,width,height)
        ry-=60
        assert 609<=ry<=648
        assert (0 if rx<124 else 1 if rx<236 else 2)==i
        checks+=1
    for x,y in ((293,120),(120,137)):
        px,py=physical(x,y+60,width,height)
        rx,ry=logical(px,py,width,height)
        ry-=60
        assert (rx>=235 and 95<=ry<=144) if x==293 else (rx<234 and 117<=ry<=157)
        checks+=1
    for x,y in [(15,150),(180,340),(340,610),(180,645)]:
        sx,sy=feature_screen(x,y)
        px,py=physical(sx,sy,width,height)
        lx,ly=logical(px,py,width,height)
        rx,ry=feature_input(lx,ly)
        assert isclose(rx,x,abs_tol=1e-4),(width,height,x,rx)
        assert isclose(ry,y,abs_tol=1e-4),(width,height,y,ry)
        checks+=1
print(f'PASS: {checks} geometry assertions across {len(screens)} resolutions; no APK built')
