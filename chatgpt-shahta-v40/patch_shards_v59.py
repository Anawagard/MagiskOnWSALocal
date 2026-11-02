from pathlib import Path

root=Path('chatgpt-shahta-v33/project')
mine=root/'app/src/main/java/com/bezdna/mine/MineView.java'
gradle=root/'app/build.gradle'
s=mine.read_text()

def once(old,new):
    global s
    count=s.count(old)
    assert count==1,('v5.9 hook mismatch',old[:100],count)
    s=s.replace(old,new,1)

# Transient effects only; do not touch saved state, input hitboxes or progression.
once('    private final ArrayList<Popup> popups=new ArrayList<>();', '''    private final ArrayList<Popup> popups=new ArrayList<>();
    private final ArrayList<V59Shard> v59Shards=new ArrayList<>();
    private final Path v59ShardPath=new Path();''')

once('    private static final class Popup {', '''    private static final class V59Shard {
        float x,y,vx,vy,angle,spin,life,max,size;
        int mineral;
        V59Shard(float xx,float yy,float dx,float dy,float rotation,
                 float angularVelocity,float duration,float radius,int ore){
            x=xx;y=yy;vx=dx;vy=dy;angle=rotation;spin=angularVelocity;
            life=max=duration;size=radius;mineral=ore;
        }
    }
    private static final class Popup {''')

once('''            spawnImpact(180+rng.nextInt(95)-47,318+rng.nextInt(85)-42,ore(),critical);
            if(popups.size()<14)''', '''            spawnImpact(180+rng.nextInt(95)-47,318+rng.nextInt(85)-42,ore(),critical);
            spawnV59Shards(180,330,ore(),critical,false);
            if(popups.size()<14)''')

once('''        spawnExplosion(180,329,found,true);
        popups.add''', '''        spawnExplosion(180,329,found,true);
        spawnV59Shards(180,329,found,true,true);
        popups.add''')

once('''        Iterator<Popup> fi=popups.iterator();''', '''        Iterator<V59Shard> v59it=v59Shards.iterator();
        while(v59it.hasNext()){
            V59Shard shard=v59it.next();
            shard.life-=(float)dt;
            shard.x+=shard.vx*(float)dt;
            shard.y+=shard.vy*(float)dt;
            shard.vy+=320f*(float)dt;
            shard.vx*=.986f;
            shard.angle+=shard.spin*(float)dt;
            if(shard.life<=0||shard.y>540)v59it.remove();
        }
        Iterator<Popup> fi=popups.iterator();''')

once('''        drawV50FractureNetwork(c,id,damageRatio);
        drawV53LivingOreGlints(c,id,damageRatio);''', '''        drawV50FractureNetwork(c,id,damageRatio);
        drawV59SurfaceChips(c,id,damageRatio);
        drawV53LivingOreGlints(c,id,damageRatio);''')

once('''        drawRock(c,ore(),bcol);
        c.restore();
        drawPickaxe(c);''', '''        drawRock(c,ore(),bcol);
        c.restore();
        drawV59Shards(c);
        drawPickaxe(c);''')

methods='''
    /** Short-lived material-aware debris, bounded to 64 fragments and
     *  reduced automatically on slower devices. Never serialized.
     */
    private void spawnV59Shards(float x,float y,int ore,boolean critical,boolean breaking){
        if(!fxEnabled)return;
        int count=breaking?23:critical?12:7;
        if(measuredFps<30f)count=Math.max(3,count/3);
        else if(measuredFps<45f)count=Math.max(4,count/2);
        if(v59Shards.size()+count>64){
            int remove=Math.min(v59Shards.size(),v59Shards.size()+count-64);
            v59Shards.subList(0,remove).clear();
        }
        int family=ore<=3?0:ore==9||ore==14||ore==17?2:ore>=20?3:1;
        for(int i=0;i<count;i++){
            float angle=(float)(rng.nextFloat()*Math.PI*2);
            float speed=breaking?90+rng.nextFloat()*185:55+rng.nextFloat()*145;
            float radius=(family==0?2.8f:3.8f)+rng.nextFloat()*(breaking?8f:5f);
            float duration=.30f+rng.nextFloat()*(breaking?.85f:.48f);
            v59Shards.add(new V59Shard(
                x+(rng.nextFloat()-.5f)*52,y+(rng.nextFloat()-.5f)*50,
                (float)Math.cos(angle)*speed,(float)Math.sin(angle)*speed-90,
                rng.nextFloat()*360,(rng.nextFloat()-.5f)*690,
                duration,radius,ore));
        }
    }
    /** Ore families break into rotating, shaded polygonal chips. */
    private void drawV59Shards(Canvas c){
        if(!fxEnabled||v59Shards.isEmpty())return;
        for(V59Shard shard:v59Shards){
            float fade=Math.max(0f,Math.min(1f,shard.life/shard.max));
            int alpha=Math.min(255,(int)(fade*235));
            int base=ORE[shard.mineral];
            int family=shard.mineral<=3?0:shard.mineral==9||shard.mineral==14||shard.mineral==17?2:shard.mineral>=20?3:1;
            float r=shard.size;
            c.save();c.translate(shard.x,shard.y);c.rotate(shard.angle);
            v59ShardPath.reset();
            v59ShardPath.moveTo(-r*.85f,-r*.6f);
            v59ShardPath.lineTo(r*.25f,-r*(family==0?.65f:1.25f));
            v59ShardPath.lineTo(r,r*.2f);
            if(family!=0)v59ShardPath.lineTo(r*.2f,r*1.2f);
            v59ShardPath.lineTo(-r*.75f,r*.75f);
            v59ShardPath.close();
            p.reset();p.setAntiAlias(true);
            p.setColor((alpha<<24)|(colorBlend(base,0xff233344,.23f)&0x00ffffff));
            c.drawPath(v59ShardPath,p);
            p.setColor((Math.min(255,alpha+12)<<24)|(colorBlend(base,WHITE,.50f)&0x00ffffff));
            c.drawLine(-r*.78f,-r*.55f,r*.20f,-r*(family==0?.62f:1.18f),p);
            if(family>=2&&r>=5f){
                p.setColor(((alpha/2)<<24)|0x00d6faff);
                c.drawLine(r*.20f,-r*.90f,r*.42f,r*.15f,p);
            }
            c.restore();
        }
    }
    /** Damage-dependent edge spalling stays inside each v5.8 ore outline.
     *  Facets are deterministic for each mineral and damage level.
     */
    private void drawV59SurfaceChips(Canvas c,int id,float damageRatio){
        if(damageRatio<.10f)return;
        int count=Math.min(13,1+(int)(damageRatio*14));
        if(measuredFps<30f)count=Math.min(7,count);
        c.save();c.clipPath(v58RockShape(id));
        for(int i=0;i<count;i++){
            double angle=(i*2.39996323+id*.41);
            float radius=83f+(float)Math.sin(i*3.7+id)*8f;
            float x=(float)Math.cos(angle)*radius;
            float y=(float)Math.sin(angle)*radius*.95f;
            float size=5f+(i%4)*2.4f+damageRatio*4f;
            v59ShardPath.reset();
            v59ShardPath.moveTo(x-size,y-size*.5f);
            v59ShardPath.lineTo(x+size*.8f,y-size*.7f);
            v59ShardPath.lineTo(x+size*.35f,y+size);
            v59ShardPath.close();
            p.reset();p.setAntiAlias(true);
            p.setColor(0xb20a1422);
            c.drawPath(v59ShardPath,p);
            p.setStrokeWidth(1.5f);p.setColor(colorBlend(ORE[id],WHITE,.38f));
            c.drawLine(x-size,y-size*.5f,x+size*.8f,y-size*.7f,p);
        }
        c.restore();
    }
'''
once('    private void drawParticles(Canvas c){',methods+'\n    private void drawParticles(Canvas c){')

assert s.count('private void drawV59Shards(')==1
assert s.count('private void drawV59SurfaceChips(')==1
assert s.count('spawnV59Shards(180,329,found,true,true);')==1
assert s.count('spawnV59Shards(180,330,ore(),critical,false);')==1
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert 'public void save()' in s and 'private void rebirth()' in s
mine.write_text(s)
g=gradle.read_text()
assert "versionCode 35" in g and "versionName '5.8'" in g
assert 'signingConfig signingConfigs.shahtaDebug' in g
gradle.write_text(g.replace('versionCode 35','versionCode 36').replace("versionName '5.8'","versionName '5.9'"))
print('v5.9: physics-based material fragments, damage-edge chips, adaptive render budget')
