"""Shahta 7.0: comprehensive raster-material art pack, regenerated deterministically.
24 illustrated cave environments + 24 textured ore sprites + four menu backgrounds +
textured shared panel, button, nav and header skins. No external assets or licenses.
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
# Resolve relative to this script, not the shell working directory.
# This keeps generation and audit pointed at the same Android assets folder.
ROOT=Path(__file__).resolve().parent.parent / "chatgpt-shahta-v33/project"
# Never fabricate an empty Android project when the historical baseline is absent.
# The manual release workflow restores the project before generating art.
_REQUIRED = ("app/build.gradle", "app/src/main/java/com/bezdna/mine/MineView.java",
             "app/src/main/java/com/bezdna/mine/MainActivity.java")
_missing = [name for name in _REQUIRED if not (ROOT / name).is_file()]
if _missing:
    raise SystemExit(f"BLOCKED: Android baseline missing at {ROOT}; required: {_missing}. "
                     "Restore sources before generating raster assets; no files written.")
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
    # Biome-specific foreground geology: four distinct silhouettes repeated
    # with independent palettes and seeded placement across all 24 biomes.
    # Drawn once into the bitmap; no additional runtime Canvas operations.
    motif=index%4
    if motif==0:
        # Jagged crystalline shelves with a narrow luminous ridge.
        for side in (0,1):
            for j in range(9):
                y=int(85+j*43+r.integers(-12,13))
                edge=0 if side==0 else w
                tip=edge+(1 if side==0 else -1)*int(r.integers(17,54))
                d.polygon([(edge,y-18),(tip,y),(edge,y+23)],
                          fill=(20,32,44,160))
                d.line([(edge,y-18),(tip,y)],fill=(*color,125),width=2)
    elif motif==1:
        # Layered sedimentary ledges and fine fossil-like inclusions.
        for j in range(12):
            y=int(65+j*39+r.integers(-9,10))
            span=int(r.integers(34,98))
            d.line([(0,y),(span,y+int(r.integers(-5,6)))],
                   fill=(*color,94),width=3)
            d.line([(w-span,y+8),(w,y+11)],fill=(8,15,25,125),width=4)
    elif motif==2:
        # Rounded mineral nodules with hard opaque cores.
        for j in range(25):
            x=int(r.choice([r.integers(5,82),r.integers(w-82,w-5)]))
            y=int(r.integers(68,h-65)); radius=int(r.integers(3,11))
            d.ellipse((x-radius,y-radius,x+radius,y+radius),
                      fill=(11,24,33,155),outline=(*color,128),width=2)
    else:
        # Fractured volcanic seams, kept outside the central play corridor.
        for side in (0,1):
            for j in range(11):
                x=int(r.integers(4,65)) if side==0 else int(r.integers(w-65,w-4))
                y=int(r.integers(60,h-60))
                d.line([(x,y),(x+int(r.integers(-10,11)),y+15),
                        (x+int(r.integers(-16,17)),y+32)],
                       fill=(232,119,72,110),width=2)
    # Six depth-dependent geological signatures differentiate biomes that share
    # the same foreground motif. Keep these confined to the side walls so
    # navigation labels and the central mining corridor remain readable.
    # Menu scenes use indices 31..34; map them to distinct geological
    # signatures instead of letting all fall through the final branch.
    signature=index//4 if index < 24 else (index-30)%6
    if signature==0:
        # Fine parallel quartz seams.
        for j in range(9):
            y=78+j*46
            d.line([(5,y),(45,y-8),(72,y-4)],fill=(*color,75),width=1)
    elif signature==1:
        # Sparse stratified dark inclusions.
        for j in range(16):
            y=int(r.integers(75,h-55))
            x=int(r.choice([r.integers(6,58),r.integers(w-58,w-6)]))
            d.ellipse((x-3,y-2,x+4,y+2),fill=(8,17,27,125))
    elif signature==2:
        # Narrow, cool mineral fault lines.
        for j in range(8):
            y=int(r.integers(75,h-85))
            d.line([(w-9,y),(w-37,y+12),(w-57,y+9)],
                   fill=(106,198,204,82),width=2)
    elif signature==3:
        # Warm oxidized deposits on both edges.
        for j in range(12):
            y=int(r.integers(72,h-70))
            x=12 if j%2==0 else w-12
            d.ellipse((x-9,y-4,x+9,y+4),fill=(190,104,65,65))
    elif signature==4:
        # Thin intersecting cleavage traces.
        for j in range(12):
            y=int(r.integers(75,h-75))
            x=24 if j%2==0 else w-24
            d.line([(x-12,y-9),(x+8,y+12)],fill=(*color,88),width=1)
    else:
        # Bright pinprick crystals on the peripheral walls.
        for j in range(25):
            y=int(r.integers(70,h-65))
            x=int(r.choice([r.integers(8,60),r.integers(w-60,w-8)]))
            d.point((x,y),fill=(209,240,237,130))
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
    # Correlated chipped edge: an irregular stone contour, not a star/gear.
    nodes=r.normal(0,9.0,18)
    radii=np.interp(np.linspace(0,18,64,endpoint=False),
                    np.arange(19),np.r_[nodes,nodes[0]])
    for a in range(64):
        rad=a*math.tau/64
        dist=113+float(radii[a])+6*math.sin(rad*3+index)+4*math.cos(rad*7+index*.4)
        points.append((150+math.cos(rad)*dist,149+math.sin(rad)*dist*.87))
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
    # Distinct mineral microstructures are baked into the bitmap, never drawn
    # as extra per-frame Canvas geometry. Keep all marks inside the alpha mask.
    grain=Image.new("RGBA",(w,h),(0,0,0,0))
    gd=ImageDraw.Draw(grain,"RGBA")
    if index % 3 == 0:
        # Sedimentary ore: fine, staggered horizontal laminae.
        for j in range(46):
            x=int(r.integers(50,246)); y=int(r.integers(48,249))
            length=int(r.integers(8,31))
            gd.line((x,y,x+length,y+int(r.integers(-3,4))),
                    fill=(229,232,220,75),width=1)
    elif index % 3 == 1:
        # Crystalline ore: intersecting short angular cleavages.
        for j in range(38):
            x=int(r.integers(48,244)); y=int(r.integers(45,245))
            dx=int(r.integers(5,19)); dy=int(r.integers(7,23))
            gd.line([(x-dx,y+dy),(x,y),(x+dx,y+dy//2)],
                    fill=(225,241,242,90),width=1)
    else:
        # Metallic ore: discontinuous diagonal striations.
        for j in range(55):
            x=int(r.integers(52,242)); y=int(r.integers(48,246))
            length=int(r.integers(5,20))
            gd.line((x,y,x+length,y-length//2),
                    fill=(14,23,35,92),width=2)
    # Six mineral families add a second, index-dependent texture signature.
    # All features are rasterized and clipped to the original ore silhouette.
    family=Image.new("RGBA",(w,h),(0,0,0,0))
    fd=ImageDraw.Draw(family,"RGBA")
    motif=index%6
    for j in range(30):
        x=int(r.integers(55,245)); y=int(r.integers(55,242))
        if motif==0:  # sparse quartz flecks
            fd.ellipse((x-2,y-2,x+2,y+2),fill=(239,246,232,92))
        elif motif==1:  # copper oxidation pits
            radius=int(r.integers(2,7))
            fd.ellipse((x-radius,y-radius,x+radius,y+radius),
                       outline=(40,87,77,120),width=2)
        elif motif==2:  # layered silver plates
            fd.line((x-9,y,x+9,y-3),fill=(211,231,238,112),width=2)
        elif motif==3:  # golden granular seams
            fd.line((x-5,y+4,x+3,y-5),fill=(248,205,109,116),width=2)
        elif motif==4:  # dark basalt vesicles
            radius=int(r.integers(2,6))
            fd.ellipse((x-radius,y-radius,x+radius,y+radius),
                       fill=(15,23,35,105))
        else:  # amethyst angular inclusions
            fd.line([(x-5,y),(x,y-8),(x+5,y),(x,y+7),(x-5,y)],
                    fill=(227,202,252,106),width=1)
    family.putalpha(ImageChops.multiply(family.getchannel("A"),mask))
    grain.putalpha(ImageChops.multiply(grain.getchannel("A"),mask))
    im=Image.alpha_composite(im,grain)
    im=Image.alpha_composite(im,family)
    # Baked directional rim lighting makes the stone edge more dimensional.
    # Keep the highlight strictly inside the existing ore silhouette.
    interior=mask.filter(ImageFilter.MinFilter(11))
    rim=ImageChops.subtract(mask,interior)
    rim_alpha=np.asarray(rim,dtype=np.float32)
    yy_r,xx_r=np.mgrid[0:h,0:w].astype(np.float32)
    facing=np.clip(.50-(xx_r-150)/310-(yy_r-149)/310,0,1)
    alpha=np.uint8(np.clip(rim_alpha*facing*.38,0,255))
    light=Image.new("RGBA",(w,h),(225,244,238,0))
    light.putalpha(Image.fromarray(alpha,"L"))
    im=Image.alpha_composite(im,light)
    im.save(path,optimize=True)

def panel_art(path,base,border,size=(400,96),bright=False):
    """Modernist HUD surface: flat midnight titanium, precise hairlines and accent bar."""
    w,h=size
    yy,xx=np.mgrid[0:h,0:w].astype(np.float32)
    # Clean layered gradient, not rock, wood or bevelled medieval UI.
    top=np.asarray(base,dtype=np.float32)
    arr=top[None,None,:]*(.86+.10*(1-yy/h))[:,:,None]
    arr=np.broadcast_to(arr,(h,w,3)).copy()
    arr+=np.maximum(0,1-np.abs(xx-w*.28)/(w*.8))[:,:,None]*2
    # Deterministic fine brushed-metal grain, baked into the raster skin.
    # Keep contrast below 3 RGB levels so labels remain readable and the
    # same asset is produced byte-for-byte on repeated generation.
    grain=(np.sin(xx*.79+yy*.11)*.75 + np.sin(yy*1.91)*.55)
    arr+=grain[:,:,None]
    im=image_array(arr).convert("RGBA")
    d=ImageDraw.Draw(im,"RGBA")
    # Honour the per-surface border palette instead of giving every panel
    # the same grey stroke. Bright controls keep a turquoise focus rail.
    border_rgb=tuple(int(np.clip(channel,0,255)) for channel in border)
    accent=(93,224,210,255) if bright else (*border_rgb,230)
    d.rounded_rectangle((1,1,w-2,h-2),radius=12,
                        outline=(*border_rgb,150 if bright else 118),width=2)
    d.line((15,3,w-15,3),fill=(*accent[:3],85),width=1)
    d.rounded_rectangle((8,9,11,h-10),radius=2,fill=accent)
    if bright:
        d.line((22,h-7,w-22,h-7),fill=(110,241,219,88),width=2)
    # Quiet technical-grid signature: subtle cyan circuitry etched into the
    # top-right corner. Kept entirely in the fixed nine-slice corner region,
    # away from central labels and touch targets. Different surfaces retain
    # the same design language without introducing runtime Canvas work.
    trace_rgb=(93,224,210) if bright else border_rgb
    trace_alpha=105 if bright else 66
    d.line([(w-57,12),(w-43,12),(w-38,17),(w-38,24)],
           fill=(*trace_rgb,trace_alpha),width=1)
    d.ellipse((w-40,22,w-36,26),fill=(*trace_rgb,trace_alpha+35))
    d.line([(w-61,h-16),(w-48,h-16),(w-44,h-20)],
           fill=(*trace_rgb,trace_alpha),width=1)
    # Minimal dual-tone corner indexing distinguishes modernist panels from
    # the old flat buttons without compromising high-contrast text areas.
    d.line((19,h-12,32,h-12),fill=(*trace_rgb,trace_alpha),width=1)
    # Engraved industrial status ticks: bitmap-only detail, no touch/layout changes.
    # Confine marks to the corners so nine-slice stretching never distorts them.
    tick=(112,226,216,118) if bright else (*border_rgb,96)
    for offset in (0,5,10):
        x=w-28+offset
        d.line((x,11,x,16+(offset==0)*4),fill=tick,width=1)
    d.line((w-32,h-12,w-18,h-12),fill=(*border_rgb,85),width=1)
    d.line((w-18,h-12,w-18,h-19),fill=(*border_rgb,85),width=1)
    im.save(path,optimize=True)

for i,color in enumerate(SCENES):
    cave(i,color,OUT/("biome_%02d.jpg"%i))
for i,color in enumerate(ORES):
    ore(i,color,OUT/("ore_%02d.png"%i))
for j,base in enumerate([(59,118,137),(132,74,51),(73,108,133),(101,93,143)],start=1):
    cave(30+j,base,OUT/("menu_%d.jpg"%j))
panel_art(OUT/"panel.png",(23,32,47),(85,125,148))
panel_art(OUT/"button.png",(21,103,109),(92,227,207),size=(160,64),bright=True)
panel_art(OUT/"button_off.png",(32,44,58),(91,112,131),size=(160,64))
panel_art(OUT/"header.png",(17,27,42),(85,132,156),size=(360,88))
panel_art(OUT/"nav.png",(17,28,42),(90,150,164),size=(360,50))
# Crack texture: real alpha-image wear, blended by HP damage at draw time.
crack=Image.new("RGBA",(300,300),(0,0,0,0))
draw=ImageDraw.Draw(crack,"RGBA")
rr=np.random.default_rng(44571)
for j in range(24):
    x=int(rr.integers(40,255));y=int(rr.integers(35,245))
    pts=[(x,y)]
    for segment in range(int(rr.integers(3,8))):
        x+=int(rr.integers(-23,24))
        y+=int(rr.integers(-15,25))
        pts.append((x,y))
    draw.line(pts,fill=(9,13,17,215),width=int(rr.integers(2,5)),joint="curve")
    draw.line([(x0+1,y0+1) for x0,y0 in pts],fill=(218,211,183,112),width=1)
crack.save(OUT/"fractures.png",optimize=True)

# Reuse the separately authored, textured miner sprite rather than a Canvas silhouette.
from redesign_assets import miner as generate_miner_sprite
generate_miner_sprite().save(OUT/"miner.png",optimize=True)
# Verify the *actual decoded output*, including alpha, dimensions and uniqueness.
# Unlike assert, these checks also run under python -O.
from audit_raster_assets_v710 import audit as audit_raster_assets
audit_raster_assets(OUT)
print("V7.0 generated raster art: ",len(list(OUT.iterdir())),"files; bytes",
      sum(p.stat().st_size for p in OUT.iterdir()))