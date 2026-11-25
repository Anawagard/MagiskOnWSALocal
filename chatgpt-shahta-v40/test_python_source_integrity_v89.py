"""Static source audit for modernist release scripts (no Android build).

Run: python3 chatgpt-shahta-v40/test_python_source_integrity_v89.py
Checks every Python source in this directory, including tests and patch stages.
"""
import ast
from pathlib import Path

HERE = Path(__file__).resolve().parent
scripts = sorted(HERE.glob("*.py"))
assert scripts, "No source scripts found"
def assert_unique_definitions(body, context):
    """Detect shadowed definitions in each lexical function/class scope."""
    definitions = [node for node in body
                   if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    names = [node.name for node in definitions]
    assert len(names) == len(set(names)), f"Duplicate definitions in {context}"
    for node in definitions:
        assert_unique_definitions(node.body, f"{context}.{node.name}")
    # Definitions inside a single control-flow suite also share a lexical
    # namespace. Check each suite independently: definitions in opposite
    # if/else or try/except branches can legitimately be alternatives.
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue  # Already visited above.
        suites = []
        if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While)):
            suites = [node.body, node.orelse]
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            suites = [node.body]
        elif isinstance(node, (ast.Try, getattr(ast, "TryStar", ast.Try))):
            suites = [node.body, node.orelse, node.finalbody]
            suites.extend(handler.body for handler in node.handlers)
        elif isinstance(node, ast.Match):
            suites = [case.body for case in node.cases]
        for index, suite in enumerate(suites):
            if suite:
                assert_unique_definitions(suite, f"{context}.{type(node).__name__}[{index}]")


# Negative fixtures ensure the detector actually rejects shadowing.
for sample in ("def f(): pass\ndef f(): pass",
               "class C:\n def f(self): pass\n def f(self): pass",
               "class C: pass\nclass C: pass",
               "def outer():\n def inner(): pass\n def inner(): pass",
               "async def outer():\n async def inner(): pass\n async def inner(): pass",
               "if True:\n def duplicated(): pass\n def duplicated(): pass",
               "try:\n def duplicated(): pass\n def duplicated(): pass\nexcept Exception: pass"):
    try:
        assert_unique_definitions(ast.parse(sample).body, "fixture")
    except AssertionError:
        pass
    else:
        raise AssertionError("Duplicate-definition fixture was accepted")

checks = 0
for script in scripts:
    raw = script.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), f"Unexpected UTF-8 BOM: {script.name}"
    source = raw.decode("utf-8")
    assert "\x00" not in source, f"NUL byte: {script.name}"
    tree = ast.parse(source, filename=str(script))
    compile(tree, str(script), "exec")
    checks += 4
    assert_unique_definitions(tree.body, script.name)
    checks += 1

print(f"PASS: {len(scripts)} Python scripts parsed and compiled; {checks} static checks; no Android build")
