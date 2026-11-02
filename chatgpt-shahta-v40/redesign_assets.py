"""Offline raster art pack for the complete redesign; never builds an APK."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import math, random
ROOT=Path("chatgpt-shahta-v33/project/app/src/main/assets/shahta_redesign")
PALETTES=[
((100,122,138),(166,186,195)),((155,93,54),(235,160,91)),
((46,133,94),(129,230,163)),((174,128,54),(255,216,117)),
((74,143,191),(162,238,255)),((167,66,77),(255,125,112)),
((128,89,181),(220,166,255)),((178,91,46),(255,170,80)),
((44,113,165),(123,204,247)),((78,66,115),(179,148,211)),
((55,153,155),(129,243,225)),((166,139,82),(246,221,145)),
((162,77,130),(255,161,205)),((75,113,190),(162,190,255)),
((122,178,190),(224,254,250)),((107,72,150),(206,145,255)),
((170,95,75),(255,169,128)),((155,126,181),(237,205,255)),
((82,141,80),(179,241,126)),((182,101,62),(255,183,117)),
((65,120,170),(158,216,255)),((108,162,80),(215,253,151)),
((145,93,165),(240,163,247)),((178,143,84),(255,225,145))]
def clamp(x):return max(0,min(255,int(x)))
def noise(w,h,seed):
    rng=random.Random(seed)
    img=Image.new("L",(w,h),128)
    for grid,strength in ((5,.34),(13,.28),(31,.23),(81,.19)):
        gw=max(2,round(grid*w/h))
        layer=Image.new("L",(gw,grid))
        layer.putdata([rng.randrange(256) for _ in range(gw*grid)])
        img=Image.blend(img,layer.resize((w,h),Image.Resampling.BICUBIC),strength)
    return list(img.getdata())
def surface(w,h,base,accent,seed,sediment):
    rng=random.Random(seed);values=noise(w,h,seed)
    pixels=[]
    for y in range(h):
        for x in range(w):
            n=(values[y*w+x]-128)*1.5+rng.randrange(-15,16)
            band=math.sin(y*.075+math.sin(x*.019+seed)*8)*12 if sediment else math.sin((x+y)*.05)*7
            bright=.75+.21*(1-y/h)+.12*x/w
            pixels.append(tuple(clamp(v*bright+n+band+(accent[k]-v)*.12) for k,v in enumerate(base)))
    img=Image.new("RGB",(w,h));img.putdata(pixels)
    return img.convert("RGBA")
def cave(i):
    base,accent=PALETTES[i];rng=random.Random(4100+i)
    img=surface(384,512,base,accent,8100+i,True)
    over=Image.new("RGBA",img.size);d=ImageDraw.Draw(over,"RGBA")
    for j in range(24):
        y=rng.randrange(-20,530)
        pts=[(x,y+math.sin(x*.023+j)*rng.randrange(3,13)) for x in range(0,385,12)]
        d.line(pts,fill=(12,22,28,rng.randrange(35,110)),width=rng.randrange(1,5),joint="curve")
    for _ in range(170):
        x=rng.randrange(384);y=rng.randrange(512);r=rng.randrange(1,4)
        d.ellipse((x-r,y-r,x+r,y+r),fill=(*accent,rng.randrange(40,125)))
    return Image.alpha_composite(img,over.filter(ImageFilter.GaussianBlur(.6)))
def ore(i):
    base,accent=PALETTES[i];rng=random.Random(5100+i);size=320
    points=[]
    for j in range(64):
        a=j*math.tau/64
        radius=117+13*math.sin(a*5+i)+rng.randrange(-17,18)
        points.append((160+math.cos(a)*radius,160+math.sin(a)*radius*.92))
    mask=Image.new("L",(size,size));ImageDraw.Draw(mask).polygon(points,fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(1.3))
    img=surface(size,size,base,accent,9200+i,False)
    detail=Image.new("RGBA",img.size);d=ImageDraw.Draw(detail,"RGBA")
    for _ in range(44):
        x=rng.randrange(40,280);y=rng.randrange(40,280);r=rng.randrange(2,12)
        d.ellipse((x-r,y-r,x+r,y+r),fill=(*accent,rng.randrange(50,170)))
        d.arc((x-r,y-r,x+r,y+r),170,300,fill=(255,242,210,110),width=1)
    for _ in range(12):
        x=rng.randrange(65,255);y=rng.randrange(50,245);pts=[(x,y)]
        for j in range(5):
            x+=rng.randrange(-18,19);y+=rng.randrange(7,22);pts.append((x,y))
        d.line(pts,fill=(19,24,34,190),width=3,joint="curve")
    img=Image.alpha_composite(img,detail)
    edge=ImageChops.subtract(mask,mask.filter(ImageFilter.MinFilter(17)))
    shade=Image.new("RGBA",img.size,(12,17,24,0))
    shade.putalpha(edge.point(lambda v:v//2))
    img=Image.alpha_composite(img,shade);img.putalpha(mask)
    return img
def miner():
    img=Image.new("RGBA",(240,340))
    mask=Image.new("L",img.size);d=ImageDraw.Draw(mask)
    d.ellipse((67,48,170,145),fill=255)
    d.polygon([(74,130),(164,130),(190,252),(151,299),(76,293),(46,228)],fill=255)
    d.polygon([(85,270),(118,273),(109,334),(71,332)],fill=255)
    d.polygon([(134,271),(167,261),(191,331),(154,337)],fill=255)
    d.polygon([(59,150),(81,170),(41,245),(21,235)],fill=255)
    d.polygon([(163,155),(183,143),(215,227),(194,237)],fill=255)
    textured=surface(240,340,(106,87,68),(194,158,111),9911,False)
    textured.putalpha(mask.filter(ImageFilter.GaussianBlur(1)))
    img=Image.alpha_composite(img,textured);d=ImageDraw.Draw(img,"RGBA")
    d.polygon([(60,91),(77,56),(147,44),(181,87),(179,104),(59,111)],fill=(207,154,73,255))
    d.arc((60,48,181,119),185,350,fill=(255,223,142,245),width=7)
    d.ellipse((113,75,141,99),fill=(246,235,173,255))
    d.line((91,160,150,185),fill=(230,174,87,255),width=10)
    d.rounded_rectangle((146,155,195,222),radius=8,fill=(50,70,76,220),outline=(202,172,104,255),width=4)
    return img
def plate():
    img=surface(512,128,(36,53,64),(77,104,108),13019,False)
    d=ImageDraw.Draw(img,"RGBA")
    d.rounded_rectangle((4,4,508,124),radius=17,outline=(213,178,109,190),width=3)
    d.line((18,14,494,14),fill=(241,217,151,90),width=2)
    return img
def main():
    ROOT.mkdir(parents=True,exist_ok=True)
    for i in range(24):
        cave(i).save(ROOT/("cave_%02d.png"%i),optimize=True)
        ore(i).save(ROOT/("ore_%02d.png"%i),optimize=True)
    miner().save(ROOT/"miner.png",optimize=True)
    plate().save(ROOT/"plate.png",optimize=True)
    files=list(ROOT.glob("*.png"))
    assert len(files)==50 and all(p.stat().st_size>5000 for p in files)
    print("Raster assets generated:",len(files))
if __name__=="__main__":main()
