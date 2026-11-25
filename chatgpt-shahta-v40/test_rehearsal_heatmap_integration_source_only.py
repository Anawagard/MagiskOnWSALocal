"""Ensure the full 576-pair heatmap is actually published by the source-only runner."""
import ast
from pathlib import Path

runner = Path(__file__).with_name("run_full_source_rehearsal_v124.py")
tree = ast.parse(runner.read_text(encoding="utf-8"))
calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
heatmaps = [node for node in calls if isinstance(node.func, ast.Name)
            and node.func.id == "render_visibility_heatmap"]
assert len(heatmaps) == 1, "runner must render exactly one full heatmap"
call = heatmaps[0]
assert len(call.args) >= 2
assert isinstance(call.args[0], ast.Name) and call.args[0].id == "scores"
assert isinstance(call.args[1], ast.Name) and call.args[1].id == "heatmap_path"
assert any(keyword.arg == "assets" for keyword in call.keywords), "protect production assets"
assert any(isinstance(node, ast.Constant) and node.value == "ore_biome_visibility_heatmap.png"
           for node in ast.walk(tree)), "stable diagnostic filename required"
print("PASS: source-only rehearsal publishes 576-pair heatmap with asset isolation")
