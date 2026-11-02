"""v7.4 shop layout and hitbox regression; Python only, never builds APK."""
from math import isclose
from pathlib import Path

W,H=360,720
screens=[(360,720),(720,1280),(1080,2400),(1272,2772),(1440,3200)]
tabs={"basic":(16,130,124,158),"tech":(128,130,236,158)}
settings=(246,102,345,154)
toolbar=(10,93,350,158)
cards=[(10+(i%2)*175,164+(i//2)*153,165,145) for i in range(6)]
buy=[(x+13,y+102,x+152,y+138) for x,y,_,_ in cards]

def contains(r,x,y):
    a,b,c,d=r
    return a<=x<=c and b<=y<=d

def view(w,h):
    s=min(w/W,h/H)
    return s,(w-W*s)/2,(h-H*s)/2

def roundtrip(x,y,w,h):
    s,ox,oy=view(w,h)
    px,py=x*s+ox,(y+60)*s+oy
    return (px-ox)/s,(py-oy)/s-60

def shop_action(x,y,current_page):
    if contains(settings,x,y):
        return "settings",current_page
    if contains(tabs["basic"],x,y):
        return "basic",0
    if contains(tabs["tech"],x,y):
        return "tech",1
    for i,r in enumerate(buy):
        if contains(r,x,y):
            return "buy",i+(6 if current_page else 0)
    return "none",current_page

patch=Path(__file__).with_name("patch_modernist_v74.py").read_text()
for marker in (
    "if(x>=16&&x<=124){shopPage=0;",
    "if(x>=128&&x<=236){shopPage=1;",
    "if(page==1&&x>=246&&x<=345&&y>=102&&y<=154)",
    "v71ShopTile(c,10+(i%2)*175,164+(i/2)*153",
    "v72NineSlice(c,shopPage==0?",
    "v72NineSlice(c,shopPage==1?",
):
    assert marker in patch,marker

checks=0
assert len(cards)==6 and len(buy)==6
for name,rect in tabs.items():
    assert contains(toolbar,(rect[0]+rect[2])/2,(rect[1]+rect[3])/2)
    assert not contains(settings,(rect[0]+rect[2])/2,(rect[1]+rect[3])/2)
    checks+=1
for i,r in enumerate(buy):
    x,y,w,h=cards[i]
    assert x+13==r[0] and y+102==r[1]
    assert r[2]<=x+w and r[3]<=y+h
    assert r[3]<=653,("clipped purchase button",i,r)
    for j,other in enumerate(buy):
        if i!=j:
            assert not contains(other,(r[0]+r[2])/2,(r[1]+r[3])/2)
    checks+=1

for w,h in screens:
    for tab,rect in tabs.items():
        for x,y in ((rect[0]+1,rect[1]+1),
                    ((rect[0]+rect[2])/2,(rect[1]+rect[3])/2),
                    (rect[2]-1,rect[3]-1)):
            rx,ry=roundtrip(x,y,w,h)
            assert isclose(rx,x,abs_tol=1e-4) and isclose(ry,y,abs_tol=1e-4)
            for current in (0,1):
                action,target=shop_action(rx,ry,current)
                assert (action,target)==(tab,0 if tab=="basic" else 1)
                checks+=1
    for x,y in ((247,103),(295,127),(344,153)):
        rx,ry=roundtrip(x,y,w,h)
        assert shop_action(rx,ry,0)[0]=="settings"
        checks+=1
    for i,r in enumerate(buy):
        for x,y in ((r[0]+1,r[1]+1),
                    ((r[0]+r[2])/2,(r[1]+r[3])/2),
                    (r[2]-1,r[3]-1)):
            rx,ry=roundtrip(x,y,w,h)
            for current in (0,1):
                assert shop_action(rx,ry,current)==("buy",i+6*current)
                checks+=1
    # Between buttons, in decorative margins and the blank space below cards,
    # a tap must not purchase an upgrade or change the shop page.
    for x,y in ((12,131),(126,145),(240,145),(350,130),
                (100,160),(180,309),(180,463),(180,620)):
        rx,ry=roundtrip(x,y,w,h)
        assert shop_action(rx,ry,0)==("none",0),(w,h,x,y)
        checks+=1
print(f"PASS: {checks} source-only shop geometry assertions across {len(screens)} screens")
