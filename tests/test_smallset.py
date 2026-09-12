"""Small-set manifest verification tests — temp files only, no model calls."""
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime.smallset import apply_manifest, check_binding, verify_manifest

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

    def test_ref_suffix_spoof_rejected(self):
        # Exact equality: convention + "-evil" must NOT pass.
        m = tiny_manifest(["A"])
        rep = check_binding(
            m, [tiny_photo("A", ref="workroom:frame-full-evil")], False)
        self.assertFalse(rep["ok"])
        self.assertTrue(any("convention" in e for e in rep["errors"]))


CONVENTION = "workroom:frame-full"
BRIEF_V1 = json.loads((ROOT / "briefs/brief-v1.json").read_text(
    encoding="utf-8"))
GOOD_SIGNALS = {"scene_claim": "product", "has_people": False,
                "long_edge": 1400, "channel": "instagram", "sku": "NUDE-01"}


def round3_setup(d, old_label="beige"):
    """Temp manifest + one real byte file. Paths are absolute so
    verify_manifest resolves them regardless of repo root."""
    asset = Path(d) / "a.jpg"
    asset.write_bytes(b"round3-bytes")
    sha = hashlib.sha256(b"round3-bytes").hexdigest()
    manifest = {"brief": "briefs/brief-v1.json",
                "ref_convention": CONVENTION,
                "photos": [{"asset_key": "R3-01", "path": str(asset),
                            "sha256": sha, "old_label": old_label}]}
    return manifest


def round3_photo(old, ref=CONVENTION):
    return {"asset_key": "R3-01",
            "observed": {"colour": {"value": "beige", "ref": ref},
                         "item": {"value": "bra", "ref": ref}},
            "old": old,
            "signals": dict(GOOD_SIGNALS),
            "signal_sources": {s: "test:declared" for s in GOOD_SIGNALS}}


class TestCustodyRound3(unittest.TestCase):
    def test_old_label_swap_neutralized(self):
        # Observations smuggle old "red dress" (would route CONFLICT);
        # manifest injects "beige", so routing follows the manifest.
        from runtime.run_min import run
        with tempfile.TemporaryDirectory() as d:
            manifest = round3_setup(d, old_label="beige")
            smuggled = round3_photo(old={"colour": "red dress",
                                         "item": "red",
                                         "shot": "red"})
            bound = apply_manifest(manifest, [smuggled])
            self.assertEqual(bound[0]["old"],
                             {"colour": "beige",
                              "item": "beige",
                              "shot": "beige"})
            results = run(BRIEF_V1, bound, fixture=False)
            item = results["items"][0]
            self.assertEqual(item["evidence_state"], "CLEAR")
            self.assertEqual(item["bucket"], "Shortlist")

    def test_brief_swap_aborts(self):
        from runtime.run_min import main
        with tempfile.TemporaryDirectory() as d:
            manifest = round3_setup(d)
            obs = {"fixture": False,
                   "photos": [round3_photo(old={"colour": "x"})]}
            manifest_path = os.path.join(d, "manifest.json")
            obs_path = os.path.join(d, "obs.json")
            out_path = os.path.join(d, "out.json")
            Path(manifest_path).write_text(json.dumps(manifest),
                                           encoding="utf-8")
            Path(obs_path).write_text(json.dumps(obs), encoding="utf-8")
            argv = ["run_min.py", "--brief", "briefs/other.json",
                    "--manifest", manifest_path, "--obs", obs_path,
                    "--out", out_path]
            with patch.object(sys, "argv", argv):
                rc = main()
            self.assertEqual(rc, 2)
            self.assertFalse(os.path.exists(out_path))


def sealed_manifest(entries, convention="workroom:frame-full"):
    return {"brief": "briefs/brief-v1.json", "ref_convention": convention,
            "photos": entries}


def sealed_entry(key, path="p", sha="s", old_label="none"):
    return {"asset_key": key,
            "manifest": {"path": path, "sha256": sha,
                         "ref_convention": "workroom:frame-full"},
            "old": {"colour": old_label, "item": old_label,
                    "shot": old_label}}


def manifest_entry(key, path="p", sha="s", old_label="none"):
    return {"asset_key": key, "path": path, "sha256": sha,
            "old_label": old_label}


class TestSealedBinding(unittest.TestCase):
    def test_ok(self):
        from runtime.smallset import check_sealed_binding
        m = sealed_manifest([manifest_entry("A")])
        rep = check_sealed_binding(m, [sealed_entry("A")])
        self.assertTrue(rep["ok"], rep["errors"])

    def test_swapped_file_rejected(self):
        # Same asset_key, another legal file + SHA: verify_manifest
        # would still pass, but the sealed evidence belongs to the old
        # file. Must stop.
        from runtime.smallset import check_sealed_binding
        m = sealed_manifest([manifest_entry("A", path="other.jpg",
                                            sha="1" * 64)])
        rep = check_sealed_binding(m, [sealed_entry("A")])
        self.assertFalse(rep["ok"])
        blob = " ".join(rep["errors"])
        self.assertIn("other.jpg", blob)

    def test_old_label_change_rejected(self):
        from runtime.smallset import check_sealed_binding
        m = sealed_manifest([manifest_entry("A", old_label="beige")])
        rep = check_sealed_binding(m, [sealed_entry("A", old_label="none")])
        self.assertFalse(rep["ok"])
        self.assertTrue(any("old" in e for e in rep["errors"]))

    def test_key_set_mismatch_rejected(self):
        from runtime.smallset import check_sealed_binding
        m = sealed_manifest([manifest_entry("A")])
        rep = check_sealed_binding(m, [sealed_entry("B")])
        self.assertFalse(rep["ok"])
        self.assertTrue(any("missing in sealed: A" in e
                            for e in rep["errors"]))

    def test_sealed_duplicate_rejected(self):
        from runtime.smallset import check_sealed_binding
        m = sealed_manifest([manifest_entry("A")])
        rep = check_sealed_binding(
            m, [sealed_entry("A"), sealed_entry("A")])
        self.assertFalse(rep["ok"])
        self.assertTrue(any("duplicate" in e for e in rep["errors"]))

    def test_real_sealed_binds_current_manifest(self):
        """Reads the TRACKED replay input so a clean clone can run this."""
        from runtime.smallset import check_sealed_binding
        manifest = json.loads((ROOT / "fixtures/smallset/manifest.json")
                              .read_text(encoding="utf-8"))
        sealed = json.loads(
            (ROOT / "fixtures/smallset/sealed-public.json")
            .read_text(encoding="utf-8"))
        rep = check_sealed_binding(manifest, sealed["items"])
        self.assertTrue(rep["ok"], rep["errors"])


if __name__ == "__main__":
    unittest.main()
