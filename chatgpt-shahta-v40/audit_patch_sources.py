"""Offline audit of the modernist patch chain; no Android baseline required.

Run: python3 chatgpt-shahta-v40/audit_patch_sources.py
Does not execute patch scripts, Gradle, or network requests.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PATCHES = [ROOT / "patch_full_redesign_v70.py", ROOT / "patch_modernist_v71.py"]
PATCHES += [ROOT / f"patch_modernist_v{n}.py" for n in range(72, 80)]
FORBIDDEN = {"subprocess", "requests", "urllib", "http", "socket", "importlib", "shutil"}
DYNAMIC_CALLS = {"eval", "exec", "compile", "__import__"}
SHELL_CALLS = {("os", "system"), ("os", "popen"), ("os", "spawnl"), ("os", "spawnv"), ("os", "execv"), ("os", "execve")}

def require(condition, message):
    if not condition:
        raise RuntimeError(message)
def check_execution_safety(tree, label):
    """Reject direct and aliased process execution, including imported os helpers."""
    os_aliases = {"os"}
    shell_aliases = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "os":
                    os_aliases.add(alias.asname or "os")
        elif isinstance(node, ast.ImportFrom) and node.module == "os":
            for alias in node.names:
                if alias.name in {name for _, name in SHELL_CALLS}:
                    shell_aliases.add(alias.asname or alias.name)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        if isinstance(target, ast.Name) and target.id in DYNAMIC_CALLS | shell_aliases:
            raise RuntimeError(f"{label}: unsafe execution: {target.id}")
        if (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name)
                and target.value.id in os_aliases
                and ("os", target.attr) in SHELL_CALLS):
            raise RuntimeError(f"{label}: unsafe os execution: {target.attr}")

# Verify the alias detector before auditing the real patch chain.
for fixture in ("import os as operating\\noperating.system('echo no')",
                "from os import popen as launch\\nlaunch('echo no')",
                "from os import execve\\nexecve('x', [], {})"):
    try:
        check_execution_safety(ast.parse(fixture), "negative fixture")
    except RuntimeError:
        pass
    else:
        raise AssertionError("Unsafe execution fixture was accepted")

for path in PATCHES:
    if not path.is_file():
        raise SystemExit(f"BLOCKED: missing patch: {path.name}")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    check_execution_safety(tree, path.name)
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
    require(not any(s in source for s in (".github/workflows/", "gradle assemble", "assembleDebug", "adb install")), f"{path.name}: build or workflow mutation reference")
    require("gradlew" not in source and "workflow_dispatch" not in source,
            f"{path.name}: build or workflow trigger reference")
    print(f"PASS {path.name}: Python syntax and import safety")
assert len(PATCHES) == 10, "expected v7.0 and v7.1-v7.9 patches"
print(f"PASS: {len(PATCHES)} source-only patch scripts inspected; baseline application NOT verified")
