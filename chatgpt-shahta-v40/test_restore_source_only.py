"""Offline source restoration regression tests; never invoke Android tooling."""
import base64
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

from restore_source_only import restore, TARGETS

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


if __name__ == "__main__":
    unittest.main()
