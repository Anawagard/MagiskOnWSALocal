from pathlib import Path
p=Path("chatgpt-shahta-v33/project/app/src/main/java/com/bezdna/mine/MineView.java")
s=p.read_text()
def put(old,new):
    global s
    assert old in s, "Missing hook: "+old[:80]
    s=s.replace(old,new,1)
put("private int chainLevel,geologyLevel,shopPage;",
    "private int chainLevel,geologyLevel,shopPage;\n    private boolean settingsOpen=false, soundEnabled=true, fxEnabled=true;\n    private int soundVolume=65;\n    private android.media.ToneGenerator tone;")
# persisted options initialization: prefs is initialized in constructor by this point
put('geologyLevel=Math.max(0,prefs.getInt("geology",0));',
    'geologyLevel=Math.max(0,prefs.getInt("geology",0));\n        soundEnabled=prefs.getBoolean("audio_enabled",true);\n        fxEnabled=prefs.getBoolean("effects_enabled",true);\n        soundVolume=Math.max(0,Math.min(100,prefs.getInt("audio_volume",65)));')
# Minimal synthesized SFX using built-in Android ToneGenerator (no permissions, no media files)
sound=r'''
    private void playSound(int kind){
        if(!soundEnabled||soundVolume==0)return;
        try{
            if(tone==null)tone=new android.media.ToneGenerator(android.media.AudioManager.STREAM_MUSIC,soundVolume);
            int code=kind==0?android.media.ToneGenerator.TONE_PROP_BEEP:
                kind==1?android.media.ToneGenerator.TONE_PROP_ACK:
                kind==2?android.media.ToneGenerator.TONE_PROP_PROMPT:
                kind==3?android.media.ToneGenerator.TONE_PROP_NACK:
                android.media.ToneGenerator.TONE_PROP_BEEP2;
            tone.startTone(code,kind==0?38:kind==1?170:kind==2?90:kind==3?220:125);
        }catch(RuntimeException ignored){}
    }
    private void storeAudioSettings(){
        prefs.edit().putBoolean("audio_enabled",soundEnabled)
            .putBoolean("effects_enabled",fxEnabled)
            .putInt("audio_volume",soundVolume).apply();
        if(tone!=null){tone.release();tone=null;}
    }
    private void drawAudioSettings(Canvas c){
        panel(c,16,150,328,480,0xff20324b);
        text(c,"ЗВУК И ЭФФЕКТЫ",180,195,20,GOLD,true);
        text(c,"Удобные настройки для игры",180,222,11,MUTED,true);
        button(c,37,245,286,60,"ЗВУК: "+(soundEnabled?"ВКЛ":"ВЫКЛ"),"Нажми для переключения",true);
        button(c,37,326,286,60,"ГРОМКОСТЬ: "+soundVolume+"%","Нажми для изменения",soundEnabled);
        button(c,37,407,286,60,"ВИЗУАЛЬНЫЕ ЭФФЕКТЫ: "+(fxEnabled?"ВКЛ":"ВЫКЛ"),"Частицы и анимации",true);
        button(c,37,520,286,61,"НАЗАД В МАГАЗИН","Все настройки сохраняются",true);
    }
'''
put("    private void drawShop(Canvas c){",sound+"\n    private void drawShop(Canvas c){")
put('text(c,"ЦЕНТР УЛУЧШЕНИЙ",180,112,19,GOLD,true);',
    'text(c,"ЦЕНТР УЛУЧШЕНИЙ",180,112,19,GOLD,true);\n        button(c,241,82,103,26,"⚙ ЗВУК","",true);\n        if(settingsOpen){drawAudioSettings(c);return;}')
# intercept settings taps before global nav, and provide shop access
put('checkBossTimeout(System.currentTimeMillis());\n        float x=',
    'checkBossTimeout(System.currentTimeMillis());\n        float x=')
put('if(y>=651){',
'''if(page==1&&settingsOpen){
            if(y>=245&&y<=307){soundEnabled=!soundEnabled;storeAudioSettings();if(soundEnabled)playSound(2);}
            else if(y>=326&&y<=388){soundVolume=(soundVolume+25)%125;storeAudioSettings();playSound(2);}
            else if(y>=407&&y<=469){fxEnabled=!fxEnabled;storeAudioSettings();playSound(2);}
            else if(y>=520&&y<=585){settingsOpen=false;playSound(2);}
            invalidate();return true;
        }
        if(page==1&&x>=235&&y>=80&&y<=112){settingsOpen=true;playSound(2);invalidate();return true;}
        if(y>=651){''')
# feedback hooks
put('damageRock(total,crit,false);','playSound(0);\n                damageRock(total,crit,false);')
put('private void destroyRock(){','private void destroyRock(){\n        playSound(1);')
put('upgradesBought++;\n                    message(', 'upgradesBought++;\n                    playSound(2);\n                    message(')
put('private void rebirth(){','private void rebirth(){\n        if(depth>=50)playSound(3);')
put('private void drawParticles(Canvas c){','private void drawParticles(Canvas c){\n        if(!fxEnabled)return;')
put('private void drawDeepAtmosphere(Canvas c,int biome,int tint){',
    'private void drawDeepAtmosphere(Canvas c,int biome,int tint){\n        if(!fxEnabled)return;')
p.write_text(s)
g=Path("chatgpt-shahta-v33/project/app/build.gradle")
v=g.read_text()
assert "versionCode 10" in v and "versionName '3.5'" in v
g.write_text(v.replace("versionCode 10","versionCode 11").replace("versionName '3.5'","versionName '3.6'"))
print("Audio SFX and persistent volume/effects settings added")
