"""v7.2 modernist multi-page composition; source-only and release-safe.

Run AFTER patch_modernist_v71.py. No compilation, no workflow dispatch,
no gameplay/persistence/signing changes. Legacy forge/guild/atlas actions are
preserved, while drawing and input use the same affine transformation.
"""
from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
src=root/"app/src/main/java/com/bezdna/mine/MineView.java"
s=src.read_text()

def once(old,new):
    global s
    n=s.count(old)
    assert n==1,("v7.2 anchor mismatch",old[:120],n)
    s=s.replace(old,new,1)

def replace_method(signature,body):
    global s
    anchor="    "+signature+"{"
    assert s.count(anchor)==1,(signature,s.count(anchor))
    start=s.index(anchor)
    pos=s.index("{",start)
    level=0
    end=None
    for i in range(pos,len(s)):
        if s[i]=="{":level+=1
        elif s[i]=="}":
            level-=1
            if level==0:
                end=i+1
                break
    assert end is not None,signature
    s=s[:start]+body.strip("\n")+s[end:]

# Preserve rounded corners and fine strokes at ALL card aspect ratios.
# Bitmap panels were previously stretched 400x96 -> e.g. 165x145.
# Nine-slicing retains the original corner radius without vector stand-ins.
nine_slice=r"""
    private final android.graphics.Rect v72Source=new android.graphics.Rect();
    private final android.graphics.RectF v72Target=new android.graphics.RectF();
    // Reuse slice coordinates: no short-lived arrays on 60/120 Hz frames.
    private final int[] v72Xs=new int[4],v72Ys=new int[4];
    private final float[] v72Xd=new float[4],v72Yd=new float[4];
    private void v72Slice(Canvas c,android.graphics.Bitmap bitmap,
                          int sx0,int sy0,int sx1,int sy1,
                          float dx0,float dy0,float dx1,float dy1){
        if(sx1<=sx0||sy1<=sy0||dx1<=dx0||dy1<=dy0)return;
        v72Source.set(sx0,sy0,sx1,sy1);
        v72Target.set(dx0,dy0,dx1,dy1);
        c.drawBitmap(bitmap,v72Source,v72Target,p);
    }
    private void v72NineSlice(Canvas c,String asset,float x,float y,
                              float w,float h,int alpha){
        android.graphics.Bitmap bitmap=v70Asset(asset);
        if(bitmap==null||w<=0||h<=0)return;
        int bw=bitmap.getWidth(),bh=bitmap.getHeight();
        int sx=Math.min(18,bw/4),sy=Math.min(18,bh/4);
        float dx=Math.min(11f,w/3f),dy=Math.min(11f,h/3f);
        v72Xs[0]=0;v72Xs[1]=sx;v72Xs[2]=bw-sx;v72Xs[3]=bw;
        v72Ys[0]=0;v72Ys[1]=sy;v72Ys[2]=bh-sy;v72Ys[3]=bh;
        v72Xd[0]=x;v72Xd[1]=x+dx;v72Xd[2]=x+w-dx;v72Xd[3]=x+w;
        v72Yd[0]=y;v72Yd[1]=y+dy;v72Yd[2]=y+h-dy;v72Yd[3]=y+h;
        p.reset();p.setAntiAlias(true);p.setFilterBitmap(true);
        p.setAlpha(Math.max(0,Math.min(255,alpha)));
        for(int row=0;row<3;row++)
            for(int col=0;col<3;col++)
                v72Slice(c,bitmap,v72Xs[col],v72Ys[row],v72Xs[col+1],v72Ys[row+1],
                    v72Xd[col],v72Yd[row],v72Xd[col+1],v72Yd[row+1]);
        p.setAlpha(255);
    }

    // Modern header remains fixed while the original interactive content
    // is placed on a common, narrower grid on three feature pages.
    private void v72SectionHeader(Canvas c,String title,String subtitle,int tab){
        v72NineSlice(c,"panel.png",10,94,340,49,255);
        leftFittedText(c,title,26,114,17,0xffe9fbf8,260);
        leftFittedText(c,subtitle,26,132,10,0xff9acbc8,265);
        v70Draw(c,String.format(Locale.US,"ore_%02d.png",(tab*5)%24),
            304,100,37,37,255);
    }
"""
once("    private void panel(Canvas c,float x,float y,float w,float h,int col){",
     nine_slice+"\n    private void panel(Canvas c,float x,float y,float w,float h,int col){")

replace_method("private void panel(Canvas c,float x,float y,float w,float h,int col)",r"""
    private void panel(Canvas c,float x,float y,float w,float h,int col){
        v72NineSlice(c,"panel.png",x,y,w,h,245);
    }
""")
replace_method("private void button(Canvas c,float x,float y,float w,float h,String title,String sub,boolean enabled)",r"""
    private void button(Canvas c,float x,float y,float w,float h,String title,String sub,boolean enabled){
        v72NineSlice(c,enabled?"button.png":"button_off.png",x,y,w,h,255);
        boolean two=sub!=null&&!sub.isEmpty();
        float titleY=y+(two?h*.43f:h*.61f);
        fittedText(c,title,x+w*.5f,titleY,h<37?10:12,
            enabled?0xffeffffc:0xffa7b7c0,Math.max(12,w-12));
        if(two)fittedText(c,sub,x+w*.5f,y+h*.79f,h<37?9:10,
            enabled?0xffb5f1e6:0xff8498a3,Math.max(12,w-12));
    }
""")
replace_method("private void drawBottom(Canvas c)",r"""
    // Navigation rail occupies the same 5 x 72 logical touch cells.
    private void drawBottom(Canvas c){
        v70Draw(c,"nav.png",0,87,360,50,255);
        for(int i=0;i<5;i++){
            float x=3+i*72f;
            boolean active=page==i;
            v72NineSlice(c,active?"button.png":"button_off.png",
                x+2,90,64,44,active?250:188);
            // Keep icon and label inside the 64x44 painted hit target.
            // Larger text and brighter inactive labels improve narrow-phone
            // readability without changing the existing navigation cells.
            v70Draw(c,V70_ICONS[i],x+23,92,22,22,255);
            fittedText(c,V70_NAV[i],x+34,126,10,
                active?0xfff1fffc:0xffc7dce0,61);
            if(active)rect(c,x+14,132,40,2,0xff62e5d1);
        }
    }
""")

# Keep every existing forge, guild and atlas control and its purchase/action
# logic. Change their actual content geometry consistently on all three tabs.
# A clip hides the old header; the new fixed header never blocks a control.
for name in ("drawForge","drawGuild","drawCollection"):
    once("    private void "+name+"(Canvas c){",
         "    private void "+name+"Legacy(Canvas c){")

pages=[
    ("drawForge","КУЗНЯ / РЕЛИКВИИ","ПОСТОЯННЫЕ УСИЛЕНИЯ",2),
    ("drawGuild","ГИЛЬДИЯ / ПРОГРЕСС","ПЕРЕРОЖДЕНИЕ И МАСТЕРСТВО",3),
    ("drawCollection","АТЛАС / МИРЫ","ОТКРЫТИЯ И ГЛУБИНЫ",4),
]
wrappers=""
for name,title,subtitle,tab in pages:
    wrappers+=f"""
    private void {name}(Canvas c){{
        c.save();
        c.clipRect(0,145,360,653);
        c.translate(13f,18f);
        c.scale(.93f,.94f);
        {name}Legacy(c);
        c.restore();
        v72SectionHeader(c,"{title}","{subtitle}",{tab});
    }}
"""
once("    private void drawPage(Canvas c,int tab){",
     wrappers+"\n    private void drawPage(Canvas c,int tab){")

# Input inverse of exactly the same content transform.
# Top navigation is handled BEFORE this code in onTouchEvent and is unaffected.
once("        float y=(screenY-60f)/1.0f;",
     """        float y=screenY-60f;
        if(page>=2&&page<=4){
            // The legacy feature-page controls are drawn only inside the
            // clipped y=145..653 content viewport, shifted down by 60.
            // Do not activate invisible buttons behind the new section header.
            if(screenY<205f||screenY>713f)return true;
            // Rendered legacy content spans logical x=13..347.8.
            // Reject touches in the invisible side gutters before inverse mapping.
            if(x<13f||x>347.8f)return true;
            x=(x-13f)/.93f;
            y=(y-18f)/.94f;
        }""")

# Check that render and touch transforms cannot silently diverge.
for name in ("drawForge","drawGuild","drawCollection"):
    assert s.count("private void "+name+"(Canvas c)")==1,name
    assert s.count("private void "+name+"Legacy(Canvas c)")==1,name
assert s.count("c.translate(13f,18f);")==3
assert s.count("c.scale(.93f,.94f);")==3
assert s.count("if(screenY<205f||screenY>713f)return true;")==1
assert s.count("if(x<13f||x>347.8f)return true;")==1
assert s.count("x=(x-13f)/.93f;")==1
assert s.count("y=(y-18f)/.94f;")==1
assert s.count("private void v72NineSlice(")==1
assert s.count("private void v72SectionHeader(")==1
assert "if(screenY>=88&&screenY<=136)" in s
assert 'getSharedPreferences("mine_save_v1"' in s
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert 'shahta-save-v1' in (root/"app/src/main/java/com/bezdna/mine/MainActivity.java").read_text()
assert "public void save()" in s and "private void rebirth()" in s
assert "signingConfig signingConfigs.shahtaDebug" in (root/"app/build.gradle").read_text()
src.write_text(s)
print("v7.2: 9-slice raster cards, adaptive button labels, high-contrast top rail, "
      "forge/guild/atlas grid reflow with exact inverse touch mapping. "
      "Save/balance/signing unchanged. No APK built.")
