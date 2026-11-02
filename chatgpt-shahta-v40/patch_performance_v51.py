from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()

def once(old,new):
    global s
    assert s.count(old)==1,("v5.1 source hook mismatch",old[:120],s.count(old))
    s=s.replace(old,new,1)

# The entire static 24-biome environment used to be redrawn at 60 FPS.
# Keep input positions and game logic unchanged; draw expensive background
# layers into a small bounded bitmap and refresh them periodically. Weather,
# moving pickaxe, ore, hit effects, HUD and buttons still render every frame.
once("        drawCavern(c,biome,bcol);\n        drawCaveWeather(c,biome,bcol);",
     "        drawV51CachedCavern(c,biome,bcol);\n        drawCaveWeather(c,biome,bcol);")

method="""
    /** Frame-budgeted 24-biome cave art cache (324 x 362 ARGB, ~458 KiB). */
    private android.graphics.Bitmap v51CavernCache;
    private int v51CachedBiome=-1,v51CachedTint;
    private boolean v51CachedFx,v51CacheUnavailable;
    private long v51CavernRenderedAt;
    private void drawV51CachedCavern(Canvas c,int biome,int tint){
        long now=android.os.SystemClock.uptimeMillis();
        boolean changed=v51CachedBiome!=biome||v51CachedTint!=tint||
            v51CachedFx!=fxEnabled;
        if(v51CavernCache==null&&!v51CacheUnavailable){
            try{
                v51CavernCache=android.graphics.Bitmap.createBitmap(
                    324,362,android.graphics.Bitmap.Config.ARGB_8888);
                changed=true;
            }catch(OutOfMemoryError oom){
                v51CacheUnavailable=true;
            }
        }
        if(v51CavernCache==null){
            drawCavern(c,biome,tint);
            return;
        }
        // Low-end devices retain atmospheric motion via the separate weather
        // layer, while expensive architecture/motifs update less frequently.
        long refresh=fxEnabled?(measuredFps<30f?3500L:1600L):60000L;
        if(changed||now-v51CavernRenderedAt>=refresh){
            v51CavernCache.eraseColor(android.graphics.Color.TRANSPARENT);
            Canvas surface=new Canvas(v51CavernCache);
            surface.translate(-18,-149);
            drawCavern(surface,biome,tint);
            v51CachedBiome=biome;
            v51CachedTint=tint;
            v51CachedFx=fxEnabled;
            v51CavernRenderedAt=now;
        }
        p.reset();p.setAntiAlias(true);p.setFilterBitmap(false);
        c.drawBitmap(v51CavernCache,18,149,p);
    }
"""
once("    private void drawCavern(Canvas c,int biome,int theme){",
     method+"\n    private void drawCavern(Canvas c,int biome,int theme){")

# Recycle the bitmap along with the existing v4.9 ore cache.
once("    @Override protected void onDetachedFromWindow(){\n        if(cachedV49Rock!=null){cachedV49Rock.recycle();cachedV49Rock=null;}",
     "    @Override protected void onDetachedFromWindow(){\n        if(v51CavernCache!=null){v51CavernCache.recycle();v51CavernCache=null;}\n        if(cachedV49Rock!=null){cachedV49Rock.recycle();cachedV49Rock=null;}")

# Cut the non-interactive atmospheric overdraw further on struggling devices.
once("int dustCount=measuredFps<43f?14:28;",
     "int dustCount=measuredFps<25f?7:measuredFps<43f?14:28;")
once("int glowCount=measuredFps<43f?5:9;",
     "int glowCount=measuredFps<25f?2:measuredFps<43f?5:9;")
once("            int count=7+layer*4;",
     "            int count=measuredFps<25f?3+layer*2:7+layer*4;")

# Skip expensive alpha offscreen layers during low-FPS page transitions.
once("        if(pageSlide>0&&previousPage>=0&&previousPage!=page){",
     "        if(measuredFps>=35f&&pageSlide>0&&previousPage>=0&&previousPage!=page){")

# Stable data model and signing identity remain untouched.
assert "drawV51CachedCavern(c,biome,bcol);" in s
assert "drawV47BiomeIdentity(c,biome,theme);" in s
assert "drawV50FractureNetwork(c,id,damageRatio);" in s
assert "drawV50LightShafts(c,biome,theme);" in s
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert "public void save()" in s and "private void rebirth()" in s
mine.write_text(s)
g=gradle.read_text()
assert "versionCode 27" in g and "versionName '5.0'" in g
assert "signingConfig signingConfigs.shahtaDebug" in g
gradle.write_text(g.replace("versionCode 27","versionCode 28")
                   .replace("versionName '5.0'","versionName '5.1'"))
print("v5.1: 24-biome cave bitmap cache, low-FPS particle budget and page-transition fallback")
