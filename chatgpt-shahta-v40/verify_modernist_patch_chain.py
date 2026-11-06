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

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DEFAULT_PROJECT = REPO / "chatgpt-shahta-v33" / "project"
def locate_project():
    """Resolve the real Android baseline, never treating patch scripts as a project."""
    configured = os.environ.get("SHAHTA_BASELINE_PROJECT")
    if configured:
        return Path(configured).expanduser().resolve()
    if DEFAULT_PROJECT.is_dir():
        return DEFAULT_PROJECT
    candidates = []
    for parent in (REPO, REPO.parent):
        for gradle in parent.glob("*/project/app/build.gradle"):
            candidate = gradle.parent.parent.parent
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
        "v77", "v78", "int toastY = page==0 ? 178 : 623;",
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
    try:
        os.chdir(root)
        for patch in chain:
            print(f"APPLY source-only {patch.name}", flush=True)
            runpy.run_path(str(patch), run_name="__main__")
    finally:
        os.chdir(original_cwd)
    after = java.read_text(encoding="utf-8")
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
        'int toastY = page==0 ? 178 : 623;',
    ):
        assert marker in after, f"Missing post-chain invariant: {marker}"
    assert 'v72NineSlice(canvas,"panel.png",18,178,324,26,252);' not in after, "Stale v7.8 toast placement remains"
    assert 'v72NineSlice(canvas,"panel.png",18,240,324,26,252);' not in after, "Stale v7.7 toast placement remains"
    # Validate the final toast geometry, not only the existence of a marker.
    # Mine toast is above the content area; feature-page toast is below the
    # last shop card and above the lower interaction boundary (y=653).
    import re
    toast_match = re.search(r"int toastY\s*=\s*page\s*==\s*0\s*\?\s*(\d+)\s*:\s*(\d+)\s*;", after)
    assert toast_match is not None, "Missing page-aware toast coordinates"
    mine_y, feature_y = map(int, toast_match.groups())
    toast_height = 26
    assert mine_y == 178 and feature_y == 623, "Unexpected toast placement"
    assert mine_y + toast_height <= 205, "Mine toast overlaps content"
    assert feature_y >= 615 and feature_y + toast_height <= 653, "Feature toast overlaps cards or controls"
    assert after.count("int toastY = page==0 ? 178 : 623;") == 1, "Duplicate toast placement"
    assert after.count('v72NineSlice(canvas,"panel.png",18,toastY,324,26,252);') == 1
    assert after.count('rect(canvas,26,toastY+5,3,16,0xff65e1d0);') == 1
    assert after.count('leftFittedText(canvas,toast,39,toastY+18,12,0xfff0fffb,285);') == 1
    assert after.count("c.translate(13f,18f);") == 3
    assert after.count("c.scale(.93f,.94f);") == 3
    print(f"PASS: {len(chain)} patches applied in order to disposable source tree; "
          "only expected source/version files changed; saves, package/signing retained; no build.")
