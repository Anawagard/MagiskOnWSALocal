"""v6.7: 24 illustrated atlas landscapes and biome-era reliefs.

Atlas artwork only. No changes to hitboxes, gameplay, preferences or backups.
All drawing uses the existing Paint and Canvas primitives, without allocating
Paths, RectFs, Bitmaps, arrays or shaders during a frame.
"""
from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()

def once(before,after):
    global s
    n=s.count(before)
    assert n==1,("v6.7 hook mismatch",before[:110],n)
    s=s.replace(before,after,1)

# Preserve the complete input handler and save/rebirth implementation.
touch_before=s[s.index("    @Override public boolean onTouchEvent(MotionEvent e)"):]
once("        drawOreCrystal(c,cx+1,cy+5,9,tint,fxEnabled?(float)Math.sin(time*2):.5f);",
     "        drawV67AtlasLandscape(c,cx,cy,biome);\n"
     "        drawOreCrystal(c,cx+1,cy+5,9,tint,fxEnabled?(float)Math.sin(time*2):.5f);")

method=r"""
    /** 24 biome mini-landscapes: six geological families x four depth eras.
     *  Rendered inside the existing 48x48 atlas clip, behind the ore crystal.
     *  No new tap regions, state mutations or per-frame heap allocations.
     */
    private void drawV67AtlasLandscape(Canvas c,float cx,float cy,int biome){
        final int index=Math.max(0,Math.min(23,biome));
        final int family=index%6,epoch=index/6;
        final int tint=BIOME[index];
        final int highlight=colorBlend(tint,WHITE,.25f+epoch*.10f);
        final int ridge=colorBlend(tint,0xff081823,.58f);
        final boolean moving=fxEnabled&&measuredFps>=42f;
        final float shimmer=moving?
            (float)(.65f+.35f*Math.sin(time*1.3f+index*.71f)):.70f;
        c.save();
        c.clipRect(cx-23,cy-23,cx+23,cy+23);
        p.reset();p.setAntiAlias(true);p.setStyle(Paint.Style.FILL);
        // Three staggered ridgelines make each miniature read as a real place.
        for(int layer=0;layer<3;layer++){
            final float base=cy-4f+layer*9f;
            final float shift=(index*7+layer*11)%13;
            p.setColor(colorBlend(ridge,highlight,.10f+layer*.10f));
            for(int segment=0;segment<5;segment++){
                float x=cx-25+segment*11f;
                float peak=base-5f-((segment*3+index+layer*2)%5)*1.5f;
                c.drawLine(x,base,x+5.5f+shift*.1f,peak,p);
                c.drawLine(x+5.5f+shift*.1f,peak,x+11,base,p);
            }
        }
        p.setColor((0x90<<24)|(highlight&0x00ffffff));
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(1.15f+epoch*.16f);
        switch(family){
        case 0: // sediment arches, fossil shells
            for(int i=0;i<2+epoch;i++){
                float x=cx-16+i*11f;
                c.drawArc(x-5,cy-14,x+5,cy+1,175,190,false,p);
                c.drawLine(x-4,cy-1,x-4,cy+8,p);
            }
            break;
        case 1: // old mechanical shafts, lift gantries
            for(int i=0;i<2+epoch;i++){
                float x=cx-16+i*10f;
                c.drawRect(x-3,cy-14,x+3,cy+7,p);
                c.drawLine(x-6,cy-11,x+6,cy-11,p);
                c.drawCircle(x,cy-5,2.2f,p);
            }
            break;
        case 2: // ice needles and prismatic caves
            for(int i=0;i<3+epoch;i++){
                float x=cx-18+i*9f;
                c.drawLine(x-4,cy+8,x,cy-15-(i%2)*3,p);
                c.drawLine(x,cy-15-(i%2)*3,x+4,cy+8,p);
                c.drawLine(x-4,cy+8,x+4,cy+8,p);
            }
            break;
        case 3: // magma faults and furnace vents
            for(int i=0;i<2+epoch;i++){
                float x=cx-15+i*11f;
                c.drawLine(x-3,cy+10,x+2,cy-3,p);
                c.drawLine(x+2,cy-3,x-1,cy-10,p);
                c.drawArc(x-5,cy-17,x+7,cy-7,195,145,false,p);
            }
            break;
        case 4: // glowing fungi and roots
            for(int i=0;i<2+epoch;i++){
                float x=cx-15+i*11f;
                c.drawLine(x,cy+10,x,cy-3,p);
                c.drawArc(x-7,cy-11,x+7,cy+1,182,176,false,p);
                c.drawLine(x-3,cy+3,x-7,cy+7,p);
            }
            break;
        default: // runic monoliths and forgotten cities
            for(int i=0;i<2+epoch;i++){
                float x=cx-16+i*11f;
                c.drawRect(x-4,cy-15,x+4,cy+9,p);
                c.drawLine(x-3,cy-10,x+3,cy-4,p);
                c.drawLine(x+3,cy-10,x-3,cy-4,p);
            }
            break;
        }
        // Era marker and a small atmospheric glimmer; static when FPS is low.
        p.setStyle(Paint.Style.FILL);
        p.setColor(((int)(90+70*shimmer)<<24)|(highlight&0x00ffffff));
        for(int i=0;i<=epoch;i++){
            c.drawCircle(cx-18+i*5,cy-18,1.15f,p);
        }
        c.restore();
        p.setStyle(Paint.Style.FILL);
    }
"""
once("    private void drawV43AtlasThumbnail(Canvas c,float cx,float cy,int biome){",
     method+"\n    private void drawV43AtlasThumbnail(Canvas c,float cx,float cy,int biome){")

assert s[s.index("    @Override public boolean onTouchEvent(MotionEvent e)"):]==touch_before
assert s.count("private void drawV67AtlasLandscape(")==1
assert s.count("drawV67AtlasLandscape(c,cx,cy,biome);")==1
assert "drawV66CaveArchitecture(c,biome,bcol);" in s
assert "drawV66OreEngraving(c,id,damageRatio);" in s
assert "private int zoneNo(){return (depth-1)/25;}" in s
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert "public void save()" in s and "private void rebirth()" in s

g=gradle.read_text()
assert "versionCode 43" in g and "versionName '6.6'" in g
assert "signingConfig signingConfigs.shahtaDebug" in g
assert "applicationId 'com.bezdna.mine'" in g
mine.write_text(s)
gradle.write_text(g.replace("versionCode 43","versionCode 44")
                   .replace("versionName '6.6'","versionName '6.7'"))
print("v6.7: 24 atlas landscapes, six material motifs, four eras, no touch/save changes")
