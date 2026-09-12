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
        # ROBE publishing facts are owner-verified, so its Shortlist
        # decision no longer depends on a stub.
        self.assertFalse(by_key["ROBE-5059"]["stubbed"])
        # BACK-5F20 decided on docs-sourced has_people (scene stub
        # never consulted) -> not flagged.
        self.assertFalse(by_key["BACK-5F20"]["stubbed"])

    def test_robe_publishing_facts_are_owner_verified(self):
        robe = next(i for i in self.results["items"]
                    if i["asset_key"] == "ROBE-5059")
        self.assertEqual(robe["signals"]["scene_claim"], "product")
        self.assertFalse(robe["signals"]["has_people"])
        self.assertEqual(robe["signals"]["channel"], "instagram")
        self.assertEqual(robe["signals"]["sku"], "NUDE-01")
        for name in ("scene_claim", "has_people", "channel", "sku"):
            self.assertEqual(robe["signal_sources"][name],
                             "owner:Crystal:2026-09-12")

    def test_sealed_provenance_carried(self):
        for i in self.results["items"]:
            self.assertEqual(i["model"], "gemini-2.5-flash")
            self.assertEqual(i["prompt_version"], "syn-obs-v1")
            self.assertIsNotNone(i["manifest"])
            self.assertIn("signals_used", i)

    def test_replay_input_is_tracked_and_public_safe(self):
        """Clean-clone rule: the evidence the MVP reads is in the repo."""
        import subprocess
        from runtime.local_mvp import REPLAY_PATH, REPLAY_SHA256, SEALED_SHA256
        self.assertTrue(REPLAY_PATH.is_file(),
                        "replay input missing — a clean clone cannot run")
        if (ROOT / ".git").exists():
            tracked = subprocess.run(
                ["git", "ls-files", "--error-unmatch",
                 str(REPLAY_PATH.relative_to(ROOT))],
                cwd=ROOT, capture_output=True)
            self.assertEqual(tracked.returncode, 0,
                             "replay input is not tracked by git")
        # In an exported tree there is no .git; the file being here at all
        # is the proof, since only tracked files survive `git archive`.
        raw = REPLAY_PATH.read_bytes()
        import hashlib
        self.assertEqual(hashlib.sha256(raw).hexdigest(), REPLAY_SHA256)
        doc = json.loads(raw.decode("utf-8"))
        self.assertEqual(doc["replay_of"]["sha256"], SEALED_SHA256)
        # Raw model text, usage and stop reasons never enter the repo, and
        # the downstream verdict is recomputed, never replayed.
        for item in doc["items"]:
            for banned in ("raw", "usage", "stop_reason", "verdict",
                           "bucket", "reason", "pending", "resolver"):
                self.assertNotIn(banned, item, banned)
        text = raw.decode("utf-8").lower()
        for marker in ("/users/", "/home/", "akia", "begin private", ".pem"):
            self.assertNotIn(marker, text, marker)

    def test_replay_matches_receipt_when_receipt_present(self):
        """On this machine the original receipt is still here: prove the
        tracked replay is exactly what it derives."""
        from runtime.local_mvp import REPLAY_PATH, SEALED_PATH
        if not SEALED_PATH.is_file():
            self.skipTest("sealed receipt not present (clean clone)")
        from tools.make_replay_input import derive
        self.assertEqual(derive(SEALED_PATH.read_bytes())["text"],
                         REPLAY_PATH.read_text(encoding="utf-8"))

    def test_no_raw_model_text_under_replay(self):
        """Replay carries no raw text; nothing downstream may invent one."""
        for i in self.results["items"]:
            self.assertIsNone(i["raw"])
            self.assertIsNone(i["usage"])
            self.assertIsNone(i["stop_reason"])

    def test_coverage_computed(self):
        cov = {c["slot"]: c for c in self.results["coverage"]["slots"]}
        self.assertEqual(cov["hero"]["status"], "HAVE")
        self.assertEqual(cov["hero"]["members"], ["ROBE-5059"])
        self.assertEqual(cov["detail"]["status"], "MISSING")
        self.assertEqual(cov["detail"]["members"], [])

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
            self.assertNotIn("ROBE-5059</strong> · STUB", text)
        finally:
            if dest.exists():
                dest.unlink()

    def test_local_viewer_wires_to_local_mvp_json(self):
        html_text = (ROOT / "ui/minrun/local.html").read_text(encoding="utf-8")
        self.assertIn('fetch("local-mvp.json")', html_text)
        self.assertIn('id="coverage"', html_text)
        self.assertIn("STUB", html_text)
        self.assertNotIn("18", html_text)

    def test_public_ready_true_without_stubbed_shortlist(self):
        self.assertEqual(self.results["summary"]["stubbed"], 0)
        self.assertTrue(self.results["summary"]["public_ready"])


if __name__ == "__main__":
    unittest.main()
