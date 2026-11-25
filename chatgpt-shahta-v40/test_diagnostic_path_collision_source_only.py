"""Source-only guard against overwriting one diagnostic with another.

No Android, Gradle, emulator or network operations.
"""
import ast
from pathlib import Path

SOURCE = Path(__file__).with_name("audit_ore_biome_composites_source_only.py")
tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
main = next(node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main")
guards = [node for node in ast.walk(main) if isinstance(node, ast.If)]
collision_guards = [
    node for node in guards
    if "risk_sheet.resolve()" in ast.unparse(node.test)
    and "heatmap.resolve()" in ast.unparse(node.test)
]
assert len(collision_guards) == 1, "Both diagnostic destinations must be compared after resolution"
assert any(isinstance(node, ast.Call)
           and isinstance(node.func, ast.Attribute)
           and node.func.attr == "error"
           and isinstance(node.func.value, ast.Name)
           and node.func.value.id == "parser"
           for node in ast.walk(collision_guards[0])), "A collision must fail before analysis"
analysis_calls = [
    node for node in ast.walk(main)
    if isinstance(node, ast.Call)
    and isinstance(node.func, ast.Name) and node.func.id == "analyze"
]
assert len(analysis_calls) == 1
assert collision_guards[0].lineno < analysis_calls[0].lineno
print("DIAGNOSTIC OUTPUT COLLISION SOURCE-ONLY PASS")
