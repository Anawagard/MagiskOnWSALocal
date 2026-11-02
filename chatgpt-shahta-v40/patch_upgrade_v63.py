from pathlib import Path

root = Path('chatgpt-shahta-v33/project')
source = root / 'app/src/main/java/com/bezdna/mine/MineView.java'
gradle = root / 'app/build.gradle'
s = source.read_text()

def once(before, after):
    global s
    count = s.count(before)
    assert count == 1, ('v6.3 source anchor mismatch', before[:120], count)
    s = s.replace(before, after, 1)

# Decorative rank tracks stay inside existing cards, outside purchase buttons.
# maxRank=0 means the shop's uncapped, repeating ten-level milestone track.
method = '''
    /** Zero-allocation upgrade progress: all twelve segments use shared Paint. */
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
        for(int i=0;i<segments;i++){
            int color=i<filled?tint:0xff304455;
            rect(c,x+i*(segmentWidth+gap),y,segmentWidth,3f,color);
        }
        if(filled>0&&fxEnabled&&measuredFps>=45f){
            float gleam=(float)(.35f+.2f*Math.sin(time*2.1f));
            int alpha=Math.min(255,Math.max(0,(int)(gleam*255f)));
            rect(c,x+(filled-1)*(segmentWidth+gap),y,segmentWidth,1f,
                (alpha<<24)|0x00ffffff);
        }
    }
'''
once('    private void shopRow(Canvas c,int y,int k,String icon,String title,String detail,int level,int accent){',
     method+'\n    private void shopRow(Canvas c,int y,int k,String icon,String title,String detail,int level,int accent){')
once('        text(c,"Уровень "+level,80,y+57,10,accent,false);\n        button(c,237,y+12,100,49',
     '        text(c,"Уровень "+level,80,y+57,10,accent,false);\n        drawV63RankTrack(c,80,y+65,136,level,0,accent);\n        button(c,237,y+12,100,49')
once('            text(c,"Ранг "+mastery[k]+" / 60",76,y+61,10,colors[k],false);\n            button(c,238,y+12,97,49',
     '            text(c,"Ранг "+mastery[k]+" / 60",76,y+61,10,colors[k],false);\n            drawV63RankTrack(c,76,y+68,148,mastery[k],60,colors[k]);\n            button(c,238,y+12,97,49')
once('            text(c,"РАНГ "+gemPerk[k]+" / 60",79,y+58,10,colors[k],false);\n            button(c,238,y+12,98,47',
     '            text(c,"РАНГ "+gemPerk[k]+" / 60",79,y+58,10,colors[k],false);\n            drawV63RankTrack(c,79,y+65,146,gemPerk[k],60,colors[k]);\n            button(c,238,y+12,98,47')
once('        text(c,"РАНГ "+artifact[k]+" / 12",91,y+67,12,tint,false);\n        button(c,226,y+70,105,30',
     '        text(c,"РАНГ "+artifact[k]+" / 12",91,y+67,12,tint,false);\n        drawV63RankTrack(c,91,y+80,119,artifact[k],12,tint);\n        button(c,226,y+70,105,30')
once('        text(c,effect+"  •  Ранг "+talent[k]+"/20",28,y+48,11,tint,false);\n        button(c,230,y+13,101,48',
     '        text(c,effect+"  •  Ранг "+talent[k]+"/20",28,y+48,11,tint,false);\n        drawV63RankTrack(c,28,y+62,180,talent[k],20,tint);\n        button(c,230,y+13,101,48')

for invariant in ('@Override public boolean onTouchEvent(MotionEvent e)',
                  'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);',
                  'public void save()', 'private void rebirth()',
                  'drawV62OrePedestal(c,biome,bcol);',
                  'private void drawV63RankTrack('):
    assert invariant in s, invariant
assert s.count('drawV63RankTrack(c,') == 5

g = gradle.read_text()
assert "versionCode 39" in g and "versionName '6.2'" in g
assert 'signingConfig signingConfigs.shahtaDebug' in g
assert "applicationId 'com.bezdna.mine'" in g
source.write_text(s)
gradle.write_text(g.replace('versionCode 39','versionCode 40')
                    .replace("versionName '6.2'", "versionName '6.3'"))
print('v6.3: five upgrade progress track families, original buttons, state and signature preserved')
