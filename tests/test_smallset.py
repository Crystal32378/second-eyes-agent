"""Small-set manifest verification tests — temp files only, no model calls."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from runtime.smallset import check_binding, verify_manifest

ROOT = Path(__file__).resolve().parents[1]


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


def tiny_manifest(keys, convention="workroom:frame-full"):
    return {"brief": "briefs/brief-v1.json",
            "ref_convention": convention,
            "photos": [{"asset_key": k, "path": "p", "sha256": "s",
                        "old_label": "none"} for k in keys]}


def tiny_photo(key, ref="workroom:frame-full"):
    return {"asset_key": key,
            "observed": {"colour": {"value": "beige", "ref": ref}},
            "old": {}, "signals": {}}


class TestBinding(unittest.TestCase):
    """Custody gate: manifest <-> observations must bind one to one."""

    def test_ok_binding(self):
        m = tiny_manifest(["A", "B"])
        rep = check_binding(m, [tiny_photo("A"), tiny_photo("B")], False)
        self.assertTrue(rep["ok"], rep["errors"])

    def test_reported_counterexample_fails(self):
        # Fu round 2: real manifest + unrelated FIX observations passed.
        manifest = json.loads((ROOT / "fixtures/smallset/manifest.json")
                              .read_text(encoding="utf-8"))
        obs = json.loads((ROOT / "fixtures/minrun/observations.json")
                         .read_text(encoding="utf-8"))
        rep = check_binding(manifest, obs["photos"],
                            bool(obs.get("fixture", False)))
        self.assertFalse(rep["ok"])
        blob = " ".join(rep["errors"])
        self.assertIn("fixture:true", blob)
        self.assertIn("not in manifest", blob)
        self.assertIn("convention", blob)

    def test_missing_entry_fails(self):
        m = tiny_manifest(["A", "B"])
        rep = check_binding(m, [tiny_photo("A")], False)
        self.assertFalse(rep["ok"])
        self.assertTrue(any("count mismatch" in e for e in rep["errors"]))
        self.assertTrue(any("missing in observations: B" in e
                            for e in rep["errors"]))

    def test_extra_entry_fails(self):
        m = tiny_manifest(["A"])
        rep = check_binding(m, [tiny_photo("A"), tiny_photo("Z")], False)
        self.assertFalse(rep["ok"])
        self.assertTrue(any("not in manifest: Z" in e for e in rep["errors"]))

    def test_duplicate_asset_fails(self):
        m = tiny_manifest(["A"])
        rep = check_binding(m, [tiny_photo("A"), tiny_photo("A")], False)
        self.assertFalse(rep["ok"])
        self.assertTrue(any("duplicate" in e for e in rep["errors"]))

    def test_fixture_mixing_rejected(self):
        m = tiny_manifest(["A"])
        rep = check_binding(m, [tiny_photo("A")], True)
        self.assertFalse(rep["ok"])
        self.assertTrue(any("fixture:true" in e for e in rep["errors"]))

    def test_ref_convention_mismatch_fails(self):
        m = tiny_manifest(["A"])
        rep = check_binding(m, [tiny_photo("A", ref="test:frame-full")],
                            False)
        self.assertFalse(rep["ok"])
        self.assertTrue(any("convention" in e for e in rep["errors"]))


if __name__ == "__main__":
    unittest.main()
