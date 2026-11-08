"""Offline source restoration regression tests; never invoke Android tooling."""
import base64
import io
import hashlib
from pathlib import Path
import tarfile
import tempfile
import unittest

from restore_source_only import restore, TARGETS, ARCHIVE

try:
    import brotli
except ImportError:
    brotli = None


@unittest.skipIf(brotli is None, "brotli dependency not installed")
class RestoreTests(unittest.TestCase):
    def make_archive(self, root, entries):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w") as tar:
            for name, data in entries:
                info = tarfile.TarInfo(name)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
        path = root / "source.tar.br.base64"
        path.write_bytes(base64.b64encode(brotli.compress(stream.getvalue())))
        return path

    def test_real_archived_baseline_byte_exact(self):
        """Exercise the actual archived v3.2 tree, not only synthetic fixtures.

        A source-only regression: no Gradle, Android SDK, emulator or network.
        """
        if not ARCHIVE.is_file():
            self.skipTest("Archived v3.2 source is not present in this checkout")
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "project"
            restored_count = restore(ARCHIVE, destination)
            decoded = brotli.decompress(base64.b64decode(ARCHIVE.read_bytes(), validate=True))
            expected = {}
            with tarfile.open(fileobj=io.BytesIO(decoded), mode="r:") as tar:
                for member in tar:
                    if member.isfile():
                        with tar.extractfile(member) as stream:
                            expected[member.name] = hashlib.sha256(stream.read()).hexdigest()
            self.assertEqual(restored_count, len(expected))
            actual = {
                file.relative_to(destination).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest()
                for file in destination.rglob("*") if file.is_file()
            }
            self.assertEqual(actual, expected)
            for required in TARGETS:
                self.assertIn(required, actual)

    def test_restore_complete_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            entries = [(name, b"source") for name in TARGETS]
            archive = self.make_archive(root, entries)
            destination = root / "project"
            self.assertEqual(restore(archive, destination), len(TARGETS))
            for name in TARGETS:
                self.assertEqual((destination / name).read_bytes(), b"source")

    def test_missing_target_does_not_create_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = self.make_archive(root, [(TARGETS[0], b"source")])
            destination = root / "project"
            with self.assertRaises(ValueError):
                restore(archive, destination)
            self.assertFalse(destination.exists())

    def test_refuses_existing_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            destination = root / "project"
            destination.mkdir()
            archive = root / "irrelevant"
            with self.assertRaises(FileExistsError):
                restore(archive, destination)

    def test_rejects_parent_traversal_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            entries = [(name, b"source") for name in TARGETS]
            entries.append(("../outside.txt", b"escape"))
            archive = self.make_archive(root, entries)
            destination = root / "project"
            with self.assertRaises(ValueError):
                restore(archive, destination)
            self.assertFalse(destination.exists())
            self.assertFalse((root / "outside.txt").exists())

    def test_rejects_duplicate_archive_entry_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            entries = [(name, b"source") for name in TARGETS]
            entries.append((TARGETS[0], b"overwrite"))
            archive = self.make_archive(root, entries)
            destination = root / "project"
            with self.assertRaises(ValueError):
                restore(archive, destination)
            self.assertFalse(destination.exists())

    def test_rejects_file_shadowing_directory_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            entries = [(name, b"source") for name in TARGETS]
            entries.append(("app/src/main/java", b"not-a-directory"))
            archive = self.make_archive(root, entries)
            destination = root / "project"
            with self.assertRaises(ValueError):
                restore(archive, destination)
            self.assertFalse(destination.exists())


    def test_rejects_case_insensitive_alias_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            entries = [(name, b"source") for name in TARGETS]
            entries.append((TARGETS[0].swapcase(), b"alias"))
            archive = self.make_archive(root, entries)
            destination = root / "project"
            with self.assertRaisesRegex(ValueError, "Case-insensitive"):
                restore(archive, destination)
            self.assertFalse(destination.exists())

    def test_rejects_symlink_member_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode="w") as tar:
                for name in TARGETS:
                    info = tarfile.TarInfo(name)
                    info.size = 6
                    tar.addfile(info, io.BytesIO(b"source"))
                link = tarfile.TarInfo("app/src/main/java/escape")
                link.type = tarfile.SYMTYPE
                link.linkname = "../../outside"
                tar.addfile(link)
            archive = root / "source.tar.br.base64"
            archive.write_bytes(base64.b64encode(brotli.compress(stream.getvalue())))
            destination = root / "project"
            with self.assertRaisesRegex(ValueError, "Unsafe archive entry"):
                restore(archive, destination)
            self.assertFalse(destination.exists())
            self.assertFalse((root / "outside").exists())

    def test_invalid_base64_never_creates_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / "invalid.tar.br.base64"
            archive.write_bytes(b"not-valid-base64!!!")
            destination = root / "project"
            with self.assertRaises(ValueError):
                restore(archive, destination)
            self.assertFalse(destination.exists())

    def test_truncated_brotli_never_creates_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = self.make_archive(root, [(name, b"source") for name in TARGETS])
            encoded = base64.b64decode(archive.read_bytes(), validate=True)
            archive.write_bytes(base64.b64encode(encoded[:max(1, len(encoded) // 2)]))
            destination = root / "project"
            with self.assertRaisesRegex(ValueError, "Invalid or truncated Brotli"):
                restore(archive, destination)
            self.assertFalse(destination.exists())

    def test_rejects_absolute_member_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            entries = [(name, b"source") for name in TARGETS]
            entries.append(("/tmp/shahta-absolute-escape", b"escape"))
            archive = self.make_archive(root, entries)
            destination = root / "project"
            with self.assertRaises(ValueError):
                restore(archive, destination)
            self.assertFalse(destination.exists())



if __name__ == "__main__":
    unittest.main()
