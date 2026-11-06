"""Source-only provenance check for the archived Android baseline.

The repository intentionally stores the v3.2 project as a Brotli-compressed,
base64-encoded tarball; the v7.1 project is produced by the manual release
workflow, not committed as a directory. No Gradle, network or Actions invoked.
Requires the same 'brotli' Python package as the manual workflow.
"""
import base64
import io
from pathlib import Path
import re
import tarfile

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "chatgpt-shahta-v32/source.tar.br.base64"
WORKFLOW = ROOT / ".github/workflows/chatgpt-shahta-v40.yml"
TARGETS = (
    "app/src/main/java/com/bezdna/mine/MineView.java",
    "app/src/main/java/com/bezdna/mine/MainActivity.java",
    "app/build.gradle",
)
def audit():
    import brotli
    assert ARCHIVE.is_file() and WORKFLOW.is_file()
    packed = base64.b64decode(ARCHIVE.read_bytes(), validate=True)
    raw = brotli.decompress(packed)
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
        files = {}
        seen = set()
        for member in archive.getmembers():
            # Reject aliases and special entries before any future extraction.
            # PurePosixPath is required: archive names always use POSIX separators.
            from pathlib import PurePosixPath
            path = PurePosixPath(member.name)
            if (path.is_absolute() or ".." in path.parts or
                    member.issym() or member.islnk() or
                    not (member.isfile() or member.isdir())):
                raise ValueError("Unsafe archive entry: " + member.name)
            normalized = path.as_posix()
            if normalized in seen:
                raise ValueError("Duplicate archive entry: " + normalized)
            seen.add(normalized)
            if member.isfile():
                if member.size < 0 or member.size > 100 * 1024 * 1024:
                    raise ValueError("Unexpected archive file size: " + normalized)
                files[normalized] = member.size
        for target in TARGETS:
            if target not in files:
                raise AssertionError(f"Archive missing {target}; examples: {list(files)[:12]}")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    if not re.search(r"(?m)^  workflow_dispatch:\s*$", workflow):
        raise AssertionError("Game workflow is not manual-only")
    if re.search(r"(?m)^  (push|pull_request|schedule):", workflow):
        raise AssertionError("Automatic trigger found")
    for patch in ("patch_game.py", "patch_full_redesign_v70.py", "patch_modernist_v71.py"):
        if patch not in workflow:
            raise AssertionError("Release workflow missing " + patch)
    print(f"PASS: {len(files)} archived files; Android sources, Gradle, manual-only release chain present")
    print("NOTE: this is a v3.2 source archive, NOT a prepared v6.9/v7.1 baseline.")
    print("Replaying the release workflow's source patches locally is still required.")
if __name__ == "__main__":
    audit()
