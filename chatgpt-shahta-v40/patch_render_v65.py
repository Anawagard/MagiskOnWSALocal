"""v6.5: eliminate hot-path polygon array allocations; improve ore integrity HUD."""
from pathlib import Path
import re

root=Path('chatgpt-shahta-v33/project')
mine=root/'app/src/main/java/com/bezdna/mine/MineView.java'
gradle=root/'app/build.gradle'
s=mine.read_text()

def once(before,after):
    global s
    n=s.count(before)
    assert n==1,('v6.5 source anchor mismatch',before[:100],n)
    s=s.replace(before,after,1)

input_start=s.index('    @Override public boolean onTouchEvent(MotionEvent e)')
input_and_save_before=s[input_start:]
pattern=re.compile(r'polygon\(c,\s*new float\[\]\s*\{(.*?)\}\s*,',re.S)
counts={}

def split_arguments(raw):
    parts=[];last=0;depth=0
    for i,ch in enumerate(raw):
        if ch=='(':depth+=1
        elif ch==')':depth-=1
        elif ch==',' and depth==0:
            parts.append(raw[last:i].strip());last=i+1
    parts.append(raw[last:].strip())
    assert depth==0 and all(parts),('invalid polygon coordinates',raw)
    return parts

def replace_polygon(match):
    coords=split_arguments(match.group(1))
    assert len(coords)%2==0 and 6<=len(coords)<=32,len(coords)
    counts[len(coords)//2]=counts.get(len(coords)//2,0)+1
    return 'polyV65(c,'+match.group(1)+','

s,n=pattern.subn(replace_polygon,s)
assert n>=100,('unexpected polygon allocation count',n)
assert sum(counts.values())==n
assert 'polygon(c,new float[]{' not in s

overloads=[]
for vertices in sorted(counts):
    parameters=','.join(f'float x{i},float y{i}' for i in range(vertices))
    body=['    private void polyV65(Canvas c,'+parameters+',int color){',
          '        reusablePolygon.reset();',
          '        reusablePolygon.moveTo(x0,y0);']
    for i in range(1,vertices):
        body.append(f'        reusablePolygon.lineTo(x{i},y{i});')
    body.extend(['        reusablePolygon.close();',
                 '        p.reset();p.setAntiAlias(false);p.setColor(color);',
                 '        c.drawPath(reusablePolygon,p);',
                 '    }'])
    overloads.append('\n'.join(body))
anchor='    private void polygon(Canvas c,float[] coords,int color){'
once(anchor,'\n    /** Primitive polygon overloads: no temporary float[] allocations. */\n'+
     '\n'.join(overloads)+'\n\n'+anchor)

health='''
    /** Decorative ore-health HUD; unchanged geometry and hit testing. */
    private void drawV65OreIntegrity(Canvas c,float ratio,int biome,boolean boss){
        final float fraction=Math.max(0f,Math.min(1f,ratio));
        final int accent=boss?0xfff7826b:colorBlend(BIOME[biome],0xff64dfa9,.60f);
        bar(c,18,550,324,14,fraction,accent);
        p.reset();p.setAntiAlias(false);p.setStrokeWidth(1f);
        p.setColor(0x88415867);
        for(int i=1;i<16;i++){
            float x=18f+i*324f/16f;
            c.drawLine(x,553,x,561,p);
        }
        if(fraction>.01f&&fraction<.99f){
            float x=20f+fraction*320f;
            p.setColor(0xfff4e8c8);
            c.drawLine(x,549,x,565,p);
        }
        if(fraction<.25f){
            final int alpha=fxEnabled&&measuredFps>=38f?
                (int)(110f+50f*Math.sin(time*5f)):110;
            p.setColor((alpha<<24)|0x00f7826b);
            p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(1.5f);
            c.drawRoundRect(18,550,342,564,7,7,p);
        }
        p.setStyle(Paint.Style.FILL);
    }
'''
once('    private void bar(Canvas c,float x,float y,float w,float h,float ratio,int active){',
     health+'\n    private void bar(Canvas c,float x,float y,float w,float h,float ratio,int active){')
once('        bar(c,18,550,324,14,displayedHpRatio,guardian()?0xfff7826b:0xff64dfa9);',
     '        drawV65OreIntegrity(c,displayedHpRatio,biome,guardian());')

assert s[s.index('    @Override public boolean onTouchEvent(MotionEvent e)'):]==input_and_save_before
assert s.count('drawV65OreIntegrity(c,displayedHpRatio,biome,guardian());')==1
assert s.count('private void drawV65OreIntegrity(')==1
assert s.count('private void polyV65(')==len(counts)
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert 'drawV64BiomeHalo(c,biome,bcol);' in s
assert 'public void save()' in s and 'private void rebirth()' in s
assert 'private int zoneNo(){return (depth-1)/25;}' in s

g=gradle.read_text()
assert "versionCode 41" in g and "versionName '6.4'" in g
assert 'signingConfig signingConfigs.shahtaDebug' in g
assert "applicationId 'com.bezdna.mine'" in g
mine.write_text(s)
gradle.write_text(g.replace('versionCode 41','versionCode 42')
                   .replace("versionName '6.4'","versionName '6.5'"))
print('v6.5: removed',n,'polygon float-array allocations across',
      sorted(counts),'vertex arities; segmented ore integrity HUD; input/save/signing unchanged')
