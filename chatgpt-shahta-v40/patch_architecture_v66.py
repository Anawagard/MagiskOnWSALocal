"""v6.6: twenty-four material engravings and architectural cave sidewalls.

Pure Canvas art: no new input targets, state, preferences or allocations in frames.
"""
from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()

def once(before,after):
    global s
    count=s.count(before)
    assert count==1,("v6.6 hook mismatch",before[:110],count)
    s=s.replace(before,after,1)

input_before=s[s.index("    @Override public boolean onTouchEvent(MotionEvent e)"):]
once("        drawV64BiomeHalo(c,biome,bcol);",
     "        drawV64BiomeHalo(c,biome,bcol);\n        drawV66CaveArchitecture(c,biome,bcol);")
once("        drawV53LivingOreGlints(c,id,damageRatio);",
     "        drawV53LivingOreGlints(c,id,damageRatio);\n        drawV66OreEngraving(c,id,damageRatio);")

architecture=r"""
    /** Distinct wall reliefs for six materials across four depth epochs.
     *  All 24 biomes have a different color, orientation and spacing.
     *  Restrained side columns never cover the ore or touch navigation.
     */
    private void drawV66CaveArchitecture(Canvas c,int biome,int tint){
        final int index=Math.max(0,Math.min(23,biome));
        final int family=index%6,epoch=index/6;
        final int shade=colorBlend(tint,0xff06101b,.76f);
        final int accent=colorBlend(tint,WHITE,.32f+epoch*.08f);
        final boolean animate=fxEnabled&&measuredFps>=42f;
        final float pulse=animate?
            (float)(.64f+.36f*Math.sin(time*1.2f+index*.67f)):.70f;
        c.save();
        c.clipRect(19,155,341,506);
        p.reset();p.setAntiAlias(true);
        for(int side=0;side<2;side++){
            final float x=side==0?31f:329f;
            final float sign=side==0?1f:-1f;
            p.setStyle(Paint.Style.FILL);p.setColor(shade);
            c.drawRoundRect(x-10,172,x+10,500,4,4,p);
            p.setColor((0x55<<24)|(accent&0x00ffffff));
            c.drawRect(x+sign*7,179,x+sign*8,497,p);
            p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(1.6f);
            p.setColor(((int)(65+48*pulse)<<24)|(accent&0x00ffffff));
            c.drawLine(x-sign*5,180,x-sign*5,496,p);
            for(int j=0;j<7;j++){
                final float y=198+j*43f+epoch*2f;
                final float width=4f+(j+index)%3*1.5f;
                switch(family){
                case 0: // fossil strata
                    c.drawArc(x-width,y-7,x+width,y+7,20,145,false,p);
                    c.drawLine(x-sign*width,y,x+sign*width,y,p);
                    break;
                case 1: // mechanical rivets
                    c.drawCircle(x,y,3.6f,p);
                    c.drawLine(x-6,y-5,x+6,y+5,p);
                    break;
                case 2: // crystalline icicles
                    c.drawLine(x,y-10,x+sign*width,y,p);
                    c.drawLine(x+sign*width,y,x,y+10,p);
                    c.drawLine(x,y+10,x-sign*width,y,p);
                    break;
                case 3: // glowing fault line
                    c.drawLine(x-3,y-9,x+3,y-2,p);
                    c.drawLine(x+3,y-2,x-2,y+8,p);
                    break;
                case 4: // organic veins
                    c.drawArc(x-6,y-9,x+6,y+9,side==0?45:155,195,false,p);
                    c.drawCircle(x+sign*4,y-6,2.3f,p);
                    break;
                default: // runic stone
                    c.drawRect(x-5,y-6,x+5,y+6,p);
                    c.drawLine(x-4,y-5,x+4,y+5,p);
                    break;
                }
            }
            p.setStyle(Paint.Style.FILL);
            p.setColor(((int)(80+65*pulse)<<24)|(accent&0x00ffffff));
            for(int j=0;j<3;j++){
                final float y=220f+j*116f+(index%4)*5f;
                c.drawCircle(x+sign*2f,y,1.8f+epoch*.3f,p);
            }
        }
        c.restore();
        p.setStyle(Paint.Style.FILL);
    }
"""

engraving=r"""
    /** Material-specific engraved ore insignia, clipped to each v5.8 shape.
     *  No heap allocations; animation pauses when effects are off or FPS drops.
     */
    private void drawV66OreEngraving(Canvas c,int id,float damageRatio){
        final int index=Math.max(0,Math.min(23,id));
        final int family=index%6,epoch=index/6;
        final int accent=colorBlend(ORE[index],WHITE,.52f+epoch*.06f);
        final boolean animate=fxEnabled&&measuredFps>=42f;
        final float phase=animate?
            (float)(.5f+.5f*Math.sin(time*1.65f+index*.37f)):.5f;
        final float radius=27f+epoch*3f;
        final int opacity=Math.max(35,Math.min(148,
            (int)(66f+phase*31f-damageRatio*26f+epoch*7f)));
        c.save();
        c.clipPath(v58RockShape(index));
        c.rotate(index*13f);
        p.reset();p.setAntiAlias(true);
        p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(1.6f);
        p.setColor((opacity<<24)|(accent&0x00ffffff));
        c.drawCircle(0,0,radius,p);
        p.setStrokeWidth(.9f);
        c.drawArc(-radius-5,-radius-5,radius+5,radius+5,
            index*17f,72f+epoch*12f,false,p);
        for(int i=0;i<12;i++){
            final float a=(float)(Math.PI*i/6);
            final float dx=(float)Math.cos(a),dy=(float)Math.sin(a);
            final float r=radius+3f;
            final float length=(i+index)%3==0?7f:3.5f;
            c.drawLine(dx*r,dy*r,dx*(r+length),dy*(r+length),p);
        }
        p.setStrokeWidth(2f);
        switch(family){
        case 0: // sediment / fossil shell
            for(int i=0;i<4;i++)
                c.drawArc(-20+i*3,-18+i*3,20-i*3,18-i*3,
                    24+i*18,230-i*27,false,p);
            break;
        case 1: // brass clockwork gear
            c.drawCircle(0,0,13,p);
            for(int i=0;i<8;i++){
                float a=(float)(Math.PI*i/4);
                c.drawLine((float)Math.cos(a)*14,(float)Math.sin(a)*14,
                    (float)Math.cos(a)*20,(float)Math.sin(a)*20,p);
            }
            break;
        case 2: // six-point prismatic snowflake
            for(int i=0;i<3;i++){
                float a=(float)(Math.PI*i/3);
                float dx=(float)Math.cos(a),dy=(float)Math.sin(a);
                c.drawLine(-dx*19,-dy*19,dx*19,dy*19,p);
            }
            break;
        case 3: // volcanic fracture
            c.drawLine(-16,-18,2,-4,p);
            c.drawLine(2,-4,-5,9,p);
            c.drawLine(-5,9,15,20,p);
            c.drawLine(2,-4,17,-12,p);
            break;
        case 4: // root and leaf
            c.drawArc(-17,-21,17,21,60,220,false,p);
            c.drawOval(-4,-18,10,-3,p);
            c.drawOval(-11,3,5,18,p);
            break;
        default: // engraved rune diamond
            c.drawLine(0,-21,17,0,p);
            c.drawLine(17,0,0,21,p);
            c.drawLine(0,21,-17,0,p);
            c.drawLine(-17,0,0,-21,p);
            c.drawLine(-8,0,8,0,p);
            c.drawLine(0,-9,0,9,p);
            break;
        }
        if(animate&&index>=4){
            p.setStyle(Paint.Style.FILL);
            p.setColor(((int)(phase*105)<<24)|(accent&0x00ffffff));
            c.drawCircle(0,0,2.5f+phase*1.2f,p);
        }
        c.restore();
        p.setStyle(Paint.Style.FILL);
    }
"""
once("    private void drawCaveWeather(Canvas c,int biome,int tint){",
     architecture+"\n    private void drawCaveWeather(Canvas c,int biome,int tint){")
once("    private void drawRock(Canvas c,int id,int theme){",
     engraving+"\n    private void drawRock(Canvas c,int id,int theme){")

assert s[s.index("    @Override public boolean onTouchEvent(MotionEvent e)"):]==input_before
for name in ("drawV66CaveArchitecture","drawV66OreEngraving"):
    assert s.count("private void "+name+"(")==1
    assert s.count(name+"(c,")==1
for old in ('drawV64BiomeHalo(c,biome,bcol);',
            'drawV53LivingOreGlints(c,id,damageRatio);',
            'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);',
            'private int zoneNo(){return (depth-1)/25;}',
            'public void save()', 'private void rebirth()'):
    assert old in s,old
g=gradle.read_text()
assert "versionCode 42" in g and "versionName '6.5'" in g
assert "signingConfig signingConfigs.shahtaDebug" in g
assert "applicationId 'com.bezdna.mine'" in g
mine.write_text(s)
gradle.write_text(g.replace("versionCode 42","versionCode 43")
                   .replace("versionName '6.5'","versionName '6.6'"))
print("v6.6: 24 cave sidewall reliefs and 24 ore engravings; unchanged touches, saves and debug identity")
