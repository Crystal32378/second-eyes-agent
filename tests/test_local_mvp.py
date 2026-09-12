"""Local MVP pipeline tests — sealed file read-only, no model calls."""
import json
import unittest
from pathlib import Path

from runtime.local_mvp import SEALED_SHA256, compute_coverage, emit_preview, run

ROOT = Path(__file__).resolve().parents[1]
BRIEF = json.loads((ROOT / "briefs/brief-v1.json").read_text(encoding="utf-8"))


class TestLocalMVP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results, cls.error = run()
        assert cls.error is None, cls.error

    def test_pipeline_clean(self):
        self.assertIsNone(self.error)
        self.assertEqual(self.results["sealed_sha256"], SEALED_SHA256)
        self.assertEqual(self.results["model_calls"], 0)
        self.assertFalse(self.results["fixture"])

    def test_buckets_spread(self):
        by_key = {i["asset_key"]: i for i in self.results["items"]}
        self.assertEqual(by_key["ROBE-5059"]["bucket"], "Shortlist")
        for k in ("BACK-5F20", "IMG-4489", "WEAR-8106"):
            self.assertEqual(by_key[k]["bucket"], "Remaining")
        for k in ("IG-262", "IG-277"):
            self.assertEqual(by_key[k]["bucket"], "Needs Review")
        s = self.results["summary"]
        self.assertEqual((s["Shortlist"], s["Needs Review"],
                          s["Remaining"], s["total"]), (1, 2, 3, 6))

    def test_stubbed_flag_precise(self):
        by_key = {i["asset_key"]: i for i in self.results["items"]}
        # ROBE decided on stubbed scene/channel/sku -> flagged.
        self.assertTrue(by_key["ROBE-5059"]["stubbed"])
        # BACK-5F20 decided on docs-sourced has_people (scene stub
        # never consulted) -> not flagged.
        self.assertFalse(by_key["BACK-5F20"]["stubbed"])

    def test_sealed_provenance_carried(self):
        for i in self.results["items"]:
            self.assertEqual(i["model"], "gemini-2.5-flash")
            self.assertEqual(i["prompt_version"], "syn-obs-v1")
            self.assertTrue(i["raw"])
            self.assertIsNotNone(i["manifest"])
            self.assertIn("signals_used", i)

    def test_coverage_computed(self):
        cov = {c["slot"]: c for c in self.results["coverage"]["slots"]}
        self.assertEqual(cov["detail"]["status"], "HAVE")
        self.assertEqual(cov["detail"]["members"], ["ROBE-5059"])
        self.assertEqual(cov["hero"]["status"], "MISSING")
        self.assertEqual(cov["hero"]["members"], [])

    def test_coverage_missing_never_guessed(self):
        empty = compute_coverage(BRIEF, [])
        self.assertTrue(all(c["status"] == "MISSING" for c in empty["slots"]))

    def test_preview_inlines_counts_and_coverage(self):
        dest = ROOT / "outputs" / "test-local-preview.html"
        try:
            emit_preview(self.results, dest)
            text = dest.read_text(encoding="utf-8")
            self.assertIn("Shortlist 1", text)
            self.assertIn("Remaining 3", text)
            self.assertIn("MISSING", text)
            self.assertIn("STUB", text)
        finally:
            if dest.exists():
                dest.unlink()

    def test_local_viewer_wires_to_local_mvp_json(self):
        html_text = (ROOT / "ui/minrun/local.html").read_text(encoding="utf-8")
        self.assertIn('fetch("local-mvp.json")', html_text)
        self.assertIn('id="coverage"', html_text)
        self.assertIn("STUB", html_text)
        self.assertNotIn("18", html_text)


if __name__ == "__main__":
    unittest.main()
