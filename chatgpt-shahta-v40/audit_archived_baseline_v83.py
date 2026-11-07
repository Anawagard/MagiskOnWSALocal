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
import unicodedata
from pathlib import PurePosixPath

MAX_ARCHIVE_FILES = 20000
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024

def inspect_tar_members(archive):
    """Validate TAR paths, namespace collisions and bounded payload."""
    files, seen, portable_names, canonical_parts, total = {}, set(), set(), {}, 0
    for member in archive:
        name = member.name
        # TAR directory headers conventionally end in one slash. Accept that
        # canonical form, but reject repeated slashes and empty components.
        if member.isdir() and name.endswith("/") and not name.endswith("//"):
            name = name[:-1]
        path = PurePosixPath(name)
        if (not name or "\\" in name or path.is_absolute() or
                any(part in ("..", ".") for part in name.split("/")) or
                member.issym() or member.islnk() or
                not (member.isfile() or member.isdir())):
            raise ValueError("Unsafe archive entry: " + name)
        # Reject platform-dependent aliases before a future extraction step.
        # Windows treats colons, trailing dots/spaces and control characters
        # specially; POSIX path normalization also collapses repeated slashes.
        parts = name.split("/")
        if (any(not part or part.endswith((".", " ")) or
                any(ch in part for ch in '<>"|?*:') or part.upper().split(".")[0] in (
                    {"CON", "PRN", "AUX", "NUL"} |
                    {f"COM{i}" for i in range(1, 10)} |
                    {f"LPT{i}" for i in range(1, 10)}
                ) or any(ord(ch) < 32 or ord(ch) == 127 for ch in part)
                for part in parts if part) or
                "//" in name or name.startswith("./")):
            raise ValueError("Non-portable archive path: " + repr(name))
        normalized = path.as_posix()
        # Implicit parent directories must also agree on spelling. Otherwise
        # App/a and app/b merge silently on case-insensitive filesystems.
        for index, part in enumerate(path.parts):
            key = tuple(unicodedata.normalize("NFC", p).casefold() for p in path.parts[:index + 1])
            spelling = tuple(path.parts[:index + 1])
            previous = canonical_parts.setdefault(key, spelling)
            if previous != spelling:
                raise ValueError("Case-insensitive parent alias: " + normalized)
        # Case-insensitive filesystems can alias otherwise distinct TAR paths.
        # Reject them before any source tree is extracted on Windows/macOS.
        portable = unicodedata.normalize("NFC", normalized).casefold()
        if portable in portable_names:
            raise ValueError("Case-insensitive archive collision: " + normalized)
        portable_names.add(portable)
        if normalized in seen:
            raise ValueError("Duplicate archive entry: " + normalized)
        if any(parent.as_posix() in files for parent in path.parents if parent.as_posix() != "."):
            raise ValueError("File used as directory: " + normalized)
        if member.isfile() and any(existing.startswith(normalized + "/") for existing in seen):
            raise ValueError("File shadows directory: " + normalized)
        seen.add(normalized)
        if len(seen) > MAX_ARCHIVE_FILES:
            raise ValueError("Too many archive entries")
        if member.isfile():
            if member.size < 0 or member.size > 100 * 1024 * 1024:
                raise ValueError("Unexpected archive file size: " + normalized)
            total += member.size
            if total > MAX_ARCHIVE_BYTES:
                raise ValueError("Archive payload too large")
            files[normalized] = member.size
    return files


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
    if not ARCHIVE.is_file():
        raise FileNotFoundError(f"Missing archived Android baseline: {ARCHIVE}")
    if not WORKFLOW.is_file():
        raise FileNotFoundError(f"Missing manual game workflow: {WORKFLOW}")
    packed = base64.b64decode(ARCHIVE.read_bytes(), validate=True)
    raw = brotli.decompress(packed)
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
        files = inspect_tar_members(archive)
        for target in TARGETS:
            if target not in files:
                raise AssertionError(f"Archive missing {target}; examples: {list(files)[:12]}")
    workflow = WORKFLOW.read_text(encoding="utf-8")
    if not re.search(r"(?m)^  workflow_dispatch:\s*$", workflow):
        raise AssertionError("Game workflow is not manual-only")
    # Also reject inline YAML trigger lists (on: [push]) and quoted keys.
    # The release workflow must not run on commits or pull requests.
    if re.search(r"(?m)^  [\x27\x22]?(push|pull_request|pull_request_target|schedule|workflow_run)[\x27\x22]?\s*:", workflow):
        raise AssertionError("Automatic trigger found")
    if re.search(r"(?m)^on:\s*\[[^\]\n]*(push|pull_request|pull_request_target|schedule|workflow_run)", workflow):
        raise AssertionError("Automatic inline trigger found")
    for patch in ("patch_game.py", "patch_full_redesign_v70.py", "patch_modernist_v71.py"):
        if patch not in workflow:
            raise AssertionError("Release workflow missing " + patch)
    print(f"PASS: {len(files)} archived files; Android sources, Gradle, manual-only release chain present")
    print("NOTE: this is a v3.2 source archive, NOT a prepared v6.9/v7.1 baseline.")
    print("Replaying the release workflow's source patches locally is still required.")
if __name__ == "__main__":
    audit()
