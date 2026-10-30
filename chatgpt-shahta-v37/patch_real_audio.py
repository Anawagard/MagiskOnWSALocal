from pathlib import Path
import re
root=Path("chatgpt-shahta-v33/project")
p=root/"app/src/main/java/com/bezdna/mine/MineView.java"
s=p.read_text()
s=s.replace("private android.media.ToneGenerator tone;","private android.media.SoundPool soundPool;\n    private final int[] clips=new int[3];\n    private int sfxCounter=0;")
i=s.index("    private void playSound(int kind){")
j=s.index("    private void storeAudioSettings(){",i)
replacement="""    private void initRealAudio(){
        if(soundPool!=null)return;
        try{
            android.media.AudioAttributes attrs=new android.media.AudioAttributes.Builder()
                .setUsage(android.media.AudioAttributes.USAGE_GAME)
                .setContentType(android.media.AudioAttributes.CONTENT_TYPE_SONIFICATION).build();
            soundPool=new android.media.SoundPool.Builder().setMaxStreams(5).setAudioAttributes(attrs).build();
            clips[0]=soundPool.load(getContext(),com.bezdna.mine.R.raw.stone_hit,1);
            clips[1]=soundPool.load(getContext(),com.bezdna.mine.R.raw.stone_crack,1);
            clips[2]=soundPool.load(getContext(),com.bezdna.mine.R.raw.metal_hit,1);
        }catch(Exception ignored){}
    }
    private void playSound(int kind){
        if(!soundEnabled||soundVolume==0)return;
        initRealAudio();
        if(soundPool==null)return;
        sfxCounter++;
        int sample=kind==1||kind==3?clips[1]:(kind==2?clips[2]:clips[0]);
        if(sample>0){
            float v=(soundVolume/100f)*(kind==0?.55f:.85f);
            float pitch=kind==0?.91f+(sfxCounter%5)*.045f:kind==1?.82f:1f;
            soundPool.play(sample,v,v,1,0,pitch);
        }
    }
"""
s=s[:i]+replacement+s[j:]
s=s.replace("if(tone!=null){tone.release();tone=null;}","// SoundPool automatically uses the new saved volume on the next playback.")
p.write_text(s)
g=root/"app/build.gradle"
v=g.read_text()
assert "versionCode 11" in v and "versionName '3.6'" in v
g.write_text(v.replace("versionCode 11","versionCode 12").replace("versionName '3.6'","versionName '3.7'"))
print("Real recorded foley loaded through SoundPool")
