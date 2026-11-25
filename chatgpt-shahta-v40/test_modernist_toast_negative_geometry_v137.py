"""Fail-closed source-only tests for all five page notification safe zones.

Runs without Android SDK, Gradle, APK, or GitHub Actions.
"""
import importlib.util
from pathlib import Path

path = Path(__file__).resolve().parent / "patch_modernist_v79.py"
spec = importlib.util.spec_from_file_location("shahta_toast_v79", path)
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)

patch.validate_toast_geometry()
original_new = patch.new
original_nav = patch.nav_new
original_y = dict(patch.TOAST_Y)

def must_reject(label, change):
    try:
        change()
        try:
            patch.validate_toast_geometry()
        except RuntimeError:
            return
        raise AssertionError("Unsafe notification mutation accepted: " + label)
    finally:
        patch.new = original_new
        patch.nav_new = original_nav
        patch.TOAST_Y.clear()
        patch.TOAST_Y.update(original_y)

for page, bad_y in ((0, 265), (1, 700), (2, 204), (3, 136), (4, 714)):
    must_reject("page %d out-of-bounds toast" % page,
                lambda page=page, bad_y=bad_y: patch.TOAST_Y.__setitem__(page, bad_y))

for old, new in (
    ("page==0 ? 240", "page==0 ? 265"),
    ("page==1 ? 691", "page==1 ? 700"),
    (": 177);", ": 204);"),
    ("rect(canvas,26,toastY+4,3,18,toastAccent);",
     "rect(canvas,26,toastY+4,3,18,0xff65e1d0);"),
):
    assert old in original_new, old
    must_reject("Java render source drift " + old,
                lambda old=old, new=new: setattr(patch, "new", original_new.replace(old, new, 1)))

must_reject("duplicated nav rail", lambda: setattr(
    patch, "nav_new",
    original_nav.replace("rect(c,left+9,94,2,12,tabAccent);",
                         "rect(c,left+9,94,2,12,tabAccent);\n"
                         "                rect(c,left+9,94,2,12,tabAccent);", 1)))
patch.validate_toast_geometry()
print("PASS: 10 negative toast/rail mutations rejected; five page layouts fail closed")
