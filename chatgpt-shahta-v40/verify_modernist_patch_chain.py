"""Source-only integration rehearsal for the v7.2-v7.9 modernist patch chain.

Run from any directory: python3 chatgpt-shahta-v40/verify_modernist_patch_chain.py
Copies the Android project into a temporary directory; never runs Gradle,
Android tooling, network requests, or GitHub Actions. Does not modify checkout.
Accepts either a raw v6.9 project or an already-prepared v7.1 baseline.
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

# This integration verifier relies on assertions for release-critical contracts.
# Under python -O / PYTHONOPTIMIZE those checks disappear entirely; fail
# before touching even the disposable source tree rather than reporting PASS.
if not __debug__:
    raise SystemExit(
        "BLOCKED: source-only verification requires Python assertions; "
        "rerun without -O/-OO or PYTHONOPTIMIZE."
    )

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DEFAULT_PROJECT = REPO / "chatgpt-shahta-v33" / "project"
def locate_project():
    """Resolve the real Android baseline, never treating patch scripts as a project."""
    configured = os.environ.get("SHAHTA_BASELINE_PROJECT")
    if configured:
        selected = Path(configured).expanduser().resolve()
        required_override = (
            "app/build.gradle",
            "app/src/main/java/com/bezdna/mine/MineView.java",
            "app/src/main/java/com/bezdna/mine/MainActivity.java",
        )
        missing_override = [name for name in required_override if not (selected / name).is_file()]
        if missing_override:
            raise SystemExit(
                f"BLOCKED: SHAHTA_BASELINE_PROJECT={selected} is not a complete Android project; "
                f"missing: {missing_override}"
            )
        return selected
    # A leftover or empty project directory is not a usable baseline.
    # Validate the expected source files before preferring the default.
    required = (
        "app/build.gradle",
        "app/src/main/java/com/bezdna/mine/MineView.java",
        "app/src/main/java/com/bezdna/mine/MainActivity.java",
    )
    if all((DEFAULT_PROJECT / name).is_file() for name in required):
        return DEFAULT_PROJECT.resolve()
    candidates = []
    for parent in (REPO, REPO.parent):
        for gradle in parent.glob("*/project/app/build.gradle"):
            candidate = gradle.parent.parent  # build.gradle lives under project/app/
            if (candidate / "app/src/main/java/com/bezdna/mine/MineView.java").is_file() and (
                candidate / "app/src/main/java/com/bezdna/mine/MainActivity.java"
            ).is_file():
                candidates.append(candidate.resolve())
    candidates = sorted(set(candidates))
    if len(candidates) > 1:
        raise SystemExit(
            "BLOCKED: multiple Android baselines found; set SHAHTA_BASELINE_PROJECT: "
            + ", ".join(map(str, candidates))
        )
    return candidates[0] if candidates else DEFAULT_PROJECT

PROJECT = locate_project()
PREPARE = [HERE / "patch_full_redesign_v70.py", HERE / "patch_modernist_v71.py"]
PATCHES = [HERE / f"patch_modernist_v{v}.py" for v in range(72, 80)]
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
assert all(p.is_file() for p in PREPARE + PATCHES)
for patch in PREPARE + PATCHES:
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
    # Compare persistence and rebirth method bodies, not merely their names.
    # These are gameplay contracts; a visual-only patch must not rewrite them.
    def method_body(source, signature):
        import re
        matches = list(re.finditer(r"(?m)^\s*" + re.escape(signature) + r"\s*\{", source))
        assert len(matches) == 1, f"Expected one method: {signature}; found {len(matches)}"
        start = matches[0].start()
        opening = source.index("{", matches[0].start())
        depth = 0
        for i in range(opening, len(source)):
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
                if depth == 0:
                    return source[start:i + 1].strip()
        raise AssertionError(f"Unclosed method: {signature}")

    protected_methods = ("public void save()", "private void rebirth()")
    protected_before = {name: method_body(before, name) for name in protected_methods}
    prepared = "v70Asset(" in before and "v71Scale(" in before
    # Fail closed on ambiguous or inconsistent version metadata before any
    # source patch executes. In particular, a prepared v7.1 checkout must
    # retain the approved v7.0.1 version rather than silently accepting a
    # newer, incompatible project as the integration baseline.
    gradle_source = gradle.read_text(encoding="utf-8")
    import re
    codes = re.findall(r"(?m)^\s*versionCode\s+(\d+)\s*$", gradle_source)
    names = re.findall(r"""(?m)^\s*versionName\s+['"]([^'"]+)['"]\s*$""", gradle_source)
    assert len(codes) == len(names) == 1, (
        f"Ambiguous Gradle version metadata: codes={codes}, names={names}"
    )
    expected_version = ("48", "7.0.1") if prepared else ("46", "6.9")
    assert (codes[0], names[0]) == expected_version, (
        f"Unexpected baseline version: {(codes[0], names[0])}; "
        f"expected {expected_version}"
    )
    if not prepared:
        assert "v70Asset(" not in before and "v71Scale(" not in before, "Partially patched baseline"
    # A partially modernized checkout is not a valid baseline: applying patches
    # again can silently duplicate draw calls or shift touch geometry.
    modern_markers = [
        "v72NineSlice(", "v73", "v74", "v75", "v76",
        "v77", "v78", "int toastY = page==0 ? 178 : (page==1 ? 655 : 145);",
    ]
    found_modern = [marker for marker in modern_markers if marker in before]
    if found_modern:
        raise SystemExit(
            "BLOCKED: baseline already contains post-v7.1 modernist markers: "
            + ", ".join(found_modern)
            + ". Supply an untouched v6.9 or prepared v7.1 source tree."
        )
    chain = PATCHES if prepared else PREPARE + PATCHES
    original_cwd = Path.cwd()
    touch_after_interactions = None
    def touch_body(source):
        # v7.2 introduces inverse coordinates; v7.3/v7.4 deliberately refine
        # settings and shop hitboxes. Only v7.5-v7.9 must preserve them.
        match = re.search(r"public\s+boolean\s+onTouchEvent\s*\([^)]*\)", source)
        assert match is not None, "Missing Android touch handler"
        return method_body(source, match.group(0))
    try:
        os.chdir(root)
        for patch in chain:
            print(f"APPLY source-only {patch.name}", flush=True)
            runpy.run_path(str(patch), run_name="__main__")
            if patch.name == "patch_modernist_v74.py":
                touch_after_interactions = touch_body(java.read_text(encoding="utf-8"))
    finally:
        os.chdir(original_cwd)
    after = java.read_text(encoding="utf-8")
    assert touch_after_interactions is not None, "v7.4 interaction baseline not captured"
    assert touch_body(after) == touch_after_interactions, (
        "Post-v7.4 presentation patches unexpectedly changed the touch handler"
    )
    # Verify the real post-patch Java handler, not just matching patch-script
    # strings. These controls were historically clickable outside their art.
    final_touch = touch_body(after)
    interaction_contract = (
        "if(x>=218&&x<=323&&y>=251&&y<=301){soundEnabled=!soundEnabled;",
        "else if(x>=35&&x<=325&&y>=383&&y<=414){soundVolume=",
        "else if(x>=218&&x<=323&&y>=461&&y<=511){fxEnabled=!fxEnabled;",
        "if(page==1&&x>=246&&x<=345&&y>=102&&y<=154){settingsOpen=true;",
        "if(x>=16&&x<=124){shopPage=0;invalidate();return true;}",
        "if(x>=128&&x<=236){shopPage=1;invalidate();return true;}",
    )
    for control in interaction_contract:
        assert final_touch.count(control) == 1, (
            "Missing or duplicated final touch hitbox", control
        )
    assert "shopPage=1-shopPage" not in final_touch, (
        "Legacy shop tab toggle survived the modernist patch chain"
    )
    # The two shop tabs are separated and neither overlaps the settings
    # control. Touch and paint must refer to the same screen-space geometry.
    shop_tabs = ((16, 130, 124, 158), (128, 130, 236, 158))
    settings_button = (246, 102, 345, 154)
    assert shop_tabs[0][2] < shop_tabs[1][0] < settings_button[0]
    for left, top, right, bottom in shop_tabs:
        assert 0 <= left < right <= 360 and 0 <= top < bottom <= 720
        assert right < settings_button[0]
    updated_files = snapshot(target)
    java_rel = java.relative_to(target).as_posix()
    assert updated_files.keys() == baseline_files.keys(), "Patch chain added or removed project files"
    changed = {name for name in baseline_files if baseline_files[name] != updated_files[name]}
    expected_changed = {java_rel} if prepared else {java_rel, gradle.relative_to(target).as_posix()}
    assert changed == expected_changed, f"Unexpected changed files: {sorted(changed)}"
    assert after != before
    for name, original in protected_before.items():
        assert method_body(after, name) == original, f"Gameplay/persistence method changed: {name}"
    assert activity.read_bytes() == before_activity, "Activity/save wiring changed"
    if prepared:
        assert gradle.read_bytes() == before_gradle, "Signing/package configuration changed"
    else:
        expected_gradle = before_gradle.decode("utf-8").replace("versionCode 46", "versionCode 48").replace("versionName '6.9'", "versionName '7.0.1'")
        assert gradle.read_text() == expected_gradle, "Unexpected Gradle change"
    for marker in (
        'v72NineSlice(c,"panel.png",18,93,324,83,255);',
        'v72NineSlice(canvas,"panel.png",18,toastY,324,26,252);',
        'if(screenY<205f||screenY>713f)return true;',
        'getSharedPreferences("mine_save_v1"',
        'public void save()',
        'private void rebirth()',
        'int toastY = page==0 ? 178 : (page==1 ? 655 : 145);',
    ):
        assert marker in after, f"Missing post-chain invariant: {marker}"
    assert 'v72NineSlice(canvas,"panel.png",18,178,324,26,252);' not in after, "Stale v7.8 toast placement remains"
    assert 'v72NineSlice(canvas,"panel.png",18,240,324,26,252);' not in after, "Stale v7.7 toast placement remains"
    # Validate the final toast geometry, not only the existence of a marker.
    # Mine toast uses the telemetry gap; shop sits below its cards;
    # feature pages use the gap between navigation and transformed content.
    import re
    toast_match = re.search(
        r"int toastY\s*=\s*page\s*==\s*0\s*\?\s*(\d+)\s*:\s*"
        r"\(page\s*==\s*1\s*\?\s*(\d+)\s*:\s*(\d+)\);", after)
    assert toast_match is not None, "Missing five-page toast coordinates"
    mine_y, shop_y, feature_y = map(int, toast_match.groups())
    toast_height = 26
    assert (mine_y, shop_y, feature_y) == (178, 655, 145), "Unexpected toast placement"
    assert mine_y + toast_height <= 205, "Mine toast overlaps content"
    assert shop_y > 653 and shop_y + toast_height <= 682, "Shop toast overlaps cards or controls"
    assert feature_y > 137 and feature_y + toast_height < 205, "Feature toast overlaps navigation or content"
    assert after.count("int toastY = page==0 ? 178 : (page==1 ? 655 : 145);") == 1
    assert after.count('v72NineSlice(canvas,"panel.png",18,toastY,324,26,252);') == 1
    assert after.count('rect(canvas,26,toastY+4,3,18,0xff65e1d0);') == 1
    assert after.count('rect(canvas,36,toastY+22,296,1,0xff315d60);') == 1
    assert after.count('leftFittedText(canvas,toast,39,toastY+18,12,0xfff0fffb,251);') == 1
    assert after.count("c.translate(13f,18f);") == 3
    assert after.count("c.scale(.93f,.94f);") == 3
    print(f"PASS: {len(chain)} patches applied in order to disposable source tree; "
          "only expected source/version files changed; saves, package/signing retained; no build.")
