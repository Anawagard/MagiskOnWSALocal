from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()

def once(old,new):
    global s
    assert s.count(old)==1,("v5.3 source hook mismatch",old[:120],s.count(old))
    s=s.replace(old,new,1)

# V5.2 texture caching intentionally freezes the expensive mineral engraving.
# A lightweight live specular pass restores motion without rebuilding that cache.
once("        drawV50FractureNetwork(c,id,damageRatio);\n        if(fxEnabled){",
     "        drawV50FractureNetwork(c,id,damageRatio);\n        drawV53LivingOreGlints(c,id,damageRatio);\n        if(fxEnabled){")

method="""
    /** Animated reflections across all 24 ores, independent of the bitmap cache. */
    private void drawV53LivingOreGlints(Canvas c,int id,float damageRatio){
        if(!fxEnabled||measuredFps<24f||!v52OreClipReady)return;
        c.save();
        c.clipPath(v52OreClip);
        int oreColor=ORE[id];
        int bright=colorBlend(oreColor,WHITE,.72f);
        // Sweep across the entire polygon, with only a few translucent strokes.
        float sweep=-148f+(time*(id>=4?19f:12f)+id*17f)%320f;
        int opacity=id==0?22:id<=3?38:61;
        for(int k=0;k<3;k++){
            float x=sweep-k*15f;
            int alpha=Math.max(8,opacity-k*17);
            line(c,x-35,-105,x+27,105,(alpha<<24)|(bright&0x00ffffff),
                k==0?2.4f:1.1f);
        }
        // Per-mineral sparkle constellations are deterministic and allocation-free.
        if(id>=4){
            int count=measuredFps<42f?2:5;
            for(int i=0;i<count;i++){
                int seed=seeded(id+83,i+191,depth/4+11);
                float x=-80+(seed%161);
                float y=-69+(seed/79)%137;
                float phase=(float)(.5+.5*Math.sin(time*(1.1+i*.13)+i*2.2+id));
                if(phase>.68f)star(c,x,y,1.2f+phase*2.1f,bright,.3f+phase*.36f);
            }
        }
        // Cracks reflect ore color only after a meaningful amount of damage.
        if(damageRatio>.35f&&id>=4){
            float strength=Math.min(1f,(damageRatio-.35f)*1.5f);
            int alpha=(int)(28+strength*90);
            int col=(alpha<<24)|(oreColor&0x00ffffff);
            for(int i=0;i<3;i++){
                int seed=seeded(depth/4+41,i+21,id+5);
                float x=-66+(seed%132),y=-55+(seed/43)%108;
                float length=5+strength*13;
                line(c,x,y,x+length,y+length*.7f,col,1.1f);
            }
        }
        c.restore();
    }
"""
once("    private void drawRock(Canvas c,int id,int theme){",
     method+"\n    private void drawRock(Canvas c,int id,int theme){")

assert "drawV53LivingOreGlints(c,id,damageRatio);" in s
assert "drawV52MaterialFacets(c,id,base);" in s
assert "drawV51CachedCavern(c,biome,bcol);" in s
assert "drawV47BiomeIdentity(c,biome,theme);" in s
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
mine.write_text(s)
g=gradle.read_text()
assert "versionCode 29" in g and "versionName '5.2'" in g
assert "signingConfig signingConfigs.shahtaDebug" in g
gradle.write_text(g.replace("versionCode 29","versionCode 30")
                   .replace("versionName '5.2'","versionName '5.3'"))
print("v5.3: cached 24-ore textures now have live glints, dynamic crack highlights and low-FPS fallback")
