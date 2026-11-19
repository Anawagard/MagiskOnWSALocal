"""Source-only contract: decorative cave sidewalls never enter the play lane."""
import ast
from pathlib import Path

source = Path(__file__).with_name("generate_art_v70.py").read_text(encoding="utf-8")
tree = ast.parse(source)
cave = next(node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "cave")
snippet = ast.get_source_segment(source, cave)
contracts = (
    "reach=min(wall_limit-13, int(fingerprint.integers(18,58)))",
    "reach=min(wall_limit-10, int(crystals.integers(17,43)))",
    "depth=min(wall_limit-1, int(plates.integers(22,48)))",
    "reach=min(wall_limit-9, int(wells.integers(17,49)))",
    "reach = min(wall_limit-6, int(seam_rng.integers(22, 58)))",
)
for contract in contracts:
    assert contract in snippet, f"Sidewall contract missing: {contract}"

checks = 0
for width in (240, 320, 360, 1080, 1272):
    wall = max(1, min(70, width // 5))
    # Test maximum reach for each family, at both left and right edges.
    for edge, max_reach, margin in (
        (12, 57, 13),  # geological fingerprint
        (9, 42, 10),   # crystal cluster
        (0, 47, 1),    # parallax plate
        (8, 48, 9),   # mineral light well
        (5, 57, 6),   # stratified seam
    ):
        reach = min(wall - margin, max_reach)
        assert reach >= 0
        assert edge + reach < wall, (width, edge, reach, wall)
        assert width - edge - reach > width - wall
        checks += 3
print(f"Narrow-wall decorations: PASS ({checks} extrema checks)")
