"""Read-only audit of modernist PNG sprites. No Android SDK, Gradle or builds.

Usage: python3 chatgpt-shahta-v40/audit_raster_assets.py [asset-directory]
The directory must contain biome_00.png..biome_23.png and
ore_00.png..ore_23.png (subdirectories are allowed).
Only standard-library modules are used.
"""
from pathlib import Path
import argparse
import struct
import sys
import zlib

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
REQUIRED = tuple(f"{kind}_{i:02d}.png" for kind in ("biome", "ore") for i in range(24))


def inspect_png(path):
    """Validate PNG chunk framing/CRC and return dimensions and color mode."""
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("invalid PNG signature")
    pos = len(PNG_SIGNATURE)
    dimensions = None
    saw_iend = False
    saw_idat = False
    while pos < len(data):
        if pos + 12 > len(data):
            raise ValueError("truncated chunk header")
        length = struct.unpack_from(">I", data, pos)[0]
        if length > 64 * 1024 * 1024:
            raise ValueError("unreasonably large PNG chunk")
        end = pos + 12 + length
        if end > len(data):
            raise ValueError("truncated PNG chunk")
        kind = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        crc = struct.unpack_from(">I", data, pos + 8 + length)[0]
        if zlib.crc32(kind + payload) & 0xffffffff != crc:
            raise ValueError("PNG chunk CRC mismatch")
        if pos == 8 and kind != b"IHDR":
            raise ValueError("IHDR must be first")
        if kind == b"IHDR":
            if dimensions is not None or length != 13:
                raise ValueError("duplicate or malformed IHDR")
            width, height, depth, mode, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if not 0 < width <= 8192 or not 0 < height <= 8192:
                raise ValueError("invalid or excessive sprite dimensions")
            if compression != 0 or filtering != 0 or interlace not in (0, 1):
                raise ValueError("unsupported PNG header")
            if (mode, depth) not in {(2, 8), (6, 8), (3, 8), (0, 8), (4, 8)}:
                raise ValueError("unsupported PNG color mode/depth")
            dimensions = (width, height, mode)
        elif kind == b"IDAT":
            saw_idat = True
        elif kind == b"IEND":
            if length != 0:
                raise ValueError("invalid IEND")
            saw_iend = True
            if end != len(data):
                raise ValueError("trailing bytes after IEND")
            break
        elif kind[0] & 0x20 == 0 and kind not in (b"PLTE",):
            raise ValueError(f"unknown critical PNG chunk {kind!r}")
        pos = end
    if not saw_iend or not saw_idat or dimensions is None:
        raise ValueError("missing IHDR, IDAT or IEND")
    return dimensions


def audit(root):
    if not root.is_dir():
        raise ValueError(f"asset directory does not exist: {root}")
    found = {}
    for path in root.rglob("*.png"):
        if path.name in REQUIRED:
            found.setdefault(path.name, []).append(path)
    failures = []
    for name in REQUIRED:
        matches = found.get(name, [])
        if len(matches) != 1:
            failures.append(f"{name}: expected exactly one file, found {len(matches)}")
            continue
        try:
            width, height, mode = inspect_png(matches[0])
            if width < 24 or height < 24:
                failures.append(f"{name}: sprite too small ({width}x{height})")
            if name.startswith("ore_") and mode not in (6, 4):
                failures.append(f"{name}: ore sprite needs alpha (RGBA/gray-alpha), mode={mode}")
        except (OSError, ValueError) as exc:
            failures.append(f"{name}: {exc}")
    if failures:
        for failure in failures:
            print("FAIL:", failure, file=sys.stderr)
        return 1
    print("PASS: 24 biome + 24 ore PNG files; dimensions, alpha and PNG framing verified")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset_directory", type=Path,
                        help="directory containing modernist sprite PNGs")
    args = parser.parse_args()
    try:
        return audit(args.asset_directory)
    except (OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
