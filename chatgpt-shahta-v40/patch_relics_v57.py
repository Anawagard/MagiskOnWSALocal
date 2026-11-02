from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()

def once(old,new):
    global s
    assert s.count(old)==1,("v5.7 anchor mismatch",old[:90],s.count(old))
    s=s.replace(old,new,1)

# Draw these behind the ore, pickaxe, and touch UI. They are visual only.
once("        drawV56BiomeWeather(c,biome,bcol);\n        c.save();",
     "        drawV56BiomeWeather(c,biome,bcol);\n        drawV57BiomeRelics(c,biome,bcol);\n        c.save();")

method=r"""
    /** Twenty-four biome-specific relic sets in the cave's edge margins.
     *  Drawn without heap allocation; no game state, RNG or touch coordinates.
     *  Everything is clipped by drawMine's existing viewport clip.
     */
    private void drawV57BiomeRelics(Canvas c,int biome,int tint){
        int light=colorBlend(tint,WHITE,.58f);
        int shade=colorBlend(tint,0xff061422,.70f);
        float pulse=fxEnabled&&measuredFps>32f?
            (float)(.65+.35*Math.sin(time*1.25f+biome)):.72f;
        for(int side=0;side<2;side++){
            float x=side==0?44f:316f;
            float dir=side==0?1f:-1f;
            // Every biome has a distinctive carved vertical fixture.
            line(c,x,208,x,451,0x99415b69,3.0f);
            line(c,x+dir*4,217,x+dir*4,441,shade,1.3f);
            for(int rung=0;rung<4;rung++){
                float y=225+rung*65;
                line(c,x-5,y,x+5,y,0x885b7986,1.4f);
            }
            c.save();
            c.translate(x,side==0?260:385);
            switch(biome){
            case 0: // sandstone: ancient chiseled tablet
                rect(c,-9,-23,18,43,0xff665946);
                line(c,-5,-14,5,-14,light,1.4f);
                line(c,-4,-7,3,-7,0xffad9b72,1);
                line(c,-5,1,5,1,light,1);break;
            case 1: // copper: pressure valve
                p.reset();p.setAntiAlias(true);p.setStyle(Paint.Style.STROKE);
                p.setStrokeWidth(3);p.setColor(0xffa77a50);
                c.drawCircle(0,0,13,p);p.setStyle(Paint.Style.FILL);
                for(int j=0;j<6;j++){
                    float a=(float)(j*Math.PI/3);
                    line(c,(float)Math.cos(a)*5,(float)Math.sin(a)*5,
                        (float)Math.cos(a)*15,(float)Math.sin(a)*15,light,1.5f);
                }break;
            case 2: // emerald: glowing hanging leaves
                for(int j=0;j<4;j++){
                    float y=-20+j*12;
                    line(c,0,y,dir*12,y+8,0xff4cbb8a,2);
                    line(c,dir*12,y+8,dir*3,y+12,light,1);
                }break;
            case 3: // gold: stepped altar insignia
                rect(c,-13,8,26,5,0xffb78b4b);
                rect(c,-9,2,18,6,0xffd4b06a);
                rect(c,-5,-13,10,15,0xff97743f);
                star(c,0,-13,4,light,pulse);break;
            case 4: // ice: suspended icicles
                for(int j=0;j<4;j++){
                    float xx=-12+j*8;
                    line(c,xx,-22,xx+2,10+j%2*8,0xffc5edfa,3.5f);
                    line(c,xx+2,-14,xx+2,5,0x99ffffff,1);
                }break;
            case 5: // scarlet: fractured seal
                p.reset();p.setAntiAlias(true);p.setStyle(Paint.Style.STROKE);
                p.setColor(0xffd76c79);p.setStrokeWidth(2.3f);
                c.drawCircle(0,0,15,p);p.setStyle(Paint.Style.FILL);
                line(c,-12,-12,10,13,light,2);
                line(c,-2,-13,3,3,0xfff1a09a,1.5f);break;
            case 6: // amethyst: hanging violet obelisk
                line(c,0,-28,0,-15,light,1);
                line(c,-8,-15,0,-25,0xffb99eea,2);
                line(c,0,-25,8,-15,0xffb99eea,2);
                line(c,-8,-15,0,19,0xff7d5cb6,3);
                line(c,8,-15,0,19,light,2);break;
            case 7: // lava: furnace vent
                rect(c,-11,-19,22,36,0xff513c3c);
                for(int j=0;j<4;j++)rect(c,-7,-12+j*8,14,3,0xfff0a15a);
                if(fxEnabled)star(c,0,-24,4,0xffffbc72,pulse);break;
            case 8: // drowned: coral branches
                line(c,0,20,0,-18,0xff67c4c7,4);
                line(c,0,-8,-12,-20,0xff90dfe0,2.5f);
                line(c,0,2,12,-10,0xff72d1e2,3);
                line(c,0,13,-9,4,light,2);break;
            case 9: // obsidian: split black blade
                line(c,-8,19,-1,-23,0xff534b6e,7);
                line(c,8,19,1,-23,0xffa87aa4,3);
                line(c,-1,-23,1,-31,light,1);break;
            case 10: // astral: constellation instrument
                p.reset();p.setAntiAlias(true);p.setColor(0xff6b95a8);
                p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(1.3f);
                c.drawCircle(0,0,17,p);c.drawCircle(0,0,10,p);
                p.setStyle(Paint.Style.FILL);
                star(c,0,-17,4,light,pulse);
                star(c,14,7,3,0xffa5f6e7,pulse);break;
            case 11: // old mine: iron rivet column
                rect(c,-10,-23,20,45,0xff465360);
                for(int j=0;j<5;j++){
                    rect(c,-8,-19+j*9,16,2,0xff7e8f96);
                    rect(c,4,-19+j*9,2,2,0xffc4b184);
                }break;
            case 12: // mushroom: stalks and luminous caps
                for(int j=0;j<3;j++){
                    float xx=-12+j*11;
                    line(c,xx,20,xx,-4-j%2*9,0xffad9bb3,3);
                    line(c,xx-6,-4-j%2*9,xx+6,-4-j%2*9,0xfff1a7e8,4);
                }break;
            case 13: // storm: conductor fork
                line(c,0,22,0,-22,0xff698ca5,3);
                line(c,0,-18,-13,-29,light,2);
                line(c,0,-18,13,-29,light,2);
                if(fxEnabled&&pulse>.75f)line(c,-5,-4,6,8,0xff9df3ff,1.4f);break;
            case 14: // glass: prismatic vertical lattice
                for(int j=0;j<3;j++){
                    float xx=-9+j*9;
                    line(c,xx,-19,xx+6,19,0xff9fe7f6,2);
                    line(c,xx+6,19,xx+10,-19,0xff779fb9,1);
                }break;
            case 15: // shadow: hollow mask
                p.reset();p.setAntiAlias(true);p.setColor(0xff615171);
                c.drawOval(-13,-18,13,19,p);
                p.setColor(0xff121626);
                c.drawOval(-9,-11,-2,-1,p);c.drawOval(2,-11,9,-1,p);
                line(c,-5,10,5,10,light,1);break;
            case 16: // meteor: tilted impact rods
                for(int j=0;j<3;j++){
                    float xx=-12+j*11;
                    line(c,xx-5,-24,xx+6,23,0xffac7969,4);
                    line(c,xx-3,-19,xx+3,7,light,1);
                }break;
            case 17: // cathedral: stained glass rose
                p.reset();p.setAntiAlias(true);p.setStyle(Paint.Style.STROKE);
                p.setStrokeWidth(2);p.setColor(0xff9cc4df);
                c.drawCircle(0,0,15,p);p.setStyle(Paint.Style.FILL);
                for(int j=0;j<6;j++){
                    float a=(float)(j*Math.PI/3);
                    line(c,0,0,(float)Math.cos(a)*14,
                        (float)Math.sin(a)*14,light,1.5f);
                }break;
            case 18: // oasis: curved reeds
                for(int j=0;j<3;j++){
                    float xx=-11+j*11;
                    line(c,xx,22,xx+dir*7,-18,0xff85b887,2.5f);
                    line(c,xx+dir*7,-18,xx+dir*12,-10,0xffd2b77e,2);
                }break;
            case 19: // ash citadel: fortress battlements
                rect(c,-13,-15,26,33,0xff654b48);
                for(int j=0;j<3;j++)rect(c,-12+j*10,-22,7,9,0xffb27759);
                line(c,-9,5,9,5,light,1.5f);break;
            case 20: // underwater: pearl shell
                p.reset();p.setAntiAlias(true);p.setColor(0xff356e83);
                c.drawOval(-15,-9,15,18,p);
                for(int j=0;j<5;j++)line(c,0,12,-12+j*6,-7,light,1);
                p.setColor(0xffc1f7f2);c.drawCircle(0,5,4,p);break;
            case 21: // fireflies: lantern cage
                rect(c,-10,-17,20,30,0xff304e3f);
                line(c,-10,-17,0,-24,0xff9cb781,2);
                line(c,0,-24,10,-17,0xff9cb781,2);
                p.reset();p.setAntiAlias(true);p.setColor(0xffddf2a0);
                c.drawCircle(0,-2,4*pulse,p);break;
            case 22: // clockwork: toothed sprocket
                p.reset();p.setAntiAlias(true);p.setStyle(Paint.Style.STROKE);
                p.setStrokeWidth(3);p.setColor(0xffb8a06b);
                c.drawCircle(0,0,13,p);p.setStyle(Paint.Style.FILL);
                for(int j=0;j<8;j++){
                    float a=(float)(j*Math.PI/4);
                    float xx=(float)Math.cos(a)*15, yy=(float)Math.sin(a)*15;
                    line(c,xx*.83f,yy*.83f,xx*1.25f,yy*1.25f,light,3);
                }break;
            case 23: // zenith: celestial crown
                line(c,-13,12,-10,-16,0xffd9bb85,3);
                line(c,-10,-16,0,-5,light,2);
                line(c,0,-5,10,-16,light,2);
                line(c,10,-16,13,12,0xffd9bb85,3);
                line(c,-13,12,13,12,0xffd9bb85,3);
                star(c,0,-19,4,0xffffedb6,pulse);break;
            default:break;
            }
            c.restore();
        }
    }
"""
once("    private void drawCaveWeather(Canvas c,int biome,int tint){",
     method+"\n    private void drawCaveWeather(Canvas c,int biome,int tint){")

assert s.count("private void drawV57BiomeRelics(")==1
assert s.count("drawV57BiomeRelics(c,biome,bcol);")==1
assert all(("case %d:"%i) in method for i in range(24))
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert 'public void save()' in s and 'private void rebirth()' in s
mine.write_text(s)
g=gradle.read_text()
assert "versionCode 33" in g and "versionName '5.6'" in g
assert "signingConfig signingConfigs.shahtaDebug" in g
gradle.write_text(g.replace("versionCode 33","versionCode 34")
                   .replace("versionName '5.6'","versionName '5.7'"))
print("v5.7: 24 unique cave relics, zero allocations per frame, unchanged gameplay/save/signing")
