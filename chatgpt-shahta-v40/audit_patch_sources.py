"""Offline audit of the modernist patch chain; no Android baseline required.

Run: python3 chatgpt-shahta-v40/audit_patch_sources.py
Does not execute patch scripts, Gradle, or network requests.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PATCHES = [ROOT / "patch_full_redesign_v70.py", ROOT / "patch_modernist_v71.py"]
PATCHES += [ROOT / f"patch_modernist_v{n}.py" for n in range(72, 78)]
FORBIDDEN = {"subprocess", "requests", "urllib", "http", "socket", "importlib"}
DYNAMIC_CALLS = {"eval", "exec", "compile", "__import__"}
SHELL_CALLS = {("os", "system"), ("os", "popen"), ("os", "spawnl"), ("os", "spawnv")}

def require(condition, message):
    if not condition:
        raise RuntimeError(message)
for path in PATCHES:
    if not path.is_file():
        raise SystemExit(f"BLOCKED: missing patch: {path.name}")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                if (target.value.id, target.attr) in SHELL_CALLS:
                    raise RuntimeError(f"{path.name}: shell invocation")
            elif isinstance(target, ast.Name) and target.id in DYNAMIC_CALLS:
                raise RuntimeError(f"{path.name}: dynamic code execution: {target.id}")
    require(not (imports & FORBIDDEN), f"{path.name}: forbidden imports {imports & FORBIDDEN}")
    require("MineView.java" in source, f"{path.name}: unexpected target")
    require("gradlew" not in source and "workflow_dispatch" not in source,
            f"{path.name}: build or workflow trigger reference")
    print(f"PASS {path.name}: Python syntax and import safety")
print(f"PASS: {len(PATCHES)} source-only patch scripts inspected; baseline application NOT verified")
