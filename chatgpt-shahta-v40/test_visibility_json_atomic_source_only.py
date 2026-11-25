"""Source-only regression for atomic 576-pair JSON publication.

No Android, Gradle, APK or GitHub Actions are invoked.
"""
import ast
from pathlib import Path

source = (Path(__file__).resolve().parent / "run_full_source_rehearsal_v124.py").read_text(encoding="utf-8")
tree = ast.parse(source)
assert "report_path.write_text(" not in source, "Unsafe direct JSON publication returned"
assert "json.dump(report, handle" in source, "JSON must be serialized to temporary sibling"
assert "allow_nan=False" in source, "Invalid non-finite scores must fail closed"
assert "handle.flush()" in source and "os.fsync(handle.fileno())" in source
assert "os.replace(report_tmp, report_path)" in source
assert "report_tmp.unlink(missing_ok=True)" in source
assert "dir=output_dir, delete=False" in source
print("ATOMIC VISIBILITY JSON SOURCE CONTRACT PASS")
