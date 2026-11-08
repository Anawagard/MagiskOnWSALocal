"""Restore the archived v3.2 Android sources for source-only integration.

No Gradle, Android SDK, GitHub Actions or network access. By default writes to
an explicit disposable directory; refuses to overwrite existing contents.

Usage:
 python3 chatgpt-shahta-v40/restore_source_only.py /tmp/shahta-source/project
"""
import argparse
import base64
import io
from pathlib import Path
import tarfile

from audit_archived_baseline_v83 import inspect_tar_members, ARCHIVE, TARGETS


def restore(archive_path: Path, destination: Path) -> int:
    import brotli
    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")
    # Normalize malformed Base64 into the documented validation error type.
    # binascii.Error otherwise escapes and breaks the source-only regression.
    import binascii
    try:
        packed = base64.b64decode(archive_path.read_bytes(), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Invalid Base64 source archive") from exc
    try:
        decoded = brotli.decompress(packed)
    except brotli.error as exc:
        raise ValueError("Invalid or truncated Brotli source archive") from exc
    # Inspect the *entire* archive before creating any destination files.
    with tarfile.open(fileobj=io.BytesIO(decoded), mode="r:") as tar:
        files = inspect_tar_members(tar)
        missing = set(TARGETS) - files.keys()
        if missing:
            raise ValueError(f"Missing Android source targets: {sorted(missing)}")
        destination.mkdir(parents=True, exist_ok=False)
        try:
            # Extract each member ourselves after path validation. Do not use
            # tarfile.extractall, which also handles links and special entries.
            for member in tar:
                target = destination.joinpath(*member.name.split("/"))
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    # Verify the bytes written, not only the TAR metadata.
                    # A truncated stream must never leave a seemingly valid
                    # restored Android project behind.
                    import hashlib
                    digest = hashlib.sha256()
                    written = 0
                    with tar.extractfile(member) as source, target.open("xb") as sink:
                        while True:
                            block = source.read(1024 * 1024)
                            if not block:
                                break
                            sink.write(block)
                            digest.update(block)
                            written += len(block)
                    if written != member.size or target.stat().st_size != member.size:
                        raise ValueError(
                            f"Truncated archive member {member.name}: "
                            f"expected {member.size}, wrote {written}"
                        )
                    # hashlib.file_digest requires Python 3.11; retain
                    # compatibility with Python 3.9/3.10 for offline audits.
                    verified = hashlib.sha256()
                    with target.open("rb") as restored:
                        while True:
                            block = restored.read(1024 * 1024)
                            if not block:
                                break
                            verified.update(block)
                    if verified.digest() != digest.digest():
                        raise ValueError(f"Restored bytes differ from TAR stream: {member.name}")
            return len(files)
        except BaseException:
            import shutil
            shutil.rmtree(destination)
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    count = restore(ARCHIVE, args.destination.expanduser().resolve())
    print(f"PASS: restored {count} source files to {args.destination}; no build")


if __name__ == "__main__":
    main()
