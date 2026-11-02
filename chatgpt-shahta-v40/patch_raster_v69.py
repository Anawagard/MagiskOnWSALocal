"""v6.9 first material-art pass: raster cave textures, not extra particles.
No changes to touch targets, game state, backups, balance or signing.
"""
from pathlib import Path
root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
s=mine.read_text()
anchor="        drawV64BiomeHalo(c,biome,bcol);"
assert s.count(anchor)==1,s.count(anchor)
s=s.replace(anchor,anchor+"\n        drawV69RasterCave(c,biome);",1)
method=r"""
    // Decoded once per biome, recycled by the process on exit.
    // Bitmap textures are real raster pixels generated at build time,
    // independent of the Canvas geometry/particle renderers.
    private final android.graphics.Bitmap[] v69StoneTextures=
        new android.graphics.Bitmap[24];
    private final boolean[] v69StoneAttempted=new boolean[24];
    private final android.graphics.Rect v69Source=new android.graphics.Rect(0,0,384,384);
    private final android.graphics.RectF v69Destination=
        new android.graphics.RectF(43f,156f,317f,505f);
    private void drawV69RasterCave(Canvas c,int biome){
        final int index=Math.max(0,Math.min(23,biome));
        if(!v69StoneAttempted[index]){
            v69StoneAttempted[index]=true;
            try(java.io.InputStream input=getContext().getAssets().open(
                String.format(java.util.Locale.US,"shahta_textures/biome_%02d.png",index))){
                v69StoneTextures[index]=android.graphics.BitmapFactory.decodeStream(input);
            }catch(java.io.IOException ex){
                android.util.Log.w("ShahtaTexture","Biome texture missing: "+index,ex);
            }
        }
        final android.graphics.Bitmap bitmap=v69StoneTextures[index];
        if(bitmap==null||bitmap.isRecycled())return;
        c.save();
        c.clipRect(43f,156f,317f,505f);
        p.reset();p.setAntiAlias(true);p.setFilterBitmap(true);
        p.setAlpha(153);
        c.drawBitmap(bitmap,v69Source,v69Destination,p);
        p.setAlpha(255);
        c.restore();
    }
"""
anchor2="    private void drawMine(Canvas c){"
assert s.count(anchor2)==1
s=s.replace(anchor2,method+"\n"+anchor2,1)
assert "@Override public boolean onTouchEvent(MotionEvent e)" in s
assert 'for(int i=0;i<6;i++)ed.putInt("tech_"+i,tech[i]);' in s
assert "public void save()" in s and "private void rebirth()" in s
assert "private int zoneNo(){return (depth-1)/25;}" in s
g=gradle.read_text()
assert "versionCode 45" in g and "versionName '6.8'" in g
assert "signingConfig signingConfigs.shahtaDebug" in g
mine.write_text(s)
gradle.write_text(g.replace("versionCode 45","versionCode 46").replace("versionName '6.8'","versionName '6.9'"))
print("v6.9 raster textures attached; save/input and debug signing preserved")
