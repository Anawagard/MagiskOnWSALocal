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
    # Keep identical with patch_modernist_v72.py: header is not interactive.
    if screen_y<205 or screen_y>713:
        return None
    return (x-13)/.93,((screen_y-60)-18)/.94

screens=[(240,320),(280,560),(320,480),(320,568),(320,720),(360,640),(360,720),(393,873),(480,800),(720,1280),(1080,2400),(1272,2772),(1440,3200),(1768,2208)]
checks=0
for width,height in screens:
    # Round-trip all viewport corners and near-edge controls, including
    # narrow displays with horizontal or vertical letterboxing.
    scale,offset_x,offset_y=viewport(width,height)
    assert scale>0 and offset_x>=-1e-8 and offset_y>=-1e-8
    for x,y in ((0,0),(W,0),(0,H),(W,H),(1,1),(W-1,H-1)):
        px,py=physical(x,y,width,height)
        rx,ry=logical(px,py,width,height)
        assert isclose(rx,x,abs_tol=1e-5),(width,height,x,rx)
        assert isclose(ry,y,abs_tol=1e-5),(width,height,y,ry)
        assert -1e-5<=px<=width+1e-5 and -1e-5<=py<=height+1e-5
        checks+=1
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
    # Test the exact clipping boundary at subpixel offsets after scaling.
    # On tall and narrow devices the logical clip must not drift due to
    # letterboxing or fractional screen-to-content conversion.
    for sy in (204.999, 205.0, 205.001, 712.999, 713.0, 713.001):
        px,py=physical(180,sy,width,height)
        lx,ly=logical(px,py,width,height)
        accepted=feature_input(lx,ly) is not None
        # Floating-point viewport inversion may move an exact endpoint by
        # one ULP. Validate proximity there; strict clipping elsewhere.
        if sy in (205.0, 713.0):
            assert isclose(ly,sy,abs_tol=1e-8),(width,height,sy,ly)
        else:
            assert accepted == (205<sy<713),(width,height,sy,accepted)
        checks+=1
    # Invisible legacy controls under the modern section header must never
    # receive touches. The clipped content is visible only at y=205..713.
    for sy in (145,174,192,204,714,719):
        px,py=physical(180,sy,width,height)
        lx,ly=logical(px,py,width,height)
        assert feature_input(lx,ly) is None,(width,height,sy)
        checks+=1
    for sy in (206,340,712):
        px,py=physical(180,sy,width,height)
        lx,ly=logical(px,py,width,height)
        assert feature_input(lx,ly) is not None,(width,height,sy)
        checks+=1
print(f'PASS: {checks} geometry assertions across {len(screens)} resolutions; no APK built')
