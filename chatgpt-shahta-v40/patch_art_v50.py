from pathlib import Path
root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()
def once(old,new):
    global s
    assert s.count(old)==1,("v5.0 source hook mismatch",old[:100],s.count(old))
    s=s.replace(old,new,1)

once("        drawV4Scene(c,biome,theme);\n        // Distinct depths",
     "        drawV4Scene(c,biome,theme);\n        drawV50LightShafts(c,biome,theme);\n        // Distinct depths")
light="""
    /** Subtle translucent mineral light shafts, individually seeded for 24 biomes. */
    private void drawV50LightShafts(Canvas c,int biome,int tint){
        if(!fxEnabled)return;
        for(int j=0;j<3;j++){
            int seed=seeded(biome+17,j+91,213);
            float x=45+seed%265;
            float sway=(float)Math.sin(time*.24f+j*1.4f+biome)*5;
            float w=13+(seed/67)%24;
            float reach=215+(seed/97)%105;
            int alpha=(int)(15+7*(.5+.5*Math.sin(time*.6+j+biome)));
            polygon(c,new float[]{x-w*.25f,151,x+w*.25f,151,
                x+sway+w,151+reach,x+sway-w,151+reach},
                (tint&0x00ffffff)|(alpha<<24));
            line(c,x,158,x+sway*.65f,151+reach*.62f,
                (tint&0x00ffffff)|0x19000000,1.2f);
        }
    }
"""
once("    private void drawV49Lithology(Canvas c,int biome,int tint){",
     light+"\n    private void drawV49Lithology(Canvas c,int biome,int tint){")
old="""        if(damageRatio>.23f){
            int breaks=damageRatio>.72?6:damageRatio>.45?4:2;
            for(int j=0;j<breaks;j++){
                int x=-55+j*20,y=-45+(j*35)%85;
                line(c,x,y,x+14,y+12,0xdd10141f,2+(j%2));
                line(c,x+14,y+12,x+4,y+24,0xbb10141f,2);
                if(id>=4&&j%2==0)line(c,x+1,y+1,x+10,y+13,(0xaa<<24)|(ORE[id]&0xffffff),2);
            }
        }"""
once(old,"        drawV50FractureNetwork(c,id,damageRatio);")
fracture="""
    /** Progressive fractures branch within the original rock silhouette. */
    private final Path v50FractureMask=new Path();
    private boolean v50FractureMaskReady;
    private void drawV50FractureNetwork(Canvas c,int id,float damageRatio){
        if(damageRatio<=.08f)return;
        if(!v50FractureMaskReady){
            v50FractureMask.moveTo(-96,-93);v50FractureMask.lineTo(15,-108);
            v50FractureMask.lineTo(93,-65);v50FractureMask.lineTo(110,39);
            v50FractureMask.lineTo(68,95);v50FractureMask.lineTo(-41,100);
            v50FractureMask.lineTo(-107,44);v50FractureMask.lineTo(-110,-29);
            v50FractureMask.close();v50FractureMaskReady=true;
        }
        c.save();c.clipPath(v50FractureMask);
        int count=Math.min(11,1+(int)(damageRatio*11));
        int bright=colorBlend(ORE[id],0xffe2f9ff,.38f);
        for(int j=0;j<count;j++){
            int seed=seeded(j+87,id+71,depth/4+27);
            float x=-82+seed%163;
            float y=-72+(seed/197)%146;
            float growth=Math.max(0,Math.min(1,(damageRatio-j*.07f)*3.1f));
            if(growth<=0)continue;
            float dx=((seed/31)%2==0?1:-1)*(16+seed%25)*growth;
            float dy=(12+(seed/59)%27)*growth;
            float midX=x+dx*.48f,midY=y+dy*.53f;
            line(c,x+1,y+2,midX+1,midY+2,0xdd07131e,3.4f);
            line(c,midX+1,midY+2,x+dx+1,y+dy+2,0xdd07131e,3.4f);
            line(c,x,y,midX,midY,0xff111a29,2.1f);
            line(c,midX,midY,x+dx,y+dy,0xff111a29,2.1f);
            if(id>=4&&fxEnabled){
                int light=(bright&0x00ffffff)|(((int)(35+damageRatio*130))<<24);
                line(c,x-1,y-1,midX-1,midY-1,light,1.1f);
                line(c,midX-1,midY-1,x+dx-1,y+dy-1,light,1.1f);
                if(j%3==0)star(c,midX,midY,2.2f,bright,.35f+damageRatio*.45f);
            }
            if(growth>.65f){
                float branch=(7+(seed/29)%12)*growth;
                line(c,midX,midY,midX-dx*.18f+branch,midY+branch*.65f,
                    0xbb0a1522,1.7f);
            }
        }
        c.restore();
    }
"""
once("    private void drawRock(Canvas c,int id,int theme){",
     fracture+"\n    private void drawRock(Canvas c,int id,int theme){")
assert "drawV50LightShafts(c,biome,theme);" in s
assert "drawV50FractureNetwork(c,id,damageRatio);" in s
assert "drawV49CachedRockTexture(c,id,base);" in s
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
mine.write_text(s)
g=gradle.read_text()
assert "versionCode 26" in g and "versionName '4.9'" in g
gradle.write_text(g.replace("versionCode 26","versionCode 27").replace("versionName '4.9'","versionName '5.0'"))
print("v5.0: progressive fracture networks, per-biome animated shafts")
