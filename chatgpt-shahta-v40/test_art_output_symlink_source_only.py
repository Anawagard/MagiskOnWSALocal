"""Source-only regression: reject symlinked raster audit destinations.

No Android source restoration, build, emulator or workflow dispatch.
"""
import importlib.util
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "shahta_art_verify", HERE / "verify_generated_art_source_only.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory(prefix="shahta-symlink-guard-") as tmp:
    base = Path(tmp)
    target = base / "empty-target"
    target.mkdir()
    alias = base / "alias"
    alias.symlink_to(target, target_is_directory=True)
    # Match CLI path normalization. resolve() would silently erase the alias.
    output = alias.expanduser().absolute()
    assert output.is_symlink()
    try:
        module.verify(output)
    except ValueError as exc:
        assert "symlinked art output" in str(exc), str(exc)
    else:
        raise AssertionError("Symlinked audit destination was accepted")
    assert not list(target.iterdir()), "Audit unexpectedly wrote through symlink"

print("PASS: symlinked output rejected before raster generation (source-only)")
