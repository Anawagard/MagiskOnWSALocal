"""Regression: empty ore-risk results publish an explicit fresh PNG.

Source-only; no Android build or workflow dispatch.
"""
import ast
from pathlib import Path

SOURCE = Path(__file__).with_name("audit_ore_biome_composites_source_only.py")


def test_empty_risk_sheet_is_not_deleted():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
              and n.name == "render_risk_contact_sheet")
    calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call)]
    assert not any(isinstance(c.func, ast.Attribute)
                   and c.func.attr == "unlink"
                   and isinstance(c.func.value, ast.Name)
                   and c.func.value.id == "destination" for c in calls)
    assert any(isinstance(c.func, ast.Attribute)
               and isinstance(c.func.value, ast.Name)
               and c.func.value.id == "os" and c.func.attr == "replace"
               for c in calls)
    assert any(isinstance(n, ast.Constant) and n.value == "NO RISK PAIRS"
               for n in ast.walk(fn))
    assert any(isinstance(n, ast.Call)
               and isinstance(n.func, ast.Name) and n.func.id == "max"
               for n in ast.walk(fn)), "zero-result grid must have nonzero dimensions"


if __name__ == "__main__":
    test_empty_risk_sheet_is_not_deleted()
    print("empty risk sheet publication: OK")
