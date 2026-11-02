from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()

def once(old,new):
    global s
    assert s.count(old)==1,("v6.1 source anchor mismatch",old[:110],s.count(old))
    s=s.replace(old,new,1)

# Atmospheric foreground only: the mine's existing clip protects HUD and
# touch targets. No changes to saved state, gameplay RNG, or hitboxes.
once("        drawV57BiomeRelics(c,biome,bcol);\n        c.save();",
     "        drawV57BiomeRelics(c,biome,bcol);\n        drawV61Foreground(c,biome,bcol);\n        c.save();")

method=r"""
    // Shared paths avoid heap allocations in the per-frame renderer.
    private final Path v61StrataPath=new Path();
    private final Path v61DetailPath=new Path();

    /** Near-field parallax strata for all 24 biomes, with six material
     *  families and biome-dependent silhouettes, colors and ornamentation.
     *  Everything stays within the existing 18..342 x 149..511 mine clip.
     */
    private void drawV61Foreground(Canvas c,int biome,int tint){
        final int family=biome%6;
        final int shade=colorBlend(tint,0xff07101d,.80f);
        final int edge=colorBlend(tint,0xffa4d6dd,.42f);
        final float sway=fxEnabled&&measuredFps>=38f?
            (float)Math.sin(time*.34f+biome*.71f)*2.5f:0f;
        c.save();
        c.clipRect(18,149,342,511);
        for(int side=0;side<2;side++){
            final float wall=side==0?18f:342f;
            final float dir=side==0?1f:-1f;
            final float breadth=31f+(biome*7+side*13)%19;
            v61StrataPath.reset();
            v61StrataPath.moveTo(wall,149);
            v61StrataPath.lineTo(wall+dir*(breadth*.52f),149);
            for(int j=0;j<8;j++){
                float y=149+j*51f;
                float n=(float)Math.sin(j*1.89+biome*.73+side*1.7);
                float offset=breadth*.56f+n*8f+(j%3)*2f+sway*(j%2);
                v61StrataPath.lineTo(wall+dir*offset,y);
            }
            v61StrataPath.lineTo(wall,511);
            v61StrataPath.close();
            p.reset();p.setAntiAlias(true);p.setColor(shade);
            c.drawPath(v61StrataPath,p);
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(1.6f);
            p.setColor((0x8c<<24)|(edge&0x00ffffff));
            c.drawPath(v61StrataPath,p);
            p.setStyle(Paint.Style.FILL);
            for(int j=0;j<5;j++){
                float y=190+j*66+(biome*3+j*7)%17;
                float x=wall+dir*(18f+(biome*5+j*11)%15);
                float h=8f+(biome+j*3)%14;
                switch(family){
                case 0: // jagged shale and fossils
                    v61DetailPath.reset();
                    v61DetailPath.moveTo(x-dir*7,y+8);
                    v61DetailPath.lineTo(x+dir*4,y-h);
                    v61DetailPath.lineTo(x+dir*11,y+7);
                    v61DetailPath.close();
                    p.setColor(colorBlend(shade,edge,.42f));
                    c.drawPath(v61DetailPath,p);
                    break;
                case 1: // copper machinery and clockwork strata
                    p.setColor(colorBlend(shade,edge,.54f));
                    c.drawRect(x-4,y-10,x+4,y+10,p);
                    p.setColor(edge);
                    c.drawCircle(x,y,2.4f,p);
                    break;
                case 2: // crystalline ridges
                    v61DetailPath.reset();
                    v61DetailPath.moveTo(x,y-h);
                    v61DetailPath.lineTo(x+dir*7,y);
                    v61DetailPath.lineTo(x,y+10);
                    v61DetailPath.lineTo(x-dir*5,y);
                    v61DetailPath.close();
                    p.setColor(colorBlend(shade,edge,.62f));
                    c.drawPath(v61DetailPath,p);
                    break;
                case 3: // fractured magma vents
                    p.setColor(colorBlend(shade,0xffd96e4e,.48f));
                    c.drawRect(x-3,y-h,x+3,y+9,p);
                    p.setColor(edge);
                    c.drawCircle(x,y-h,1.7f,p);
                    break;
                case 4: // hanging roots and fungal strands
                    p.setColor(colorBlend(shade,edge,.66f));
                    p.setStrokeWidth(2.3f);
                    c.drawLine(x,y-h,x+dir*(5+j%4),y+13,p);
                    p.setColor(edge);
                    c.drawCircle(x+dir*(5+j%4),y+13,2.6f,p);
                    break;
                default: // ancient masonry and astral runes
                    p.setColor(colorBlend(shade,edge,.44f));
                    c.drawRect(x-5,y-6,x+5,y+6,p);
                    p.setColor(edge);
                    p.setStrokeWidth(1.3f);
                    c.drawLine(x-3,y,x+3,y,p);
                    c.drawLine(x,y-4,x,y+4,p);
                    break;
                }
            }
        }
        c.restore();
    }
"""
once("    private void drawCaveWeather(Canvas c,int biome,int tint){",
     method+"\n    private void drawCaveWeather(Canvas c,int biome,int tint){")

assert s.count("private void drawV61Foreground(")==1
assert s.count("drawV61Foreground(c,biome,bcol);")==1
assert "c.clipRect(18,149,342,511);" in method
assert "for(int side=0;side<2;side++)" in method
assert "final int family=biome%6;" in method
for required in ('for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);',
                 'public void save()','private void rebirth()',
                 '@Override public boolean onTouchEvent(MotionEvent e)',
                 'drawV60ImpactResonance(c);'):
    assert required in s,required
mine.write_text(s)
g=gradle.read_text()
assert "versionCode 37" in g and "versionName '6.0'" in g
assert "signingConfig signingConfigs.shahtaDebug" in g
assert "applicationId 'com.bezdna.mine'" in g
gradle.write_text(g.replace("versionCode 37","versionCode 38")
                   .replace("versionName '6.0'","versionName '6.1'"))
print("v6.1: layered near-field cave strata, 24 biome variants, unchanged gameplay and saves")
