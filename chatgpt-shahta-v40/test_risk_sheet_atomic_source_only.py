"""Source-only regression: risk contact sheets must publish atomically.

No Android sources, APK builds or workflows are invoked.
"""
import ast
from pathlib import Path

SOURCE = Path(__file__).with_name("audit_ore_biome_composites_source_only.py")


def test_risk_sheet_atomic_publish():
    module = ast.parse(SOURCE.read_text(encoding="utf-8"))
    function = next(node for node in module.body
                    if isinstance(node, ast.FunctionDef)
                    and node.name == "render_risk_contact_sheet")
    calls = [node for node in ast.walk(function) if isinstance(node, ast.Call)]
    def has_call(root, name):
        return any(isinstance(call.func, ast.Attribute)
                   and isinstance(call.func.value, ast.Name)
                   and call.func.value.id == root
                   and call.func.attr == name for call in calls)
    assert has_call("tempfile", "NamedTemporaryFile"), "missing sibling temporary file"
    assert has_call("os", "replace"), "missing atomic replace"
    assert any(isinstance(call.func, ast.Attribute)
               and isinstance(call.func.value, ast.Name)
               and call.func.value.id == "sheet"
               and call.func.attr == "save"
               and call.args and isinstance(call.args[0], ast.Name)
               and call.args[0].id == "temporary" for call in calls), (
                   "risk sheet must be saved to the temporary path")
    assert not any(isinstance(call.func, ast.Attribute)
                   and isinstance(call.func.value, ast.Name)
                   and call.func.value.id == "sheet"
                   and call.func.attr == "save"
                   and call.args and isinstance(call.args[0], ast.Name)
                   and call.args[0].id == "destination" for call in calls), (
                       "direct writes to final risk sheet are forbidden")


if __name__ == "__main__":
    test_risk_sheet_atomic_publish()
    print("risk contact sheet atomic publication: OK")
