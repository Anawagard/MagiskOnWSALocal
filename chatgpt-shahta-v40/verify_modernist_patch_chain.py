"""Source-only integration rehearsal for the v7.2-v7.7 modernist patch chain.

Run from any directory: python3 chatgpt-shahta-v40/verify_modernist_patch_chain.py
Copies the Android project into a temporary directory; never runs Gradle,
Android tooling, network requests, or GitHub Actions. Does not modify checkout.
Requires the v7.1 baseline (v70Asset and modernist raster assets).
If it is not checked into this branch, set SHAHTA_BASELINE_PROJECT to an
existing local project directory. Missing input fails before any patch runs.
"""
from pathlib import Path
import ast
import contextlib
import hashlib
import os
import runpy
import shutil
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DEFAULT_PROJECT = REPO / "chatgpt-shahta-v33" / "project"
PROJECT = Path(os.environ["SHAHTA_BASELINE_PROJECT"]).expanduser().resolve() if os.environ.get("SHAHTA_BASELINE_PROJECT") else DEFAULT_PROJECT
PATCHES = [HERE / f"patch_modernist_v{v}.py" for v in range(72, 78)]
if not PROJECT.is_dir():
    raise SystemExit(
        f"BLOCKED: v7.1 Android baseline not found at {PROJECT}. "
        "Provide the actual project directory with SHAHTA_BASELINE_PROJECT; "
        "no patches or builds were run."
    )
required = (
    "app/src/main/java/com/bezdna/mine/MineView.java",
    "app/src/main/java/com/bezdna/mine/MainActivity.java",
    "app/build.gradle",
)
missing = [name for name in required if not (PROJECT / name).is_file()]
if missing:
    raise SystemExit(f"BLOCKED: baseline at {PROJECT} lacks: {missing}; no patches or builds were run.")
assert all(p.is_file() for p in PATCHES)
for patch in PATCHES:
    ast.parse(patch.read_text(encoding="utf-8"), filename=str(patch))

with tempfile.TemporaryDirectory(prefix="shahta-source-rehearsal-") as tmp:
    root = Path(tmp)
    target = root / "chatgpt-shahta-v33" / "project"
    target.parent.mkdir(parents=True)
    shutil.copytree(PROJECT, target)
    java = target / "app/src/main/java/com/bezdna/mine/MineView.java"
    activity = target / "app/src/main/java/com/bezdna/mine/MainActivity.java"
    gradle = target / "app/build.gradle"
    def snapshot(tree):
        return {
            p.relative_to(tree).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in tree.rglob("*") if p.is_file()
        }

    baseline_files = snapshot(target)
    before_activity = activity.read_bytes()
    before_gradle = gradle.read_bytes()
    before = java.read_text(encoding="utf-8")
    assert "v70Asset(" in before, "Baseline lacks v7.1 raster support"
    original_cwd = Path.cwd()
    try:
        os.chdir(root)
        for patch in PATCHES:
            print(f"APPLY source-only {patch.name}", flush=True)
            runpy.run_path(str(patch), run_name="__main__")
    finally:
        os.chdir(original_cwd)
    after = java.read_text(encoding="utf-8")
    updated_files = snapshot(target)
    java_rel = java.relative_to(target).as_posix()
    assert updated_files.keys() == baseline_files.keys(), "Patch chain added or removed project files"
    changed = {name for name in baseline_files if baseline_files[name] != updated_files[name]}
    assert changed == {java_rel}, f"Unexpected changed files: {sorted(changed)}"
    assert after != before
    assert activity.read_bytes() == before_activity, "Activity/save wiring changed"
    assert gradle.read_bytes() == before_gradle, "Signing/package configuration changed"
    for marker in (
        'v72NineSlice(c,"panel.png",18,93,324,83,255);',
        'v72NineSlice(canvas,"panel.png",18,240,324,26,252);',
        'if(screenY<205f||screenY>713f)return true;',
        'getSharedPreferences("mine_save_v1"',
        'public void save()',
        'private void rebirth()',
    ):
        assert marker in after, f"Missing post-chain invariant: {marker}"
    assert after.count("c.translate(13f,18f);") == 3
    assert after.count("c.scale(.93f,.94f);") == 3
    print("PASS: six patches applied in order to disposable source tree; "
          "only MineView.java changed; navigation, saves, package/signing config retained; no build.")
