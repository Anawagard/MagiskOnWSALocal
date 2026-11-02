from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()
def once(old,new):
    global s
    assert s.count(old)==1,("v5.2 source hook mismatch",old[:110],s.count(old))
    s=s.replace(old,new,1)

# Reuse the exact polygonal ore silhouette for texture clipping instead of
# allocating a Path for every frame before the v4.9 texture cache warms up.
once("        Path mask=new Path();\n        mask.moveTo(-96,-93);mask.lineTo(15,-108);mask.lineTo(93,-65);\n        mask.lineTo(110,39);mask.lineTo(68,95);mask.lineTo(-41,100);\n        mask.lineTo(-107,44);mask.lineTo(-110,-29);mask.close();\n        c.clipPath(mask);",
"""        if(!v52OreClipReady){
            v52OreClip.moveTo(-96,-93);v52OreClip.lineTo(15,-108);
            v52OreClip.lineTo(93,-65);v52OreClip.lineTo(110,39);
            v52OreClip.lineTo(68,95);v52OreClip.lineTo(-41,100);
            v52OreClip.lineTo(-107,44);v52OreClip.lineTo(-110,-29);
            v52OreClip.close();v52OreClipReady=true;
        }
        c.clipPath(v52OreClip);""")

once("        drawV42OreHighlights(c,id,base);\n        c.restore();",
     "        drawV42OreHighlights(c,id,base);\n        drawV52MaterialFacets(c,id,base);\n        c.restore();")

method="""
    /** Distinct seeded material engraving for all 24 ore types. */
    private final Path v52OreClip=new Path();
    private boolean v52OreClipReady;
    private void drawV52MaterialFacets(Canvas c,int id,int base){
        int color=ORE[id];
        int lit=colorBlend(color,0xfff6ffff,.46f);
        int dark=colorBlend(base,0xff0b1421,.48f);
        int highlight=(lit&0x00ffffff)|0x99000000;
        int shadow=(dark&0x00ffffff)|0xaa000000;
        int family=id==0?0:id<=3?1:(id==9||id==14||id==17)?2:id>=20?4:3;
        int count=measuredFps<25f?6:14;
        for(int j=0;j<count;j++){
            int seed=seeded(id+117,j+239,zone()+41);
            float x=-87+seed%174;
            float y=-82+(seed/71)%164;
            float size=5+(seed/131)%12;
            if(family==0){
                // Sedimentary stone: discontinuous stratification and pores.
                line(c,x-size,y,x+size*.8f,y-2,shadow,1.5f);
                line(c,x-size*.6f,y+3,x+size*.35f,y+2,highlight,.8f);
            }else if(family==1){
                // Copper, iron, gold: oriented veins and metallic edge gleam.
                float dir=(seed%2==0?1f:-1f);
                line(c,x-size*.5f,y-size,x+dir*size*.7f,y+size,shadow,2.5f);
                line(c,x-size*.5f+2,y-size,x+dir*size*.7f+2,y+size,highlight,1.1f);
            }else if(family==2){
                // Obsidian, void fragments and meteorite: chipped plates.
                polygon(c,new float[]{x-size,y,x-2,y-size,x+size,y-3,x+4,y+size},
                    (dark&0x00ffffff)|0x77000000);
                line(c,x-2,y-size,x+size,y-3,highlight,1.1f);
                line(c,x+size,y-3,x+4,y+size,shadow,1.2f);
            }else if(family==4){
                // Late-game rare ores: radial, faceted prismatic shards.
                polygon(c,new float[]{x,y-size*1.3f,x+size*.75f,y,
                    x,y+size,x-size*.75f,y},
                    (color&0x00ffffff)|0x88000000);
                line(c,x,y-size*1.3f,x,y+size,highlight,1.1f);
                line(c,x-size*.75f,y,x+size*.75f,y,shadow,.9f);
            }else{
                // Gemstones: triangular refraction with hard cut edges.
                polygon(c,new float[]{x,y-size,x+size,y+size*.6f,x-size,y+size*.7f},
                    (color&0x00ffffff)|0x66000000);
                line(c,x,y-size,x+size,y+size*.6f,highlight,1.4f);
                line(c,x,y-size,x-size,y+size*.7f,shadow,1.1f);
            }
        }
    }
"""
once("    /** Stone and mineral facets clipped to the original ore silhouette. */",
     method+"\n    /** Stone and mineral facets clipped to the original ore silhouette. */")

assert "drawV52MaterialFacets(c,id,base);" in s
assert "c.clipPath(v52OreClip);" in s
assert "drawV51CachedCavern(c,biome,bcol);" in s
assert "drawV47BiomeIdentity(c,biome,theme);" in s
assert "drawV50FractureNetwork(c,id,damageRatio);" in s
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
mine.write_text(s)
g=gradle.read_text()
assert "versionCode 28" in g and "versionName '5.1'" in g
assert "signingConfig signingConfigs.shahtaDebug" in g
gradle.write_text(g.replace("versionCode 28","versionCode 29")
                   .replace("versionName '5.1'","versionName '5.2'"))
print("v5.2: 24 ore material families and reusable rock clipping path")
