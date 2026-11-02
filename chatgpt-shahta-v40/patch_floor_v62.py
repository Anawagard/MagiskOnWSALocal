from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()

def once(old,new):
    global s
    n=s.count(old)
    assert n==1,("v6.2 anchor mismatch",old[:110],n)
    s=s.replace(old,new,1)

# Biome floor and mineral pedestal are purely decorative and drawn behind ore.
# No changes to input, RNG, damage, rewards or persistent data.
once("        drawV61Foreground(c,biome,bcol);\n        c.save();",
     "        drawV61Foreground(c,biome,bcol);\n        drawV62OrePedestal(c,biome,bcol);\n        c.save();")

method=r"""
    // Reused geometry: no Path, bitmap or gradient allocations during frames.
    private final Path v62TerrainPath=new Path();
    /** Twenty-four deterministic floor identities and mining plinths.
     *  These remain behind the mineral and within the original cave viewport.
     */
    private void drawV62OrePedestal(Canvas c,int biome,int tint){
        final int index=Math.max(0,Math.min(23,biome));
        final int family=index%6;
        final int base=colorBlend(tint,0xff07111b,.81f);
        final int accent=colorBlend(tint,WHITE,.48f);
        final float pulse=fxEnabled&&measuredFps>=42f?
            (float)(.77f+.23f*Math.sin(time*1.7f+index*.71f)): .82f;
        c.save();
        c.clipRect(19,149,341,509);
        // Recessed oval floor dais with two restrained etched rims.
        p.reset();p.setAntiAlias(true);p.setColor(base);
        c.drawOval(62,427,298,480,p);
        p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(2.3f);
        p.setColor((0xa0<<24)|(accent&0x00ffffff));
        c.drawOval(62,427,298,480,p);
        p.setStrokeWidth(1.1f);
        p.setColor((0x68<<24)|(accent&0x00ffffff));
        c.drawOval(77,435,283,470,p);
        p.setStyle(Paint.Style.FILL);
        // The rock hides the centre of the dais; floor strata remain visible.
        v62TerrainPath.reset();
        v62TerrainPath.moveTo(19,501);
        for(int i=0;i<=16;i++){
            float x=19+i*20.125f;
            float ridge=(float)Math.sin(i*1.71+index*.53f)*4f;
            float y=490f+(index*7+i*13)%11+ridge;
            v62TerrainPath.lineTo(x,y);
        }
        v62TerrainPath.lineTo(341,509);
        v62TerrainPath.lineTo(19,509);
        v62TerrainPath.close();
        p.setColor(colorBlend(base,accent,.16f));
        c.drawPath(v62TerrainPath,p);
        // Material-specific glyphs: six visual families, twenty-four seeds.
        for(int i=0;i<11;i++){
            float x=33+i*29f;
            float y=488f+(index*3+i*7)%12;
            float size=3f+(index+i*5)%7;
            p.setColor((0x9c<<24)|(accent&0x00ffffff));
            switch(family){
            case 0: // sediment and fossil strata
                c.drawRect(x-size,y,x+size,y+1.5f,p);
                c.drawCircle(x,y-3,1.1f,p);
                break;
            case 1: // brass and clockwork teeth
                c.drawRect(x-2,y-size,x+2,y+3,p);
                c.drawRect(x-5,y-1,x+5,y+1,p);
                break;
            case 2: // prismatic ice and gemstone spikes
                v62TerrainPath.reset();
                v62TerrainPath.moveTo(x-size,y+3);
                v62TerrainPath.lineTo(x,y-size*1.6f);
                v62TerrainPath.lineTo(x+size,y+3);
                v62TerrainPath.close();
                c.drawPath(v62TerrainPath,p);
                break;
            case 3: // volcanic fissures
                p.setStrokeWidth(1.7f);
                c.drawLine(x-4,y-4,x+1,y+2,p);
                c.drawLine(x+1,y+2,x+5,y-2,p);
                break;
            case 4: // organic roots and luminescent spores
                p.setStrokeWidth(1.8f);
                c.drawLine(x,y+4,x-3,y-size,p);
                c.drawCircle(x-3,y-size,1.5f+pulse,p);
                break;
            default: // ancient rune tablets
                c.drawRect(x-4,y-5,x+4,y+4,p);
                p.setColor(base);
                c.drawRect(x-1,y-3,x+1,y+2,p);
                break;
            }
        }
        // Individual constellation of small mineral studs around the dais.
        for(int i=0;i<6;i++){
            float a=(float)(index*.29+i*Math.PI/3);
            float x=180f+(float)Math.cos(a)*103f;
            float y=451f+(float)Math.sin(a)*17f;
            p.setColor((Math.min(255,(int)(pulse*170))<<24)|(accent&0x00ffffff));
            c.drawCircle(x,y,1.4f+(index+i)%3*.35f,p);
        }
        c.restore();
        p.setStyle(Paint.Style.FILL);
    }
"""
once("    private void drawCaveWeather(Canvas c,int biome,int tint){",
     method+"\n    private void drawCaveWeather(Canvas c,int biome,int tint){")

for hook in ("private void drawV62OrePedestal(","drawV62OrePedestal(c,biome,bcol);",
             "v62TerrainPath.reset();","c.clipRect(19,149,341,509);"):
    assert hook in s,hook
for invariant in ('for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);',
                  'public void save()','private void rebirth()',
                  '@Override public boolean onTouchEvent(MotionEvent e)',
                  'drawV61Foreground(c,biome,bcol);'):
    assert invariant in s,invariant
g=gradle.read_text()
assert "versionCode 38" in g and "versionName '6.1'" in g
assert "signingConfig signingConfigs.shahtaDebug" in g
assert "applicationId 'com.bezdna.mine'" in g
mine.write_text(s)
gradle.write_text(g.replace("versionCode 38","versionCode 39")
                   .replace("versionName '6.1'","versionName '6.2'"))
print("v6.2: 24 material-specific cave floors, recessed ore plinths, cached paths; game and save unchanged")
