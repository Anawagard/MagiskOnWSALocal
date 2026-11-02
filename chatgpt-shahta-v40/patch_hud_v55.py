from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()

def once(old,new):
    global s
    assert s.count(old)==1,("v5.5 source hook mismatch",old[:100],s.count(old))
    s=s.replace(old,new,1)

# Preserve the five original navigation hitboxes, labels, and screen routing.
# Replace font-dependent tiny emoji with crisp, hand-drawn vector icons.
once('        text(c,ico,x+32.5f,683+bounce,15,selected?0xffffe0a1:0xffa6becb,true);',
     '        drawV55NavIcon(c,x+32.5f,678+bounce,tab,selected);')

# The original title/ore labels retain their positions. The 25 cells are
# decorative, below the labels and above the mine viewport (no touch changes).
once('        drawV54BiomeCrest(c,biome,bcol);\n        fittedText(c,"УРОВЕНЬ "+depth+"   •   РУДА: "+ORE_NAMES[ore()],180,130,11,MUTED,312);',
     '        drawV54BiomeCrest(c,biome,bcol);\n        fittedText(c,"УРОВЕНЬ "+depth+"   •   РУДА: "+ORE_NAMES[ore()],180,130,11,MUTED,312);\n        drawV55BiomeProgress(c,biome);')

# Every crest receives its own constellation, not one of six repeated symbols.
start=s.index('        int sigil=biome%6;',s.index('private void drawV54BiomeCrest('))
end=s.index('        text(c,V54_BIOME_BADGES[biome]',start)
s=s[:start]+'''        int bright=colorBlend(tint,WHITE,.55f);
        drawV55BiomeSigil(c,biome,bright);
'''+s[end:]

# Atlas thumbnails now share the same visual language as the mine HUD.
once('        drawOreCrystal(c,cx+1,cy+5,9,tint,fxEnabled?(float)Math.sin(time*2):.5f);\n        c.restore();',
     '''        drawOreCrystal(c,cx+1,cy+5,9,tint,fxEnabled?(float)Math.sin(time*2):.5f);
        c.save();c.translate(cx+15,cy-14);c.scale(.72f,.72f);
        drawV55BiomeSigil(c,biome,colorBlend(tint,WHITE,.62f));
        c.restore();
        c.restore();''')

methods="""
    /** Font-independent navigation symbols; no changes to original touch targets. */
    private void drawV55NavIcon(Canvas c,float x,float y,int tab,boolean selected){
        int ink=selected?0xffffe0a1:0xff9bb9c6;
        int glow=selected?0xff9bf4dc:0xff638d9d;
        c.save();c.translate(x,y);
        if(tab==0){
            polygon(c,new float[]{-8,-5,3,-8,10,-4,9,-1,-1,-3,-7,0},ink);
            line(c,0,-4,5,8,ink,2.8f);
            line(c,5,8,7,10,glow,1.2f);
        }else if(tab==1){
            p.reset();p.setAntiAlias(true);p.setColor(ink);
            p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(2);
            c.drawCircle(0,0,5.5f,p);
            p.setStyle(Paint.Style.FILL);
            for(int j=0;j<8;j++){
                double a=j*Math.PI/4;
                float dx=(float)Math.cos(a),dy=(float)Math.sin(a);
                line(c,dx*7,dy*7,dx*9,dy*9,ink,2.1f);
            }
            p.setColor(glow);c.drawCircle(0,0,2.3f,p);
        }else if(tab==2){
            polygon(c,new float[]{0,-10,9,-2,5,8,-5,8,-9,-2},ink);
            polygon(c,new float[]{0,-7,5,-2,0,5,-5,-2},glow);
            line(c,-9,-2,9,-2,0xff213d4a,1);
        }else if(tab==3){
            polygon(c,new float[]{0,-10,3,-3,10,0,3,3,0,10,-3,3,-10,0,-3,-3},ink);
            p.reset();p.setAntiAlias(true);p.setColor(glow);c.drawCircle(0,0,2.2f,p);
        }else{
            polygon(c,new float[]{-10,-7,-1,-9,0,7,-9,9},ink);
            polygon(c,new float[]{1,-9,10,-7,9,9,0,7},glow);
            line(c,0,-8,0,8,0xff153447,1.3f);
            line(c,-7,-3,-3,-4,0xff153447,1);
            line(c,4,-4,7,-3,0xff153447,1);
        }
        c.restore();
    }

    /** 25 non-interactive cells, one for each level in the current biome. */
    private void drawV55BiomeProgress(Canvas c,int biome){
        int filled=1+(depth-1)%25;
        int accent=colorBlend(BIOME[biome],WHITE,.25f);
        rect(c,18,137,324,5,0xff091823);
        float cell=12.16f;
        for(int i=0;i<25;i++){
            int col=i<filled?accent:0xff253847;
            rect(c,20+i*cell,138,10.2f,3,col);
        }
        if(fxEnabled&&measuredFps>=30f){
            float pulse=(float)(.6+.4*Math.sin(time*3.0));
            rect(c,20+(filled-1)*cell,138,10.2f*pulse,1,0xfff5e1b3);
        }
    }

    /** Twenty-four deterministic micro-constellations for biome seals. */
    private void drawV55BiomeSigil(Canvas c,int biome,int tint){
        int spokes=3+biome%6;
        float rotation=(float)(biome*.51);
        for(int i=0;i<spokes;i++){
            float angle=(float)(rotation+i*2*Math.PI/spokes);
            float x=(float)Math.cos(angle)*4.4f;
            float y=-9+(float)Math.sin(angle)*3.2f;
            float x2=(float)Math.cos(angle)*6.6f;
            float y2=-9+(float)Math.sin(angle)*5.2f;
            line(c,x,y,x2,y2,tint,.9f);
        }
        p.reset();p.setAntiAlias(true);p.setColor(tint);
        c.drawCircle(0,-9,1.65f,p);
        int a=biome/6;
        for(int i=0;i<a;i++){
            float x=-5+i*3.5f;
            p.setColor((tint&0x00ffffff)|0x99000000);
            c.drawCircle(x,-4.7f,.65f,p);
        }
    }
"""
once('    private static final String[] V54_BIOME_BADGES={',methods+'\n    private static final String[] V54_BIOME_BADGES={')
assert s.count('private void drawV55NavIcon(')==1
assert s.count('private void drawV55BiomeProgress(')==1
assert s.count('private void drawV55BiomeSigil(')==1
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert 'private int zoneNo(){return (depth-1)/25;}' in s
mine.write_text(s)

g=gradle.read_text()
assert "versionCode 31" in g and "versionName '5.4'" in g
assert "signingConfig signingConfigs.shahtaDebug" in g
gradle.write_text(g.replace("versionCode 31","versionCode 32")
                   .replace("versionName '5.4'","versionName '5.5'"))
print("v5.5: 5 vector navigation icons, 25-stage biome track, 24 unique crest constellations")
