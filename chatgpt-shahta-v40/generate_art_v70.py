"""Shahta 7.0: comprehensive raster-material art pack, regenerated deterministically.
24 illustrated cave environments + 24 textured ore sprites + four menu backgrounds +
textured shared panel, button, nav and header skins. No external assets or licenses.
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
ROOT=Path("chatgpt-shahta-v33/project")
OUT=ROOT/"app/src/main/assets/shahta_v70"
OUT.mkdir(parents=True,exist_ok=True)
SCENES=[
(106,128,148),(169,114,74),(69,157,122),(188,148,78),(93,171,199),(176,82,91),
(139,108,192),(194,98,65),(74,132,188),(114,91,143),(78,166,171),(177,160,103),
(165,98,153),(86,126,183),(151,189,203),(119,82,163),(166,104,96),(160,125,187),
(121,180,101),(196,120,76),(85,150,191),(151,192,100),(160,112,196),(194,160,117)]
ORES=[
(130,146,161),(200,118,65),(160,174,190),(237,174,60),(55,194,135),(75,166,225),
(218,66,93),(150,99,216),(185,225,237),(73,63,110),(68,210,224),(222,113,52),
(137,209,242),(183,143,219),(129,113,208),(229,204,108),(116,213,237),(152,141,161),
(234,139,178),(160,214,90),(217,165,76),(191,181,224),(246,205,89),(193,137,239)]
R=Image.Resampling.BICUBIC

def field(w,h,seed):
    r=np.random.default_rng(seed)
    z=np.zeros((h,w),dtype=np.float32)
    for k,weight in [(45,.42),(19,.32),(7,.18),(3,.08)]:
        small=r.integers(0,256,(max(2,h//k),max(2,w//k)),dtype=np.uint8)
        resized=np.asarray(Image.fromarray(small).resize((w,h),R),dtype=np.float32)
        z+=(resized-128)*weight
    z+=r.normal(0,9,(h,w))
    return z

def image_array(arr, mode="RGB"):
    return Image.fromarray(np.uint8(np.clip(arr,0,255)),mode)

def cave(index,color,path,w=360,h=570):
    r=np.random.default_rng(99011+index*71)
    rock=field(w,h,index*117+69)
    xx,yy=np.meshgrid(np.arange(w,dtype=np.float32),
                      np.arange(h,dtype=np.float32))
    strata=np.sin(yy*.095+np.sin(xx*.027+index)*4.5)*12
    displace=np.sin(yy*.017+xx*.012+index)*8
    # Rough limestone, crystal, coal and volcanic wall textures, not canvas polygons.
    tone=rock*.9+strata+displace
    left=np.exp(-((xx-24)/(w*.26))**2)
    right=np.exp(-((xx-(w-24))/(w*.27))**2)
    wall=np.maximum(left,right)
    aperture=np.exp(-(((xx-w*.5)/(w*.39))**2+
                       ((yy-h*.48)/(h*.61))**2)*1.1)
    shade=.19+.32*wall+.16*(1-aperture)+.14*(yy/h)
    ceiling=np.clip(1-(yy/(h*.48)),0,1)*.10
    shade=shade+ceiling
    base=np.asarray(color,dtype=np.float32)
    rgb=base[None,None,:]*shade[:,:,None]+tone[:,:,None]*(.75+wall[:,:,None]*.35)
    rgb[:,:,2]+=4+10*aperture
    rgb[:,:,0]+=12*(yy/h)
    im=image_array(rgb)
    d=ImageDraw.Draw(im,"RGBA")
    # Distinct layered real-pixel mineral veins, tiny fossil and fault networks.
    for j in range(75):
        x=int(r.integers(0,w));y=int(r.integers(0,h))
        length=int(r.integers(9,65))
        points=[(x,y)]
        dx=float(r.uniform(-.75,.75))
        for k in range(0,length,4):
            dx=np.clip(dx+r.uniform(-.3,.3),-1.5,1.5)
            x+=int(dx*4);y+=int(r.uniform(1.3,3.9))
            points.append((x,y))
        bright=r.random()<.35
        ink=(int(color[0]*.8+50),int(color[1]*.8+42),
             int(color[2]*.8+55),int(r.integers(45,112))) if bright else (8,12,22,115)
        d.line(points,fill=ink,width=int(r.integers(1,4)),joint="curve")
    # Ground strata and hand-built timber support silhouettes baked into backdrop.
    d.polygon([(0,510),(45,493),(105,519),(153,506),(223,525),
               (280,504),(360,516),(360,570),(0,570)],fill=(14,19,29,115))
    if index%6 in (0,1,5):
        for x in (36,318):
            d.line([(x,55),(x-3,490)],fill=(83,53,37,143),width=13)
            d.line([(x+2,55),(x,490)],fill=(212,150,87,50),width=3)
        d.arc((36,52,322,266),180,357,fill=(120,83,56,110),width=9)
    elif index%6 in (2,4):
        for j in range(14):
            x=int(r.choice([r.integers(0,78),r.integers(270,360)]))
            cy=int(r.integers(80,480)); rad=int(r.integers(4,15))
            d.ellipse((x-rad,cy-rad,x+rad,cy+rad),outline=(*color,100),width=2)
    elif index%6==3:
        for j in range(8):
            x=int(r.integers(0,360));cy=int(r.integers(70,510))
            d.line([(x,cy),(x+8,cy+17),(x-2,cy+31)],fill=(255,139,63,95),width=3)
    # Subtle dark vignette fixed in the image (no per-frame glow).
    im.save(path,quality=88,optimize=True)

def ore(index,color,path):
    w=h=300
    r=np.random.default_rng(1000+index*313)
    noise=field(w,h,6000+index*257)
    yy,xx=np.mgrid[0:h,0:w].astype(np.float32)
    lightsource=45*(.5-(xx-w*.50)/w)-36*((yy-h*.40)/h)
    shade=1.01-(np.sqrt(((xx-151)/143)**2+((yy-140)/143)**2))*.26
    tone=(noise*.95+lightsource)*shade
    base=np.asarray(color,dtype=np.float32)
    detail=np.sin(xx*.16+noise*.028)*9+np.sin(yy*.22+noise*.035)*7
    rgb=np.zeros((h,w,3),dtype=np.float32)
    for channel in range(3):
        rgb[:,:,channel]=base[channel]*(.70+shade*.23)+tone*.8+detail*.5
    mask=Image.new("L",(w,h));md=ImageDraw.Draw(mask)
    points=[]
    for a in range(64):
        rad=a*math.tau/64
        dist=r.uniform(103,132)
        if a%7==0:dist+=12
        points.append((150+math.cos(rad)*dist,149+math.sin(rad)*dist*.91))
    md.polygon(points,fill=255)
    md.ellipse((87,74,210,220),fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(.55))
    im=image_array(rgb).convert("RGBA")
    im.putalpha(mask)
    art=Image.new("RGBA",(w,h))
    d=ImageDraw.Draw(art,"RGBA")
    # Irregular vein deposits and cracks are baked into ore textures.
    for j in range(100):
        x=int(r.integers(24,271));y=int(r.integers(23,273))
        k=int(r.integers(3,19))
        mineral=(int(min(255,color[0]*1.15+25)),int(min(255,color[1]*1.15+25)),
                 int(min(255,color[2]*1.15+25)),int(r.integers(35,125)))
        if j%5==0:
            pts=[(x,y),(x+r.integers(-8,9),y+r.integers(5,15)),
                 (x+r.integers(-15,16),y+k+12)]
            d.line(pts,fill=(18,17,27,135),width=int(r.integers(1,3)))
            d.line([(x+1,y),(pts[1][0]+1,pts[1][1])],fill=mineral,width=1)
        else:
            d.ellipse((x-k//3,y-k//3,x+k//3,y+k//3),fill=mineral)
    overlay=Image.new("L",(w,h),0)
    overlay.paste(art.getchannel("A"))
    overlay=ImageChops.multiply(overlay,mask)
    art.putalpha(overlay)
    im=Image.alpha_composite(im,art)
    # Hand-engraved texture edge shadows (pre-rendered bitmap, not frame geometry).
    shadow=ImageChops.subtract(mask,mask.filter(ImageFilter.MinFilter(9)))
    dark=Image.new("RGBA",(w,h),(9,12,21,0))
    dark.putalpha(shadow.point(lambda v:int(v*.66)))
    im=Image.alpha_composite(im,dark)
    # Mineral highlights at randomized fractures.
    highlights=Image.new("RGBA",(w,h))
    hi=ImageDraw.Draw(highlights,"RGBA")
    for j in range(14):
        x=int(r.integers(55,240));y=int(r.integers(55,238))
        pts=[(x,y),(x+int(r.integers(-7,6)),y+int(r.integers(5,16))),
             (x+int(r.integers(-15,15)),y+int(r.integers(18,40)))]
        hi.line(pts,fill=(244,241,229,105),width=int(r.integers(1,3)))
    alpha=ImageChops.multiply(highlights.getchannel("A"),mask)
    highlights.putalpha(alpha)
    im=Image.alpha_composite(im,highlights)
    im.save(path,optimize=True)

def panel_art(path,base,border,size=(400,96),bright=False):
    w,h=size
    noise=field(w,h,2029+sum(base))
    xx,yy=np.meshgrid(np.arange(w,dtype=np.float32),np.arange(h,dtype=np.float32))
    factor=.72+.10*(1-yy/h)+.10*np.sin(yy/h*math.pi)
    arr=np.array(base,dtype=np.float32)[None,None,:]*factor[:,:,None]+noise[:,:,None]*.45
    im=image_array(arr)
    d=ImageDraw.Draw(im,"RGBA")
    d.rounded_rectangle((2,2,w-3,h-3),radius=13,outline=(*border,225),width=3)
    d.line((18,6,w-18,6),fill=(245,228,193,83),width=2)
    d.line((17,h-9,w-17,h-9),fill=(9,12,21,180),width=3)
    im.save(path,optimize=True)

for i,color in enumerate(SCENES):
    cave(i,color,OUT/("biome_%02d.jpg"%i))
for i,color in enumerate(ORES):
    ore(i,color,OUT/("ore_%02d.png"%i))
for j,base in enumerate([(59,118,137),(132,74,51),(73,108,133),(101,93,143)],start=1):
    cave(30+j,base,OUT/("menu_%d.jpg"%j))
panel_art(OUT/"panel.png",(39,48,59),(170,155,116))
panel_art(OUT/"button.png",(51,112,116),(186,224,208),size=(160,64),bright=True)
panel_art(OUT/"button_off.png",(49,62,70),(95,118,126),size=(160,64))
panel_art(OUT/"header.png",(27,42,57),(184,158,112),size=(360,88))
panel_art(OUT/"nav.png",(22,41,52),(154,185,182),size=(360,50))
assert len(list(OUT.glob("ore_*.png")))==24
assert len(list(OUT.glob("biome_*.jpg")))==24
print("V7.0 generated raster art: ",len(list(OUT.iterdir())),"files; bytes",
      sum(p.stat().st_size for p in OUT.iterdir()))