"""Small-set manifest verification tests — temp files only, no model calls."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from runtime.smallset import verify_manifest


def manifest_for(path, sha, ref_convention="workroom:frame-full",
                 extra=None):
    photos = [{"asset_key": "T-01", "path": path, "sha256": sha,
               "old_label": "none"}]
    if extra:
        photos[0].update(extra)
    doc = {"brief": "briefs/brief-v1.json", "photos": photos}
    if ref_convention is not None:
        doc["ref_convention"] = ref_convention
    return doc


class TestVerifyManifest(unittest.TestCase):
    def test_ok(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "a.jpg"
            f.write_bytes(b"bytes-1")
            sha = hashlib.sha256(b"bytes-1").hexdigest()
            rep = verify_manifest(manifest_for("a.jpg", sha), Path(d))
            self.assertTrue(rep["ok"], rep["errors"])
            self.assertEqual(rep["ref_convention"], "workroom:frame-full")

    def test_sha_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "a.jpg"
            f.write_bytes(b"bytes-1")
            rep = verify_manifest(manifest_for("a.jpg", "0" * 64), Path(d))
            self.assertFalse(rep["ok"])
            self.assertTrue(any("mismatch" in e for e in rep["errors"]))

    def test_missing_file_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            rep = verify_manifest(
                manifest_for("gone.jpg", "0" * 64), Path(d))
            self.assertFalse(rep["ok"])
            self.assertTrue(any("not found" in e for e in rep["errors"]))

    def test_missing_ref_convention_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "a.jpg"
            f.write_bytes(b"x")
            sha = hashlib.sha256(b"x").hexdigest()
            rep = verify_manifest(
                manifest_for("a.jpg", sha, ref_convention=None), Path(d))
            self.assertFalse(rep["ok"])
            self.assertIn("manifest missing ref_convention", rep["errors"])

    def test_real_manifest_verifies_against_repo(self):
        root = Path(__file__).resolve().parents[1]
        doc = json.loads((root / "fixtures/smallset/manifest.json")
                         .read_text(encoding="utf-8"))
        rep = verify_manifest(doc, root)
        self.assertTrue(rep["ok"], rep["errors"])
        self.assertEqual(len(rep["entries"]), 6)


if __name__ == "__main__":
    unittest.main()
