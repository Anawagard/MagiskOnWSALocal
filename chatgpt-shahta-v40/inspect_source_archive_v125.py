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
        # Reject ambiguous entries before trusting a downloaded source ZIP.
        infos = archive.infolist()
        names = [info.filename for info in infos if not info.is_dir()]
        # Directory entries are also extraction paths; validate them too.
        paths = [info.filename[:-1] if info.is_dir() else info.filename
                 for info in infos]
        # Unix symlinks and encrypted entries are unsafe to extract as sources.
        if any(((info.external_attr >> 16) & 0o170000) == 0o120000
               for info in infos):
            raise ValueError("ZIP symlink entries are not permitted")
        if any(info.flag_bits & 1 for info in infos):
            raise ValueError("Encrypted ZIP entries are not permitted")
        if any(info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
               for info in infos):
            raise ValueError("Unsupported ZIP compression method")
        if len(infos) > 50000:
            raise ValueError("Too many ZIP entries")
        if len(infos) != len({info.filename for info in infos}):
            raise ValueError("Duplicate ZIP member paths")
        if any(name.startswith("/") or chr(92) in name or
               any(part in ("", ".", "..") for part in name.split("/"))
               for name in paths):
            raise ValueError("Unsafe or non-canonical ZIP member path")
        # A file must never double as a parent directory for another entry.
        file_paths = set(names)
        if any("/".join(parts[:index]) in file_paths
               for name in paths for parts in [name.split("/")]
               for index in range(1, len(parts))):
            raise ValueError("ZIP file/directory path collision")
        if len(paths) != len(set(paths)):
            raise ValueError("Duplicate ZIP paths across files and directories")
        if sum(info.file_size for info in infos) > 2 * 1024**3:
            raise ValueError("Archive uncompressed size exceeds 2 GiB")
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
