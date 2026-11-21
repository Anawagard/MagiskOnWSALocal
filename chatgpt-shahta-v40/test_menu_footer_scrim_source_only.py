"""Guard the baked footer navigation contrast without building Android."""
import ast
import math
from pathlib import Path

SOURCE = Path(__file__).with_name('generate_art_v70.py')
EXPECTED = {
    'footer': 'np.clip((title_y - h * 0.78) / (h * 0.22), 0, 1) ** 2',
    'footer_center': '0.55 + 0.45 * np.exp(-((title_x - w * 0.5) / (w * 0.52)) ** 4)',
    'opacity': 'np.clip(0.12 * fade * center + 0.22 * footer * footer_center, 0, 1)[:, :, None]',
}

def test_source():
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    cave = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'cave')
    guards = [n for n in ast.walk(cave) if isinstance(n, ast.If)
              and ast.unparse(n.test) == '31 <= index <= 34']
    assert len(guards) == 2, 'base and final menu-only scrims required'
    final = next(g for g in guards if any(isinstance(n, ast.Name) and n.id == 'footer'
                                           for n in ast.walk(g)))
    assignments = {target.id: ast.unparse(node.value)
                   for node in ast.walk(final) if isinstance(node, ast.Assign)
                   for target in node.targets if isinstance(target, ast.Name)}
    for name, expression in EXPECTED.items():
        assert assignments.get(name) == expression, (name, assignments.get(name))
    # A syntactically present formula is not enough: the final bitmap must
    # actually receive the composite after decorations and before JPEG export.
    assert cave.body[-1].value.func.attr == 'save', 'JPEG export must be last'
    assert isinstance(cave.body[-2], ast.If) and cave.body[-2] is final, (
        'final menu-only scrim must immediately precede JPEG export')
    final_assignments = [n for n in final.body if isinstance(n, ast.Assign)]
    assert isinstance(final_assignments[-1].targets[0], ast.Name)
    assert final_assignments[-1].targets[0].id == 'im', 'composite must replace saved image'
    assert ast.unparse(final_assignments[-1].value) == (
        'image_array(pixels * (1 - opacity) + graphite[None, None, :] * opacity)'
    ), 'footer opacity must be applied to final pixels'
    assert ast.unparse(cave.body[-1].value.func.value) == 'im', (
        'export must use the composited image')

def test_geometry():
    for w,h in [(240,360),(360,570),(1080,1920),(1272,2772)]:
        def alpha(x,y):
            fade = max(0.,min(1.,(.24*h-y)/(.24*h)))**2
            center = math.exp(-((x-.5*w)/(.42*w))**4)
            footer = max(0.,min(1.,(y-.78*h)/(.22*h)))**2
            footer_center = .55+.45*math.exp(-((x-.5*w)/(.52*w))**4)
            return min(1.,max(0.,.12*fade*center+.22*footer*footer_center))
        assert alpha(w/2,.5*h) == 0
        assert alpha(w/2,.78*h) == 0
        assert 0 < alpha(w/2,.9*h) < alpha(w/2,h) <= .22+1e-12
        assert alpha(0,h) < alpha(w/2,h)
        assert alpha(w/2,0) <= .12+1e-12
        for x in (0,w/4,w/2,w):
            for y in (0,.24*h,.5*h,.78*h,.9*h,h):
                assert 0 <= alpha(x,y) <= .22+1e-12

if __name__ == '__main__':
    test_source()
    test_geometry()
    print('PASS: menu footer scrim AST and four viewport geometries')
