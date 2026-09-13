"""Captions are decoration; buckets, coverage and routing are evidence.

The viewer prints a human name beside each photograph, borrowed from the
workroom for the same byte-identical files. That name is display-only. These
tests hold the line structurally: the zone a photograph lands in comes from
its `bucket`, the coverage tiles come from `coverage.slots`, and the caption
table is reachable only from the two helpers that render text. If someone
later routes on a caption, these fail.

Fu's ruling, 2026-09-13: keep the captions, keep the asset key visible
beside them, and never let a caption participate in a gate, in coverage, or
in routing.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "ui/runtime"


class TestCaptionIsInert(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (RUNTIME / "index.html").read_text(encoding="utf-8")
        cls.script = cls.html.split("<script>")[1].split("</script>")[0]
        cls.payload = json.loads(
            (RUNTIME / "results.json").read_text(encoding="utf-8"))
        cls.keys = {i["asset_key"] for i in cls.payload["items"]}

    # ---- the table itself -------------------------------------------------

    def test_caption_table_is_declared_display_only(self):
        self.assertIn("const CAPTION", self.script)
        head = self.script.split("const CAPTION")[0]
        self.assertIn("DISPLAY-ONLY", head,
                      "the CAPTION table is not declared display-only")

    def test_no_phantom_captions(self):
        """Every caption names a photograph that is actually in the payload."""
        block = self.script.split("const CAPTION = {")[1].split("};")[0]
        captioned = set(re.findall(r'"([A-Z0-9-]+)":\s*\[', block))
        self.assertTrue(captioned, "no captions parsed")
        self.assertTrue(captioned <= self.keys,
                        "captions for assets not in results.json: {}".format(
                            sorted(captioned - self.keys)))

    def test_unknown_key_falls_back_to_the_key(self):
        """An uncaptioned photograph shows its key, never a blank or a guess."""
        self.assertIn("(CAPTION[k] || [k, k])[0]", self.script)
        self.assertIn("(CAPTION[k] || [k, k])[1]", self.script)

    def test_caption_is_only_reachable_through_the_text_helpers(self):
        """CAPTION is read in two places, both of which return a string."""
        uses = [m.start() for m in re.finditer(r"\bCAPTION\b", self.script)]
        self.assertEqual(len(uses), 3,
                         "CAPTION should appear exactly 3 times "
                         "(declaration + caption() + alt()), found {}".format(
                             len(uses)))
        for expr in ("const caption = k => (CAPTION[k] || [k, k])[0]",
                     "const alt = k => (CAPTION[k] || [k, k])[1]"):
            self.assertIn(expr, self.script)

    # ---- what actually decides placement ----------------------------------

    def test_zone_assignment_reads_bucket_only(self):
        """The only thing that sorts photographs into zones is `bucket`."""
        self.assertIn("const by = b => d.items.filter(i => i.bucket === b);",
                      self.script)
        for zone in ('by("Shortlist")', 'by("Needs Review")',
                     'by("Remaining")'):
            self.assertIn(zone, self.script, zone)

    def test_coverage_reads_the_payload_slots_only(self):
        self.assertIn("d.coverage.slots.forEach", self.script)
        self.assertIn('c.status === "MISSING"', self.script)
        self.assertIn('c.status === "HAVE"', self.script)
        # Slot membership comes from the payload, not from any caption.
        self.assertIn("c.members.forEach(m => { slotOf[m] =", self.script)

    def test_no_caption_in_any_decision_expression(self):
        """No line that decides a bucket, a slot or a count may call caption()."""
        decisive = ("bucket", "coverage", "slots", "status", "summary",
                    "filter(", "slotOf")
        for line in self.script.splitlines():
            if "caption(" in line or "CAPTION" in line or "alt(" in line:
                for word in decisive:
                    self.assertNotIn(
                        word, line,
                        "caption used in a decision expression: {!r}".format(
                            line.strip()))

    def test_counts_come_from_summary_not_from_captions(self):
        for field in ('s["Shortlist"]', 's["Needs Review"]', 's["Remaining"]',
                      's["total"]'):
            self.assertIn(field, self.script, field)
        # The rendered numbers are the payload's numbers.
        self.assertEqual(self.payload["summary"],
                         {"Shortlist": 1, "Needs Review": 2, "Remaining": 3,
                          "total": 6})

    # ---- the key stays visible -------------------------------------------

    def test_asset_key_is_rendered_beside_every_caption(self):
        """A caption never travels alone: the key is printed next to it."""
        pairs = re.findall(
            r'line\.append\(el\("h3", null, caption\(it\.asset_key\)\),\s*'
            r'el\("span", "asset-code", it\.asset_key\)\);', self.script)
        self.assertEqual(len(pairs), 2,
                         "caption and asset key are not emitted together in "
                         "both card layouts")
        # The review desk prints the key explicitly too.
        self.assertIn('el("strong", null, "Photograph: ")', self.script)

    def test_asset_key_visible_at_every_width(self):
        """Subdued on small screens (Fu's ruling), never display:none."""
        self.assertIn(".asset-code{display:inline!important}", self.html)
        small = self.html.split("@media(max-width:1100px){")[1].split("}")[0]
        self.assertIn(".asset-code{", small)
        self.assertIn("color:var(--muted)", small)
        self.assertNotIn("display:none", small)

    # ---- the line we are not crossing yet ---------------------------------

    def test_no_resolver_and_no_invented_owner(self):
        """No `Ask:` line until resolver is a sourced, public publishing fact."""
        blob = self.html + json.dumps(self.payload, ensure_ascii=False)
        self.assertNotIn("Ask:", blob)
        self.assertNotIn("resolver", blob)
        self.assertIn('el("strong", null, "Needed: ")', self.script)


if __name__ == "__main__":
    unittest.main()
