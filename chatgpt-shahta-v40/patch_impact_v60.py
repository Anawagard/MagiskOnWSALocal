from pathlib import Path
root=Path('chatgpt-shahta-v33/project')
mine=root/'app/src/main/java/com/bezdna/mine/MineView.java'
gradle=root/'app/build.gradle'
s=mine.read_text()

def once(old,new):
    global s
    count=s.count(old)
    assert count==1,('v6.0 hook mismatch',old[:120],count)
    s=s.replace(old,new,1)

# Frame-local only; no new SharedPreferences keys or changes to hitboxes.
once('    private final Path v59ShardPath=new Path();', '''    private final Path v59ShardPath=new Path();
    private final Path v60ParticlePath=new Path();
    private final Path v60ImpactPath=new Path();
    private int v60ImpactOre=0;
    private boolean v60CriticalImpact=false;
    private float v60HitX=180f,v60HitY=330f;''')

once('''            spawnImpact(180+rng.nextInt(95)-47,318+rng.nextInt(85)-42,ore(),critical);
            spawnV59Shards(180,330,ore(),critical,false);''', '''            v60ImpactOre=ore();v60CriticalImpact=critical;
            v60HitX=180+rng.nextInt(95)-47;v60HitY=318+rng.nextInt(85)-42;
            spawnImpact(v60HitX,v60HitY,ore(),critical);
            spawnV59Shards(180,330,ore(),critical,false);''')

once('''        drawRock(c,ore(),bcol);
        c.restore();
        drawV59Shards(c);''', '''        drawRock(c,ore(),bcol);
        c.restore();
        drawV60ImpactResonance(c);
        drawV59Shards(c);''')

methods='''
    /** Mineral-family-specific transient shockwave. Does not alter damage. */
    private void drawV60ImpactResonance(Canvas c){
        if(!fxEnabled||impact<=.01f||page!=0)return;
        float progress=1f-impact;
        float strength=Math.min(1f,impact*1.15f);
        int oreId=Math.max(0,Math.min(ORE.length-1,v60ImpactOre));
        int family=oreId<=3?0:(oreId==9||oreId==14||oreId==17)?2:oreId>=20?3:1;
        int hue=ORE[oreId];
        float radius=18f+progress*(v60CriticalImpact?107f:76f);
        int alpha=Math.max(0,Math.min(255,(int)(strength*(v60CriticalImpact?205:152))));
        c.save();c.clipRect(18,149,342,509);
        c.translate(v60HitX,v60HitY);
        p.reset();p.setAntiAlias(true);p.setStyle(Paint.Style.STROKE);
        p.setStrokeWidth(v60CriticalImpact?3.2f:2f);
        p.setColor((alpha<<24)|(hue&0x00ffffff));
        c.drawCircle(0,0,radius,p);
        p.setStrokeWidth(1.1f);
        p.setColor(((alpha/2)<<24)|0x00ffffff);
        c.drawCircle(0,0,radius+5f,p);
        int rays=measuredFps<35f?6:v60CriticalImpact?16:10;
        for(int i=0;i<rays;i++){
            float a=(float)(i*6.2831853/rays+oreId*.17f);
            float cs=(float)Math.cos(a),sn=(float)Math.sin(a);
            float r1=radius*(family==2?.54f:.77f);
            float r2=radius+(family==1?20f:family==3?13f:8f)*strength;
            p.setColor((Math.min(255,(int)(alpha*(i%3==0?1f:.58f)))<<24)|
                ((i%4==0?WHITE:hue)&0x00ffffff));
            p.setStrokeWidth(family==1?2.5f:family==0?1.8f:1.3f);
            if(family==1){
                v60ImpactPath.reset();
                v60ImpactPath.moveTo(cs*r1,sn*r1);
                v60ImpactPath.quadTo(cs*(r2+5)-sn*8,sn*(r2+5)+cs*8,cs*r2,sn*r2);
                c.drawPath(v60ImpactPath,p);
            }else if(family==2){
                v60ImpactPath.reset();
                v60ImpactPath.moveTo(cs*r1,sn*r1);
                v60ImpactPath.lineTo(cs*(r1+r2)*.5f-sn*5,sn*(r1+r2)*.5f+cs*5);
                v60ImpactPath.lineTo(cs*r2,sn*r2);
                c.drawPath(v60ImpactPath,p);
            }else{
                c.drawLine(cs*r1,sn*r1,cs*r2,sn*r2,p);
            }
            if(family==3&&i%3==0){
                p.setStyle(Paint.Style.FILL);
                p.setColor(((alpha/2)<<24)|0x00ffffff);
                c.drawCircle(cs*r2,sn*r2,2.3f+2f*strength,p);
                p.setStyle(Paint.Style.STROKE);
            }
        }
        if(v60CriticalImpact){
            p.setStyle(Paint.Style.FILL);
            p.setColor(((alpha/3)<<24)|0x00fff0c4);
            c.drawCircle(0,0,12f+progress*22f,p);
        }
        c.restore();
    }
'''
once('    private void drawParticles(Canvas c){',methods+'\n    private void drawParticles(Canvas c){')

# Eliminate one temporary float[] per particle per frame.
once('''            polygon(c,new float[]{a.x,a.y-a.size*.9f,a.x+a.size*.7f,a.y,
                a.x,a.y+a.size*.9f,a.x-a.size*.7f,a.y},color);''', '''            v60ParticlePath.reset();
            v60ParticlePath.moveTo(a.x,a.y-a.size*.9f);
            v60ParticlePath.lineTo(a.x+a.size*.7f,a.y);
            v60ParticlePath.lineTo(a.x,a.y+a.size*.9f);
            v60ParticlePath.lineTo(a.x-a.size*.7f,a.y);
            v60ParticlePath.close();
            p.reset();p.setAntiAlias(true);p.setColor(color);
            c.drawPath(v60ParticlePath,p);''')

# Pickaxe metal glints are purely decorative, in existing swing coordinates.
once('''        line(c,18,-28,43,-31,0x99ffffff,2);
        if(tier>=3){''', '''        line(c,18,-28,43,-31,0x99ffffff,2);
        if(fxEnabled&&swing>.12f){
            float flare=(float)Math.sin(Math.min(1f,(1f-swing)*1.8f)*Math.PI);
            float reach=11f+Math.max(0f,flare)*24f;
            p.reset();p.setAntiAlias(true);p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(2f+flare*2.5f);
            p.setColor(((int)(Math.max(0f,flare)*170)<<24)|(light&0x00ffffff));
            c.drawLine(-67,-25,-67-reach,-25-reach*.35f,p);
            c.drawLine(66,-24,66+reach,-24-reach*.30f,p);
        }
        if(tier>=3){''')

for hook in ('drawV60ImpactResonance(c);','private void drawV60ImpactResonance(',
             'v60ParticlePath.reset();','v60CriticalImpact=critical;',
             'drawV59SurfaceChips(c,id,damageRatio);'):
    assert s.count(hook)==1,(hook,s.count(hook))
for invariant in ('for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);',
                  'public void save()','private void rebirth()',
                  '@Override public boolean onTouchEvent(MotionEvent e)'):
    assert invariant in s,invariant
mine.write_text(s)
g=gradle.read_text()
assert "versionCode 36" in g and "versionName '5.9'" in g
assert 'signingConfig signingConfigs.shahtaDebug' in g
assert "applicationId 'com.bezdna.mine'" in g
gradle.write_text(g.replace('versionCode 36','versionCode 37').replace("versionName '5.9'","versionName '6.0'"))
print('v6.0: ore-specific impact waves, pickaxe glints, reusable particle path; save schema unchanged')
