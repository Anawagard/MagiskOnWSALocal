from pathlib import Path

root = Path("chatgpt-shahta-v33/project")
source = root / "app/src/main/java/com/bezdna/mine/MineView.java"
gradle = root / "app/build.gradle"
s = source.read_text()

def once(old, new):
    global s
    count = s.count(old)
    assert count == 1, ("v6.4 anchor mismatch", old[:110], count)
    s = s.replace(old, new, 1)

# Behind-ore parallax ornament only. No new touch zones, gameplay state,
# preferences, bitmap allocations or change to the save/export schema.
once("        drawV62OrePedestal(c,biome,bcol);\n        c.save();",
     "        drawV62OrePedestal(c,biome,bcol);\n        drawV64BiomeHalo(c,biome,bcol);\n        c.save();")

method = r"""
    /** Material-specific halo behind the ore, one distinct seeded composition
     *  for each of the 24 biomes. Reuses the existing Paint, no per-frame
     *  Path, Bitmap, Shader, RectF or object allocations.
     */
    private void drawV64BiomeHalo(Canvas c,int biome,int tint){
        final int index=Math.max(0,Math.min(23,biome));
        final int family=index%6;
        final int epoch=index/6;
        final int accent=colorBlend(tint,WHITE,.28f+epoch*.09f);
        final int shadow=colorBlend(tint,0xff06121d,.67f);
        final boolean animate=fxEnabled&&measuredFps>=42f;
        final float phase=animate?(float)(Math.sin(time*1.25f+index*.73f)*.5f+.5f):.45f;
        final float radius=112f+epoch*3.4f;
        final int marks=measuredFps<28f?6:12;
        c.save();
        c.clipRect(19,151,341,507);
        p.reset();p.setAntiAlias(true);
        p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(2.6f+epoch*.32f);
        p.setColor((0x58<<24)|(shadow&0x00ffffff));
        c.drawCircle(180,330,radius+4f,p);
        p.setStrokeWidth(1.25f);
        p.setColor(((animate?(int)(67+phase*44):77)<<24)|(accent&0x00ffffff));
        c.drawCircle(180,330,radius,p);
        // A second, broken orbit gives the 24 compositions different silhouettes.
        p.setStrokeWidth(1.5f+epoch*.2f);
        for(int j=0;j<4;j++){
            float start=(index*17+j*90+12f)%360f;
            float sweep=17f+epoch*4f+(family%3)*3f;
            c.drawArc(180-radius+7,330-radius+7,180+radius-7,330+radius-7,
                start,sweep,false,p);
        }
        for(int i=0;i<marks;i++){
            float angle=(float)(Math.PI*2*i/marks+index*.19f);
            float dx=(float)Math.cos(angle);
            float dy=(float)Math.sin(angle);
            float x=180+dx*radius;
            float y=330+dy*radius;
            float length=5f+epoch*1.3f+(i%3)*1.7f;
            switch(family){
            case 0: // layered sediment / fossil ribs
                c.drawLine(x-dy*length,y+dx*length,x+dy*length,y-dx*length,p);
                c.drawLine(x-dx*3,y-dy*3,x+dx*3,y+dy*3,p);
                break;
            case 1: // precision clockwork / brass gearing
                c.drawLine(x-dx*length,y-dy*length,x+dx*length,y+dy*length,p);
                if((i&1)==0)c.drawCircle(x,y,2.2f,p);
                break;
            case 2: // prism and frost crystal facets
                c.drawLine(x,y,x+dx*length-dy*4,y+dy*length+dx*4,p);
                c.drawLine(x,y,x+dx*length+dy*4,y+dy*length-dx*4,p);
                break;
            case 3: // molten fault lines
                c.drawLine(x-dy*3,y+dx*3,x+dx*length,y+dy*length,p);
                c.drawLine(x+dx*length,y+dy*length,
                    x+dx*(length+4)+dy*3,y+dy*(length+4)-dx*3,p);
                break;
            case 4: // organic root / bioluminescent spore rings
                c.drawLine(x,y,x+dx*length,y+dy*length,p);
                c.drawCircle(x+dx*(length+2),y+dy*(length+2),
                    1.7f+(animate?phase:0f),p);
                break;
            default: // engraved rune / ancient monument ticks
                c.drawLine(x-dy*length,y+dx*length,x+dy*length,y-dx*length,p);
                if((i&1)==0)c.drawLine(x-dx*4,y-dy*4,x+dx*4,y+dy*4,p);
                break;
            }
        }
        // In reduced-motion / low-FPS conditions the ring remains static.
        if(animate){
            p.setStyle(Paint.Style.FILL);
            p.setColor(((int)(42+phase*65)<<24)|(accent&0x00ffffff));
            for(int i=0;i<4;i++){
                float a=(float)(time*.28f+i*Math.PI*.5+index*.37f);
                c.drawCircle(180+(float)Math.cos(a)*(radius-7f),
                    330+(float)Math.sin(a)*(radius-7f),1.6f+phase*.7f,p);
            }
        }
        c.restore();
        p.setStyle(Paint.Style.FILL);
    }
"""
once("    private void drawCaveWeather(Canvas c,int biome,int tint){",
     method + "\n    private void drawCaveWeather(Canvas c,int biome,int tint){")

for invariant in (
    "private void drawV64BiomeHalo(",
    "drawV64BiomeHalo(c,biome,bcol);",
    "final int family=index%6;",
    "final int epoch=index/6;",
    "c.clipRect(19,151,341,507);",
    "drawV63RankTrack(c,",
    "drawV62OrePedestal(c,biome,bcol);",
    '@Override public boolean onTouchEvent(MotionEvent e)',
    'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);',
    "public void save()", "private void rebirth()",
):
    assert invariant in s, invariant
assert s.count("drawV64BiomeHalo(c,biome,bcol);")==1
g = gradle.read_text()
assert "versionCode 40" in g and "versionName '6.3'" in g
assert "signingConfig signingConfigs.shahtaDebug" in g
assert "applicationId 'com.bezdna.mine'" in g
source.write_text(s)
gradle.write_text(g.replace("versionCode 40", "versionCode 41")
                    .replace("versionName '6.3'", "versionName '6.4'"))
print("v6.4: 24 ore halos, six material motifs, four depth epochs, low-FPS budget, saves and debug identity retained")
