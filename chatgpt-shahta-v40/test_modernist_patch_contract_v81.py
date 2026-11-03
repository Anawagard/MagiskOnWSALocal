"""Standalone source-only audit for modernist patch series (no Android checkout needed).

Run: python3 chatgpt-shahta-v40/test_modernist_patch_contract_v81.py
This is intentionally independent of the Android baseline and never invokes builds.
"""
from pathlib import Path
import ast
import re

HERE = Path(__file__).resolve().parent
patches = [HERE / f"patch_modernist_v{v}.py" for v in range(72, 78)]
assert all(path.is_file() for path in patches), "Missing one of the six modernist patches"

for version, path in zip(range(72, 78), patches):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    # No shell, network, subprocess or Android build dispatch in source-only patches.
    forbidden = {"subprocess", "requests", "urllib", "socket", "gradle", "os.system"}
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports |= {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert not (imports & forbidden), (path.name, imports & forbidden)
    assert not re.search(r"\b(?:gradlew|assembleDebug|workflow_dispatch)\b", source), path.name
    assert "MineView.java" in source, f"{path.name} does not target MineView"
    assert "assert " in source, f"{path.name} has no guarded anchors"

v72 = patches[0].read_text(encoding="utf-8")
assert 'v72NineSlice(' in v72 and 'v72SectionHeader(' in v72
assert 'p.setFilterBitmap(true)' in v72
v77 = patches[-1].read_text(encoding="utf-8")
assert 'v72NineSlice(canvas,"panel.png",18,240,324,26,252)' in v77
assert 'getSharedPreferences("mine_save_v1"' in v77
print("PASS: six patches parse; guarded MineView edits; raster panels; "
      "toast geometry and save invariant; no build/network dispatch")
