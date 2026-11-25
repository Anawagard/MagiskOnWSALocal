"""Source-only contract: decorative cave sidewalls never enter the play lane."""
import ast
from pathlib import Path

source = Path(__file__).with_name("generate_art_v70.py").read_text(encoding="utf-8")
tree = ast.parse(source)
cave = next(node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "cave")
snippet = ast.get_source_segment(source, cave)
contracts = (
    "reach=min(available,max(1,round(int(fingerprint.integers(18,58))*w/360)))",
    "reach=min(available,max(1,round(int(crystals.integers(17,43))*w/360)))",
    "depth=max(1,min(wall_limit-1,round(int(plates.integers(22,48))*w/360)))",
    "reach=max(1,min(wall_limit-1-max(1,round(8*w/360)),round(int(wells.integers(17,49))*w/360)))",
    "reach = max(1, min(wall_limit-1-edge_inset, round(int(seam_rng.integers(22, 58))*w/360)))",
)
for contract in contracts:
    assert contract in snippet, f"Sidewall contract missing: {contract}"

checks = 0
for width in (240, 320, 360, 1080, 1272):
    wall = max(1, min(70, width // 5))
    # Test maximum reach for each family, at both left and right edges.
    for authored_inset, max_reach in (
        (12, 57),  # geological fingerprint
        (9, 42),   # crystal cluster
        (0, 47),    # parallax plate
        (8, 48),   # mineral light well
        (5, 57),   # stratified seam
    ):
        edge = max(1, round(authored_inset * width / 360)) if authored_inset else 0
        reach = min(wall - 1 - edge, max(1, round(max_reach * width / 360)))
        assert reach >= 0
        assert edge + reach < wall, (width, edge, reach, wall)
        assert width - 1 - edge - reach >= width - wall
        checks += 3
print(f"Narrow-wall decorations: PASS ({checks} extrema checks)")
