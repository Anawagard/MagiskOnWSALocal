"""v7.8: move mining toast above the ore hitbox (source-only).

Fails closed under Python -O and writes atomically, preserving the source when
preconditions are missing. Apply after patch_modernist_v77.py.
"""
from pathlib import Path
import os
import tempfile

source = Path('chatgpt-shahta-v33/project/app/src/main/java/com/bezdna/mine/MineView.java')
old = '''            v72NineSlice(canvas,"panel.png",18,240,324,26,252);
            rect(canvas,26,245,3,16,0xff65e1d0);
            leftFittedText(canvas,toast,39,258,12,0xfff0fffb,285);'''
new = '''            v72NineSlice(canvas,"panel.png",18,178,324,26,252);
            rect(canvas,26,183,3,16,0xff65e1d0);
            leftFittedText(canvas,toast,39,196,12,0xfff0fffb,285);'''

def apply():
    s = source.read_text(encoding='utf-8')
    if s.count(old) != 1:
        raise RuntimeError('v7.8: expected exactly one old toast anchor; source unchanged')
    required = (
        'else if(x>=105&&x<=330&&y>=210&&y<=440)',
        'if(screenY>=88&&screenY<=136)',
        'getSharedPreferences("mine_save_v1"',
    )
    missing = [marker for marker in required if marker not in s]
    if missing:
        raise RuntimeError(f'v7.8: missing gameplay contracts {missing}; source unchanged')
    result = s.replace(old, new, 1)
    fd, tmp = tempfile.mkstemp(prefix='.mineview-v78-', suffix='.tmp', dir=source.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as handle:
            handle.write(result)
        os.chmod(tmp, source.stat().st_mode)
        os.replace(tmp, source)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    print('v7.8: toast moved above ore; source-only')

if __name__ == '__main__':
    apply()
