"""Static source audit for modernist release scripts (no Android build).

Run: python3 chatgpt-shahta-v40/test_python_source_integrity_v89.py
Checks every Python source in this directory, including tests and patch stages.
"""
import ast
from pathlib import Path

HERE = Path(__file__).resolve().parent
scripts = sorted(HERE.glob("*.py"))
assert scripts, "No source scripts found"
checks = 0
for script in scripts:
    raw = script.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), f"Unexpected UTF-8 BOM: {script.name}"
    source = raw.decode("utf-8")
    assert "\x00" not in source, f"NUL byte: {script.name}"
    tree = ast.parse(source, filename=str(script))
    compile(tree, str(script), "exec")
    checks += 4
    # Duplicate top-level function names can silently shadow regression tests.
    names = [node.name for node in tree.body
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    assert len(names) == len(set(names)), f"Duplicate functions: {script.name}"
    checks += 1

print(f"PASS: {len(scripts)} Python scripts parsed and compiled; {checks} static checks; no Android build")
