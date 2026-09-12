"""Public runtime export + wiring tests — no model calls.

Verifies the sanitized bundle is mechanically derived (counts/coverage
equal the local MVP), exposes no forbidden payload, keeps required
fields, wires both directions, and leaves the 400-photo mock counts
untouched.
"""
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "ui/runtime"
WORKROOM = ROOT / "ui/workroom"


class TestPublicExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from runtime.export_public import main
        from tests.support import ensure_local_mvp
        ensure_local_mvp()
        assert main() == 0
        cls.public = json.loads((RUNTIME / "results.json").read_text(
            encoding="utf-8"))
        cls.local = json.loads((ROOT / "outputs/local-mvp.json").read_text(
            encoding="utf-8"))
        cls.manifest = json.loads(
            (ROOT / "fixtures/smallset/manifest.json").read_text(
                encoding="utf-8"))
        cls.text = (RUNTIME / "results.json").read_text(encoding="utf-8")
        cls.html = (RUNTIME / "index.html").read_text(encoding="utf-8")

    def test_counts_and_coverage_mechanical(self):
        self.assertEqual(self.public["summary"], {
            k: self.local["summary"][k]
            for k in ("Shortlist", "Needs Review", "Remaining", "total")})
        self.assertEqual(self.public["coverage"], self.local["coverage"])
        self.assertEqual(self.public["brief_id"], self.local["brief_id"])
        self.assertEqual(self.public["sealed_sha256"],
                         self.local["sealed_sha256"])

    def test_required_fields_only_shape(self):
        for item in self.public["items"]:
            self.assertEqual(set(item), {
                "asset_key", "image", "evidence_state", "verdict",
                "bucket", "reason", "pending", "observed",
                "signal_sources", "manifest"})
        self.assertEqual(set(self.public),
                         {"page", "brief_id", "sealed_sha256", "summary",
                          "coverage", "items"})

    def test_forbidden_payload_absent(self):
        blob = self.text + self.html
        for marker in ("\"raw\"", "\"usage\"", "stop_reason",
                       "prompt_version", "GEMINI", "GOOGLE_", "AKIA",
                       "/Users/", "/home/", ".pem", "amazon.nova",
                       "\"resolver\"", "\"fixture\"", "mvp-stub"):
            self.assertNotIn(marker, blob, marker)

    def test_english_verdicts_and_consulted_sources(self):
        import re as _re
        by_key = {i["asset_key"]: i for i in self.public["items"]}
        for item in self.public["items"]:
            for field in ("verdict", "reason"):
                self.assertIsNone(
                    _re.search(r"[\u4e00-\u9fff]", item[field]),
                    (item["asset_key"], field))
            for p in item["pending"]:
                self.assertIsNone(
                    _re.search(r"[\u4e00-\u9fff]", p),
                    (item["asset_key"], p))
        self.assertEqual(by_key["ROBE-5059"]["verdict"], "Match")
        self.assertEqual(by_key["BACK-5F20"]["verdict"], "Mismatch")
        self.assertEqual(by_key["IG-262"]["verdict"], "Insufficient evidence")
        # Only consulted sources are published: BACK-5F20's unconsulted
        # scene stub stays out; IG cards have no sourced signals.
        self.assertEqual(set(by_key["BACK-5F20"]["signal_sources"]), {"has_people"})
        self.assertEqual(by_key["IG-262"]["signal_sources"], {})
        self.assertEqual(
            set(by_key["ROBE-5059"]["signal_sources"]),
            {"scene_claim", "has_people", "channel", "sku", "long_edge"})

    def test_no_clearance_or_ranking_language(self):
        blob = (self.text + self.html).lower()
        self.assertNotIn("legally cleared", blob)
        self.assertNotIn("recommended", blob)
        self.assertIsNone(re.search(r"\bbest\b", blob))
        # The required honesty disclaimers must be present instead.
        self.assertIn("candidate, not clearance", blob)

    def test_images_byte_exact(self):
        by_key = {p["asset_key"]: p for p in self.manifest["photos"]}
        for item in self.public["items"]:
            f = RUNTIME / item["image"]
            self.assertTrue(f.is_file(), item["image"])
            digest = hashlib.sha256(f.read_bytes()).hexdigest()
            self.assertEqual(digest.lower(),
                             by_key[item["asset_key"]]["sha256"].lower())
            self.assertEqual(item["manifest"]["sha256"].lower(),
                             digest.lower())

    def test_stylesheet_identical(self):
        self.assertEqual((RUNTIME / "styles.css").read_bytes(),
                         (WORKROOM / "styles.css").read_bytes())

    def test_bidirectional_links(self):
        for page in ("brief-established.html", "brief-missing.html"):
            text = (WORKROOM / page).read_text(encoding="utf-8")
            self.assertIn('href="../runtime/"', text)
            self.assertIn("View recorded 6-image run", text)
            self.assertNotIn("verified 6-image runtime", text)
        self.assertIn('href="../workroom/brief-established.html"',
                      self.html)
        self.assertIn('fetch("results.json")', self.html)

    def test_mock_counts_untouched(self):
        text = (WORKROOM / "brief-established.html").read_text(
            encoding="utf-8")
        for token in ("12 candidates", "9 candidates", "6 candidates",
                      "2 candidates", "6 of 18 shown", "SIMULATED COUNTS"):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
