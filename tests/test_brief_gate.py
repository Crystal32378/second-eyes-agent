"""Brief-gate + min-run pipeline tests — fixed data only, no model calls.

Covers the four required scenarios (missing brief, missing evidence,
explicit mismatch, new-photo match) and all evidence states reaching
all three brief verdicts, including CLEAR + 證據不足 -> Needs Review.
"""
import json
import unittest
from pathlib import Path

from agent.loop import route
from runtime.brief_gate import gate
from runtime.run_min import emit_preview, run

ROOT = Path(__file__).resolve().parents[1]
BRIEF = json.loads((ROOT / "briefs/brief-v1.json").read_text(encoding="utf-8"))
OBS = json.loads((ROOT / "fixtures/minrun/observations.json").read_text(
    encoding="utf-8"))["photos"]


def photo(key):
    return next(p for p in OBS if p["asset_key"] == key)


def gated(key, brief=BRIEF):
    p = photo(key)
    state = route({"observed": p.get("observed") or {},
                   "old": p.get("old") or {}})
    return gate({**p, "evidence_state": state}, brief), state


class TestFourScenarios(unittest.TestCase):
    def test_new_photo_match_shortlist(self):
        r, state = gated("FIX-NEW-MATCH")
        self.assertEqual(state, "NEW")
        self.assertEqual((r["verdict"], r["bucket"]), ("符合", "Shortlist"))

    def test_explicit_mismatch_remaining(self):
        r, state = gated("FIX-CLEAR-MISMATCH")
        self.assertEqual(state, "CLEAR")
        self.assertEqual((r["verdict"], r["bucket"]), ("明確不符", "Remaining"))

    def test_missing_evidence_needs_review(self):
        r, state = gated("FIX-UNKNOWN-EMPTY")
        self.assertEqual(state, "UNKNOWN")
        self.assertEqual((r["verdict"], r["bucket"]), ("證據不足", "Needs Review"))

    def test_missing_brief_needs_review(self):
        r, state = gated("FIX-NEW-MATCH", brief=None)
        self.assertEqual(r["bucket"], "Needs Review")
        self.assertIn("brief", r["reason"])


class TestVerdictCoverage(unittest.TestCase):
    def test_clear_insufficient_needs_review(self):
        # Required case: CLEAR must still be able to land in Needs Review.
        r, state = gated("FIX-CLEAR-INSUFFICIENT")
        self.assertEqual(state, "CLEAR")
        self.assertEqual((r["verdict"], r["bucket"]), ("證據不足", "Needs Review"))

    def test_conflict_needs_review(self):
        r, state = gated("FIX-CONFLICT-RELEVANT")
        self.assertEqual(state, "CONFLICT")
        self.assertEqual(r["bucket"], "Needs Review")

    def test_constraint_mismatch_remaining(self):
        r, state = gated("FIX-NEW-PEOPLE-MISMATCH")
        self.assertEqual(state, "NEW")
        self.assertEqual((r["verdict"], r["bucket"]), ("明確不符", "Remaining"))

    def test_resolver_defaults_unassigned(self):
        # brief-v1 only defines resolvers.scene; constraint/evidence keys
        # must fall back to 未指定, never guessed.
        r, _ = gated("FIX-NEW-PEOPLE-MISMATCH")
        self.assertEqual(r["resolver"], "未指定")
        r2, _ = gated("FIX-CLEAR-INSUFFICIENT")
        self.assertEqual(r2["resolver"], "未指定")
        r3, _ = gated("FIX-NEW-MATCH")
        self.assertEqual(r3["resolver"], "編輯")


class TestPipelineCounts(unittest.TestCase):
    def test_summary_generated_not_hardcoded(self):
        results = run(BRIEF, OBS)
        s = results["summary"]
        self.assertEqual(s["total"], len(OBS))
        self.assertEqual(s["Shortlist"] + s["Needs Review"] + s["Remaining"],
                         s["total"])
        self.assertNotEqual((s["Shortlist"], s["Needs Review"], s["Remaining"]),
                            (18, 7, 375))
        self.assertEqual(results["model_calls"], 0)

    def test_preview_inlines_computed_counts(self):
        results = run(BRIEF, OBS)
        dest = ROOT / "outputs" / "test-preview.html"
        try:
            emit_preview(results, dest)
            text = dest.read_text(encoding="utf-8")
            s = results["summary"]
            self.assertIn("Shortlist {}".format(s["Shortlist"]), text)
            self.assertIn("Needs Review {}".format(s["Needs Review"]), text)
            self.assertIn("Remaining {}".format(s["Remaining"]), text)
            self.assertNotIn("18", text.split("Total")[0][-80:] if "Total" in text else "")
        finally:
            if dest.exists():
                dest.unlink()


if __name__ == "__main__":
    unittest.main()
