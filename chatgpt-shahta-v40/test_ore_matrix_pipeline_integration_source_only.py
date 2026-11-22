"""Guard real 576-pair raster audit integration; no Android build required."""
from pathlib import Path
import ast

HERE = Path(__file__).resolve().parent
source = (HERE / "verify_generated_art_source_only.py").read_text(encoding="utf-8")
tree = ast.parse(source)
verify = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
              and node.name == "verify")
calls = [node for node in ast.walk(verify) if isinstance(node, ast.Call)]
audit_calls = [node for node in calls if isinstance(node.func, ast.Name)
               and node.func.id == "run" and node.args
               and isinstance(node.args[0], ast.Constant)
               and node.args[0].value == "audit_ore_biome_composites_source_only.py"]
assert len(audit_calls) == 1, "Full raster audit must run exactly once"
call = audit_calls[0]
flags = [arg.value for arg in call.args if isinstance(arg, ast.Constant)
         and isinstance(arg.value, str)]
assert {"--assets", "--risk-sheet", "--heatmap"} <= set(flags)
assert source.index('run("generate_art_v70.py"') < source.index(
    'run("audit_ore_biome_composites_source_only.py"')
assert source.index('run("audit_ore_biome_composites_source_only.py"') < source.index(
    'data = json.loads(report.read_text')
assert 'shahta_ore_biome_heatmap.png' in source
assert 'Missing ore/biome matrix diagnostic' in source
print("PASS: real 576-pair matrix integrated into source-only art pipeline")
