"""Validate a downloaded GitHub ZIP before attempting the source-only rehearsal.

Run: python3 chatgpt-shahta-v40/inspect_source_archive_v125.py path/to/archive.zip
This tool never extracts files, invokes Gradle, or starts a build.
"""
from pathlib import Path
import sys
import zipfile

REQUIRED = (
    "chatgpt-shahta-v32/source.tar.br.base64",
    "chatgpt-shahta-v40/restore_source_only.py",
    "chatgpt-shahta-v40/replay_baseline_source_only.py",
    "chatgpt-shahta-v40/verify_modernist_patch_chain.py",
    "chatgpt-shahta-v40/run_full_source_rehearsal_v124.py",
    "chatgpt-shahta-v40/patch_modernist_v79.py",
)


def inspect(path):
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        roots = {name.split("/", 1)[0] for name in names}
        if len(roots) != 1:
            raise ValueError(f"Expected one GitHub archive root; got {sorted(roots)}")
        root = roots.pop()
        members = {name[len(root) + 1:] for name in names if name.startswith(root + "/")}
        missing = [name for name in REQUIRED if name not in members]
        return root, missing


def main(argv):
    if len(argv) != 2:
        raise SystemExit("Usage: python inspect_source_archive_v125.py downloaded-branch.zip")
    root, missing = inspect(Path(argv[1]))
    print(f"ARCHIVE ROOT: {root}")
    if missing:
        print("BLOCKED: archive lacks the modernist source branch files:")
        for path in missing:
            print(f"  MISSING {path}")
        print("Download ZIP from branch chatgpt-shahta-v40-redesign-20261102, not main.")
        return 2
    print("PASS: required archived baseline and modernist source scripts present")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
