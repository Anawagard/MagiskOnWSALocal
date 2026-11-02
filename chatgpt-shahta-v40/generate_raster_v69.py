"""Generate deterministic, non-vector, rasterized cave material textures.
No runtime network, no frame allocations. 24 distinct strata palettes.
"""
from pathlib import Path
from PIL import Image, ImageFilter
import random, math
out=Path("chatgpt-shahta-v33/project/app/src/main/assets/shahta_textures")
out.mkdir(parents=True,exist_ok=True)
palettes=[(84,93,107),(135,104,68),(72,118,111),(106,77,119),(124,81,72),(74,100,139),
(112,86,69),(95,132,112),(72,112,155),(157,92,76),(92,135,93),(139,114,161),
(94,108,136),(151,109,77),(79,144,151),(169,90,102),(122,147,92),(136,112,169),
(79,126,139),(160,124,81),(114,153,163),(175,102,89),(132,153,119),(161,129,179)]
for idx,base in enumerate(palettes):
    rng=random.Random(77001+idx*97)
    w,h=384,384
    coarse=Image.new("L",(24,24))
    coarse.putdata([rng.randrange(256) for _ in range(24*24)])
    coarse=coarse.resize((w,h),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(7))
    fine=Image.new("L",(w,h))
    fine.putdata([rng.randrange(256) for _ in range(w*h)])
    a=list(coarse.getdata()); b=list(fine.getdata())
    pixels=[]
    for y in range(h):
        for x in range(w):
            k=y*w+x
            # Layered, non-geometric sediment with mineral flecks.
            strata=math.sin(y*.095+math.sin(x*.021+idx)*8)*12
            n=(a[k]-128)*.37+(b[k]-128)*.18+strata
            fleck=(rng.random()<.0018)
            pixels.append(tuple(max(0,min(255,int(v+n+(58 if fleck else 0)))) for v in base))
    im=Image.new("RGB",(w,h));im.putdata(pixels)
    im.save(out/f"biome_{idx:02}.png",optimize=True)
print("Created 24 384px raster rock textures:",sum(p.stat().st_size for p in out.glob("*.png")),"bytes")
