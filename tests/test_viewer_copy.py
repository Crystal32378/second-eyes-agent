"""Viewer copy + responsive-rule tests.

The runtime page is a static viewer over a recorded run. It may not imply a
callable runtime ("live"), and "verified" may not stand alone — what was
verified is custody (manifest SHA), not accuracy. The 390px rule is asserted
here so a CSS edit cannot silently bring the overflow back; the rendered
scrollWidth === clientWidth check is run in the browser QA pass.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "ui/runtime"
WORKROOM = ROOT / "ui/workroom"


class TestViewerCopy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (RUNTIME / "index.html").read_text(encoding="utf-8")
        cls.results = (RUNTIME / "results.json").read_text(encoding="utf-8")

    def test_no_live_runtime_claim(self):
        blob = (self.html + self.results).lower()
        for banned in ("live small-set runtime", "live decisions",
                       "live runtime", "real-time", "realtime"):
            self.assertNotIn(banned, blob, banned)
        # "verified" must never stand alone as an asset property.
        self.assertIsNone(re.search(r"\d+\s+verified assets", blob))

    def test_precise_banner(self):
        self.assertIn("RECORDED SMALL-SET RUN · 6 CUSTODY-VERIFIED ASSETS · "
                      "COUNTS COMPUTED FROM SEALED RESULTS", self.html)

    def test_states_it_is_a_static_viewer(self):
        low = self.html.lower()
        self.assertIn("static viewer", low)
        self.assertIn("nothing here calls a model", low)
        self.assertIn("sha-sealed", low)

    def test_error_message_points_at_a_real_doc(self):
        refs = re.findall(r"docs/[a-z0-9-]+\.md", self.html)
        self.assertTrue(refs, "viewer cites no doc")
        for ref in refs:
            self.assertTrue((ROOT / ref).is_file(), ref)

    def test_standing_disclaimers_survive(self):
        low = (self.html + self.results).lower()
        self.assertIn("candidate, not clearance", low)
        self.assertIn("no ranking", low)
        self.assertIn("not guessed", low)

    def test_preview_nav_wraps_on_small_screens(self):
        """390px fix: the 3-link preview bar must wrap, not overflow."""
        css = (WORKROOM / "styles.css").read_text(encoding="utf-8")
        small = css.split("@media(max-width:520px){")[1].split("}@media")[0]
        self.assertIn(".preview-bar nav{flex-wrap:wrap", small)
        self.assertIn("white-space:normal", small)
        # Runtime and workroom must keep sharing one stylesheet.
        self.assertEqual((RUNTIME / "styles.css").read_bytes(),
                         (WORKROOM / "styles.css").read_bytes())

    def test_gloss_is_display_only(self):
        """Sealed tokens stay verbatim in JSON; English reading is on screen."""
        import json
        payload = json.loads(self.results)
        values = [v["value"] for it in payload["items"]
                  for v in (it["observed"] or {}).values() if v]
        self.assertIn("藍", values, "sealed token was rewritten in the payload")
        self.assertNotIn("blue [", self.results)
        self.assertNotIn("[blue]", self.results)
        # The gloss lives only in the viewer, and is labelled as verbatim.
        self.assertIn("const GLOSS", self.html)
        self.assertIn('"藍": "blue"', self.html)
        self.assertIn("Observed (verbatim):", self.html)
        self.assertIn("DISPLAY-ONLY", self.html)

    def test_workroom_nav_matches_viewer_wording(self):
        for page in ("brief-established.html", "brief-missing.html"):
            text = (WORKROOM / page).read_text(encoding="utf-8")
            self.assertIn("03 View recorded 6-image run", text)
            self.assertNotIn("verified 6-image runtime", text)

    def test_mock_counts_still_separate(self):
        self.assertIn("18 / 7 / 375", self.html)
        self.assertIn("never combined", self.html)


if __name__ == "__main__":
    unittest.main()
