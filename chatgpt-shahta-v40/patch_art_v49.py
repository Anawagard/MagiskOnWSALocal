from pathlib import Path
root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()

def once(old,new):
    global s
    assert s.count(old)==1,("v4.9 source hook mismatch",old[:90],s.count(old))
    s=s.replace(old,new,1)

# Retain all 24 biome-specific motifs; color-grade their cave atmosphere
# and add new geological seams at both side walls (never over touch controls).
once("grad(c,18,149,324,361,0xff152a38,0xff050c16);",
     "grad(c,18,149,324,361,colorBlend(tint,0xff152a38,.82f),colorBlend(tint,0xff050c16,.95f));")
once("        drawBiomeLandmark(c,biome,theme);\n        drawV47BiomeIdentity(c,biome,theme);",
     "        drawBiomeLandmark(c,biome,theme);\n        drawV47BiomeIdentity(c,biome,theme);\n        drawV49Lithology(c,biome,theme);")
lithology="""
    /** Palette-graded geological engravings on the walls of all 24 biomes. */
    private void drawV49Lithology(Canvas c,int biome,int tint){
        final int vein=colorBlend(tint,0xffc3d5d2,.38f);
        final int shade=colorBlend(tint,0xff13202d,.78f);
        for(int side=0;side<2;side++){
            float edge=side==0?21f:339f;
            float dir=side==0?1f:-1f;
            for(int layer=0;layer<9;layer++){
                int seed=seeded(layer+83,biome+37,side+201);
                float y=173+layer*36+(seed%15);
                float length=17+(seed/71)%33;
                float rise=(seed/131)%13-6;
                line(c,edge,y,edge+dir*length,y+rise,shade,3.2f);
                line(c,edge+dir*3,y-1,edge+dir*(length-3),y+rise-1,vein,1.1f);
                if(layer%3==0){
                    float bx=edge+dir*(length*.55f);
                    line(c,bx,y+rise*.55f,bx+dir*6,y+rise*.55f+13,shade,2);
                    line(c,bx+dir,y+rise*.55f,bx+dir*7,y+rise*.55f+12,
                        (tint&0x00ffffff)|0x55000000,1);
                }
            }
        }
        if(fxEnabled){
            float shimmer=(float)(.5+.5*Math.sin(time*.9+biome));
            int alpha=(int)(25+shimmer*45);
            p.reset();p.setAntiAlias(true);
            p.setColor((tint&0x00ffffff)|(alpha<<24));
            c.drawCircle(42,252+(biome%4)*47,6+shimmer*2,p);
            c.drawCircle(317,287+(biome%3)*51,5+shimmer*2,p);
        }
    }
"""
once("    private void drawDeepAtmosphere(Canvas c,int biome,int tint){",
     lithology+"\n    private void drawDeepAtmosphere(Canvas c,int biome,int tint){")
once("    private final Path reusableRidge=new Path();",
     """    private final Path reusableRidge=new Path();
    private android.graphics.Bitmap cachedV49Rock;
    private int cachedV49Depth=-1,cachedV49Ore=-1;
    private long cachedV49Since;
    private boolean v49CacheUnavailable=false;""")
old="""        c.save();
        Path mask=new Path();mask.moveTo(-96,-93);mask.lineTo(15,-108);mask.lineTo(93,-65);
        mask.lineTo(110,39);mask.lineTo(68,95);mask.lineTo(-41,100);
        mask.lineTo(-107,44);mask.lineTo(-110,-29);mask.close();
        c.clipPath(mask);
        drawStoneTexture(c,id,base);
        if(id!=0)drawMineralTexture(c,id);
        drawV42OreHighlights(c,id,base);
        c.restore();"""
once(old,"        drawV49CachedRockTexture(c,id,base);")
methods="""
    /** Stone and mineral facets clipped to the original ore silhouette. */
    private void drawV49RawRockTexture(Canvas c,int id,int base){
        c.save();
        Path mask=new Path();
        mask.moveTo(-96,-93);mask.lineTo(15,-108);mask.lineTo(93,-65);
        mask.lineTo(110,39);mask.lineTo(68,95);mask.lineTo(-41,100);
        mask.lineTo(-107,44);mask.lineTo(-110,-29);mask.close();
        c.clipPath(mask);
        drawStoneTexture(c,id,base);
        if(id!=0)drawMineralTexture(c,id);
        drawV42OreHighlights(c,id,base);
        c.restore();
    }
    private void drawV49CachedRockTexture(Canvas c,int id,int base){
        if(cachedV49Depth!=depth||cachedV49Ore!=id){
            if(cachedV49Rock!=null){cachedV49Rock.recycle();cachedV49Rock=null;}
            cachedV49Depth=depth;
            cachedV49Ore=id;
            cachedV49Since=android.os.SystemClock.uptimeMillis();
        }
        // Delay allocation until a rock survives 180 ms; fast auto-mining
        // does not create a bitmap for every instantly destroyed rock.
        if(cachedV49Rock==null&&!v49CacheUnavailable&&
            android.os.SystemClock.uptimeMillis()-cachedV49Since>=180){
            android.graphics.Bitmap bitmap=null;
            try{
                bitmap=android.graphics.Bitmap.createBitmap(232,232,
                    android.graphics.Bitmap.Config.ARGB_8888);
                Canvas surface=new Canvas(bitmap);
                surface.translate(116,116);
                drawV49RawRockTexture(surface,id,base);
                cachedV49Rock=bitmap;
            }catch(OutOfMemoryError oom){
                if(bitmap!=null)bitmap.recycle();
                v49CacheUnavailable=true;
            }
        }
        if(cachedV49Rock!=null){
            p.reset();p.setAntiAlias(true);p.setFilterBitmap(true);
            c.drawBitmap(cachedV49Rock,-116,-116,p);
        }else{
            drawV49RawRockTexture(c,id,base);
        }
        // Moving specular glints remain live above the cached surface.
        if(fxEnabled&&id!=0){
            int oreTint=ORE[id];
            for(int j=0;j<4;j++){
                float phase=time*(1.15f+j*.14f)+j*1.7f+id*.45f;
                float x=-65+j*42+(float)Math.sin(phase)*4;
                float y=-43+(j%2)*65+(float)Math.cos(phase*.7f)*5;
                float strength=.3f+.32f*(.5f+.5f*(float)Math.sin(phase*2));
                star(c,x,y,2.3f+j*.5f,oreTint,strength);
            }
        }
    }
    @Override protected void onDetachedFromWindow(){
        if(cachedV49Rock!=null){cachedV49Rock.recycle();cachedV49Rock=null;}
        super.onDetachedFromWindow();
    }
"""
once("    private void drawRock(Canvas c,int id,int theme){",
     methods+"\n    private void drawRock(Canvas c,int id,int theme){")
assert "drawV49Lithology(c,biome,theme);" in s
assert "drawV49CachedRockTexture(c,id,base);" in s
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert "public void save()" in s
mine.write_text(s)
g=gradle.read_text()
assert g.count("versionCode 25")==1 and g.count("versionName '4.8'")==1
gradle.write_text(g.replace("versionCode 25","versionCode 26").replace("versionName '4.8'","versionName '4.9'"))
print("v4.9: biome geology and cached rock textures, live glints, saves untouched")
