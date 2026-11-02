"""v6.8: richly illustrated biome title bands and progress tracks.

Pure visual polish: upgrades on five screens, 25-level biome strip and
24 color-matched mine headers. Does not touch input geometry, gameplay,
save format, backup, package ID or signing. No per-frame heap allocations.
"""
from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()

def once(old,new):
    global s
    count=s.count(old)
    assert count==1,("v6.8 hook mismatch",old[:100],count)
    s=s.replace(old,new,1)

def replace_method(start_anchor,end_anchor,new_method):
    global s
    start=s.index(start_anchor)
    end=s.index(end_anchor,start)
    assert start<end
    s=s[:start]+new_method+"\n"+s[end:]

# Existing text and tap positions stay unchanged. The band is behind the title.
once('        text(c,ZONES[biome],180,108,16,colorBlend(bcol,WHITE,.26f),true);',
     '        drawV68BiomeBanner(c,biome,bcol);\n'
     '        text(c,ZONES[biome],180,108,16,colorBlend(bcol,WHITE,.26f),true);')

banner=r"""
    /** Illustrated header for each of the 24 biome palettes.
     *  Six geological families, four epochs; all decoration behind existing text.
     */
    private void drawV68BiomeBanner(Canvas c,int biome,int tint){
        final int index=Math.max(0,Math.min(23,biome));
        final int family=index%6,epoch=index/6;
        final int metal=colorBlend(tint,0xff122a37,.74f);
        final int edge=colorBlend(tint,WHITE,.42f+epoch*.07f);
        final float glow=fxEnabled&&measuredFps>=42f?
            (float)(.66f+.34f*Math.sin(time*1.1f+index*.47f)):.74f;
        c.save();
        c.clipRect(66,90,294,118);
        p.reset();p.setAntiAlias(true);p.setStyle(Paint.Style.FILL);
        p.setColor(0xe5081823);
        c.drawRoundRect(67,91,293,117,9,9,p);
        p.setColor((0x99<<24)|(metal&0x00ffffff));
        c.drawRoundRect(70,93,290,115,7,7,p);
        p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(1.2f);
        p.setColor(((int)(90+55*glow)<<24)|(edge&0x00ffffff));
        c.drawRoundRect(68,92,292,116,8,8,p);
        p.setStrokeWidth(.75f);
        c.drawLine(96,96,264,96,p);
        c.drawLine(96,113,264,113,p);
        for(int side=0;side<2;side++){
            float x=side==0?82f:278f;
            p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(1.2f);
            switch(family){
            case 0: // fossil strata
                c.drawArc(x-7,98,x+7,112,185,170,false,p);break;
            case 1: // industrial clockwork
                c.drawCircle(x,105,6,p);
                c.drawLine(x-8,105,x+8,105,p);break;
            case 2: // prismatic ice
                c.drawLine(x,96,x+7,105,p);
                c.drawLine(x+7,105,x,114,p);
                c.drawLine(x,114,x-7,105,p);
                c.drawLine(x-7,105,x,96,p);break;
            case 3: // volcanic fractures
                c.drawLine(x-5,96,x+2,103,p);
                c.drawLine(x+2,103,x-2,108,p);
                c.drawLine(x-2,108,x+5,114,p);break;
            case 4: // organic roots
                c.drawArc(x-7,97,x+7,113,50,240,false,p);
                c.drawCircle(x+3,101,2,p);break;
            default: // runic monolith
                c.drawRect(x-6,98,x+6,112,p);
                c.drawLine(x-4,100,x+4,110,p);
                c.drawLine(x+4,100,x-4,110,p);break;
            }
            p.setStyle(Paint.Style.FILL);
            p.setColor((0xbb<<24)|(edge&0x00ffffff));
            for(int i=0;i<=epoch;i++){
                float px=x-5+i*3.5f;
                c.drawCircle(px,115,0.8f,p);
            }
        }
        c.restore();
        p.setStyle(Paint.Style.FILL);
    }
"""
once("    private void drawMine(Canvas c){",
     banner+"\n    private void drawMine(Canvas c){")

rank=r"""
    /** Five upgrade families share a beveled, twelve-segment jewel track.
     *  Preserve the exact x/y/width inputs used by the old 3px rank bars.
     */
    private void drawV63RankTrack(Canvas c,float x,float y,float width,
                                  int level,int maxRank,int tint){
        final int segments=12;
        final int rank=Math.max(0,level);
        final float fraction=maxRank>0?
            Math.min(1f,rank/(float)maxRank):
            ((rank%10)==0&&rank>0?1f:(rank%10)/10f);
        final int filled=Math.min(segments,Math.max(0,(int)Math.ceil(fraction*segments)));
        final float gap=2f;
        final float segmentWidth=(width-gap*(segments-1))/segments;
        rect(c,x-1,y-1,width+2,5,0xff152632);
        final int bright=colorBlend(tint,WHITE,.40f);
        final int dark=colorBlend(tint,0xff132d3c,.54f);
        for(int i=0;i<segments;i++){
            final float sx=x+i*(segmentWidth+gap);
            final boolean active=i<filled;
            rect(c,sx,y,segmentWidth,3f,active?dark:0xff304455);
            if(active)rect(c,sx,y,segmentWidth,1f,bright);
            if(i%3==2){
                rect(c,sx+segmentWidth-1f,y+1,1f,1f,
                    active?0xfff9e4b7:0xff526779);
            }
        }
        if(filled>0&&fxEnabled&&measuredFps>=42f){
            final float pulse=(float)(.52f+.48f*Math.sin(time*2.2f));
            final float sx=x+(filled-1)*(segmentWidth+gap);
            rect(c,sx,y,segmentWidth*pulse,1f,0xfff8efd5);
        }
    }
"""
replace_method("    private void drawV63RankTrack(",
               "    private void shopRow(",rank)

biome_progress=r"""
    /** Beveled 25-stage mine route, with a bright marker each fifth level. */
    private void drawV55BiomeProgress(Canvas c,int biome){
        final int filled=1+(depth-1)%25;
        final int accent=colorBlend(BIOME[biome],WHITE,.25f);
        final int shine=colorBlend(BIOME[biome],WHITE,.62f);
        rect(c,18,136,324,7,0xff0a1a25);
        final float cell=12.16f;
        for(int i=0;i<25;i++){
            final float x=20+i*cell;
            final boolean active=i<filled;
            rect(c,x,138,10.2f,3,active?accent:0xff263b49);
            if(active)rect(c,x,138,10.2f,1,shine);
            if(i%5==4)rect(c,x+8.2f,139,2f,2f,
                active?0xfff4e3bd:0xff546b7b);
        }
        if(fxEnabled&&measuredFps>=38f){
            final float pulse=(float)(.45f+.55f*Math.sin(time*2.6f));
            rect(c,20+(filled-1)*cell,138,10.2f*pulse,1,0xfffff0ce);
        }
    }
"""
replace_method("    private void drawV55BiomeProgress(",
               "    private void drawV55BiomeSigil(",biome_progress)

assert s.count("private void drawV68BiomeBanner(")==1
assert s.count("drawV68BiomeBanner(c,biome,bcol);")==1
assert s.count("private void drawV63RankTrack(")==1
assert s.count("private void drawV55BiomeProgress(")==1
assert "private int zoneNo(){return (depth-1)/25;}" in s
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert "public void save()" in s and "private void rebirth()" in s
assert "@Override public boolean onTouchEvent(MotionEvent e)" in s
assert "drawV67AtlasLandscape(c,cx,cy,biome);" in s
g=gradle.read_text()
assert "versionCode 44" in g and "versionName '6.7'" in g
assert "signingConfig signingConfigs.shahtaDebug" in g
assert "applicationId 'com.bezdna.mine'" in g
mine.write_text(s)
gradle.write_text(g.replace("versionCode 44","versionCode 45")
                   .replace("versionName '6.7'","versionName '6.8'"))
print("v6.8: 24 illustrated header bands, 25-step biome progress, five beveled upgrade tracks")
