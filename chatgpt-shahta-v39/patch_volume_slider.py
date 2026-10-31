from pathlib import Path

root=Path("chatgpt-shahta-v33/project")
mine=root/"app/src/main/java/com/bezdna/mine/MineView.java"
gradle=root/"app/build.gradle"
source=mine.read_text()

def replace_once(old,new):
    global source
    count=source.count(old)
    assert count==1, f"Expected exactly one source hook, found {count}: {old[:100]}"
    source=source.replace(old,new,1)

# The old cyclic formula could produce 115%, then silently clamp to 100%
# when loading preferences. Let players pick a stable 0-100% level in 5% steps.
replace_once(
    'soundVolume=(soundVolume+25)%125;storeAudioSettings();playSound(2);',
    'soundVolume=Math.max(0,Math.min(100,Math.round((x-55f)/250f*20f)*5));storeAudioSettings();playSound(2);'
)
replace_once(
    'else if(y>=326&&y<=388){soundVolume=',
    'else if(y>=326&&y<=402){soundVolume='
)
replace_once(
    'button(c,37,326,286,60,"ГРОМКОСТЬ: "+soundVolume+"%","Нажми для изменения",soundEnabled);',
    '''button(c,37,326,286,60,"ГРОМКОСТЬ: "+soundVolume+"%","Коснись полосы для выбора",soundEnabled);
        Paint volumeTrack=new Paint(3);
        volumeTrack.setColor(0xff44566f);
        c.drawRoundRect(55,393,305,400,3.5f,3.5f,volumeTrack);
        volumeTrack.setColor(soundEnabled?0xff81dccc:0xff8192a5);
        if(soundVolume>0)c.drawRoundRect(55,393,55+2.5f*soundVolume,400,3.5f,3.5f,volumeTrack);
        volumeTrack.setColor(0xfff7e7bb);
        float volumeThumb=55+2.5f*soundVolume;
        c.drawCircle(volumeThumb,396.5f,6.5f,volumeTrack);'''
)
assert '(soundVolume+25)%125' not in source
assert 'Math.round((x-55f)/250f*20f)*5' in source
assert 'c.drawCircle(volumeThumb,396.5f,6.5f,volumeTrack)' in source
mine.write_text(source)

grad=gradle.read_text()
assert grad.count("versionCode 13")==1 and grad.count("versionName '3.8'")==1
gradle.write_text(grad.replace("versionCode 13","versionCode 14")
                         .replace("versionName '3.8'","versionName '3.9'"))
print("v3.9: direct 0-100% volume selection in 5% steps, visible volume bar, fixed 115% bug")
