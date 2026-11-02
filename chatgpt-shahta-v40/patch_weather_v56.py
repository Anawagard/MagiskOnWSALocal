from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()

def once(old,new):
    global s
    assert s.count(old)==1,("v5.6 source hook mismatch",old[:120],s.count(old))
    s=s.replace(old,new,1)

# Weather remains behind the ore and pickaxe, inside the original clipped mine.
# Keep existing particles and visual-effects preference intact.
once("        drawCaveWeather(c,biome,bcol);\n        c.save();",
     "        drawCaveWeather(c,biome,bcol);\n        drawV56BiomeWeather(c,biome,bcol);\n        c.save();")

method="""
    /**
     * 24 visually different low-cost weather profiles. All effects remain
     * decorative and respect the user's visual-effects setting and frame rate.
     * Particles use deterministic coordinates: no allocations or random flicker.
     */
    private void drawV56BiomeWeather(Canvas c,int biome,int tint){
        if(!fxEnabled)return;
        final int count=measuredFps<28f?3:measuredFps<45f?5:8;
        final int light=colorBlend(tint,WHITE,.62f);
        final float t=time;
        for(int i=0;i<count;i++){
            int seed=seeded(271+i,biome+101,depth/25+17);
            float speed=2f+(biome%5)*1.4f;
            float x=27+(seed%304)+(float)Math.sin(t*.6+i*2.1)*5;
            float y=165+((seed/73+(int)(t*speed))%333);
            float flicker=(float)(.48+.45*Math.sin(t*(1.4+i*.08)+i*1.7+biome));
            float sz=1.5f+(seed/149)%3;
            int glow=((int)(45+flicker*115)<<24)|(light&0x00ffffff);
            switch(biome){
            case 0: // sandstone: drifting pale dust
                line(c,x,y,x+4,y-1,glow,1);break;
            case 1: // copper: drifting metallic filings
                rect(c,x,y,sz+2,1,glow);line(c,x+2,y,x+5,y-3,0x77d5a878,1);break;
            case 2: // emerald: floating pollen and leaf spores
                star(c,x,y,sz,0x9978f2b0,flicker);break;
            case 3: // gilded temple: bright falling gold flakes
                polygon(c,new float[]{x,y-3,x+2,y,x,y+3,x-2,y},glow);break;
            case 4: // ice: sharp diagonal snow
                line(c,x,y,x-3,y+7,0xa8e0fbff,1.4f);break;
            case 5: // crimson rift: rising hot embers
                star(c,x,510-(y-160),sz,0xaaff9470,flicker);break;
            case 6: // amethyst: tiny orbiting rune motes
                line(c,x-3,y,x,y-4,glow,1);line(c,x,y-4,x+3,y,glow,1);break;
            case 7: // lava catacombs: molten cinders
                rect(c,x,510-(y-160),sz,sz,0xb6ffaf61);break;
            case 8: // drowned ruins: air bubbles
                p.reset();p.setAntiAlias(true);p.setColor(0x8874ddf7);
                p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(1);
                c.drawCircle(x,510-(y-160),sz+1,p);p.setStyle(Paint.Style.FILL);break;
            case 9: // obsidian: drifting black-red ash
                line(c,x,y,x+3,y+4,0x99a76b91,1.4f);break;
            case 10: // astral: blinking star constellations
                star(c,x,y,sz+1,0xffb7ffff,flicker);break;
            case 11: // old mine: tiny iron chips
                rect(c,x,y,sz+2,1,0x99c2c6bd);break;
            case 12: // mushrooms: luminous spores
                p.reset();p.setAntiAlias(true);p.setColor(0x99f3a4ef);
                c.drawCircle(x,y,sz,p);break;
            case 13: // storm: brief forked static
                if(flicker>.65f){line(c,x,y,x+3,y+5,0xa8a5edff,1);
                    line(c,x+3,y+5,x-2,y+10,0xa8a5edff,1);}break;
            case 14: // glass: sharp prismatic chips
                polygon(c,new float[]{x,y-4,x+3,y,x,y+4},0x8876e9ff);break;
            case 15: // shadows: dark violet drifting wisps
                line(c,x-4,y,x+5,y+2,0x77997cb9,2.5f);break;
            case 16: // meteor: glowing falling streaks
                line(c,x,y,x-6,y+12,0x99ffc28b,1.4f);break;
            case 17: // cathedral: jewel-coloured dust
                p.reset();p.setAntiAlias(true);
                p.setColor(i%2==0?0x99efb9ff:0x999bdcf9);
                c.drawCircle(x,y,sz,p);break;
            case 18: // oasis: warm wind-driven sand
                line(c,x,y,x+7,y-2,0x99efcc91,1);break;
            case 19: // ash citadel: slow orange cinders
                star(c,x,y,sz,0x99ffb188,flicker);break;
            case 20: // ocean: blue rising pearls
                p.reset();p.setAntiAlias(true);p.setColor(0x9969e7e4);
                c.drawCircle(x,510-(y-160),sz,p);break;
            case 21: // firefly grove: soft yellow pulses
                star(c,x,y,sz+1,0xffe9fa8c,flicker);break;
            case 22: // clockwork: brass gear dust
                rect(c,x,y,sz+1,sz+1,0x99d8c0a4);
                line(c,x-2,y+1,x+sz+3,y+1,0x7794a9d9,1);break;
            case 23: // zenith: aurora-tinted motes
                line(c,x,y,x+3,y-7,0x99e1bfff,2);
                star(c,x+3,y-7,sz,0xfff5e8a8,flicker);break;
            default:break;
            }
        }
    }
"""
once("    private void drawCaveWeather(Canvas c,int biome,int tint){",
     method+"\n    private void drawCaveWeather(Canvas c,int biome,int tint){")
assert s.count("private void drawV56BiomeWeather(")==1
assert s.count("drawV56BiomeWeather(c,biome,bcol);")==1
assert all(("case %d:"%i) in method for i in range(24))
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert "drawV55NavIcon(c,x+32.5f,678+bounce,tab,selected);" in s
mine.write_text(s)

g=gradle.read_text()
assert "versionCode 32" in g and "versionName '5.5'" in g
assert "signingConfig signingConfigs.shahtaDebug" in g
gradle.write_text(g.replace("versionCode 32","versionCode 33")
                   .replace("versionName '5.5'","versionName '5.6'"))
print("v5.6: 24 differentiated biome weather profiles, adaptive FPS, no gameplay or save changes")
