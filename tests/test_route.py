"""Rerunnable routing + logging contract tests — no model calls, no network.

Run:  python3 -m unittest discover -s tests -v   (from repo root)

Routing: FOUR states (CLEAR/CONFLICT/UNKNOWN/NEW). Degenerate inputs fold
into UNKNOWN. Closed vocab is FROZEN (see runtime/vocab.py): model side is
exact token + mandatory evidence_ref; old/path side is substring scan
(CJK-safe). Logging: ref-less observations are rejected before write.
"""
import unittest

from agent.loop import route
from runtime.logging import validate_record


def obs(**fields):
    """Helper: every observed value carries a staged evidence ref."""
    return {k: ({"value": v, "ref": "frame:full"} if v is not None else None)
            for k, v in fields.items()}


class TestRoute(unittest.TestCase):
    def test_clear_confirmed(self):
        self.assertEqual(
            route({"observed": obs(colour="beige"),
                   "old": {"colour": "beige"}}),
            "CLEAR")

    def test_conflict_closed_vocab_clash(self):
        self.assertEqual(
            route({"observed": obs(colour="beige"),
                   "old": {"colour": "red"}}),
            "CONFLICT")

    def test_new_old_prose_non_comparable(self):
        # Old label says nothing comparable -> record, don't ask.
        self.assertEqual(
            route({"observed": obs(colour="beige"),
                   "old": {"colour": "很有故事感"}}),
            "NEW")

    def test_new_no_old_label(self):
        self.assertEqual(
            route({"observed": obs(item="bra"),
                   "old": {}}),
            "NEW")

    def test_unknown_no_common_field(self):
        # Disjoint fields must NOT clear (both sides valid, nothing shared).
        self.assertEqual(
            route({"observed": obs(item="bra"),
                   "old": {"colour": "red"}}),
            "UNKNOWN")

    def test_unknown_nothing_observed(self):
        self.assertEqual(
            route({"observed": {}, "old": {"colour": "red"}}),
            "UNKNOWN")

    def test_unknown_out_of_vocab_observed(self):
        self.assertEqual(
            route({"observed": obs(colour="purple-ish"),
                   "old": {"colour": "red"}}),
            "UNKNOWN")

    def test_unknown_legal_token_without_ref(self):
        # Closed vocab alone proves nothing: no ref -> discarded -> UNKNOWN.
        self.assertEqual(
            route({"observed": {"colour": {"value": "beige", "ref": ""}},
                   "old": {"colour": "beige"}}),
            "UNKNOWN")

    def test_cjk_substring_old_side(self):
        # 中文沒有詞邊界: path text must match by substring.
        self.assertEqual(
            route({"observed": obs(colour="膚"),
                   "old": {"colour": "柔魅膚_3.jpg"}}),
            "CLEAR")
        self.assertEqual(
            route({"observed": obs(item="bra"),
                   "old": {"item": "偷心密探 Sheer Bra"}}),
            "CLEAR")

    def test_longest_token_wins(self):
        # "Bralette" contains "bra" — most specific token must win.
        from runtime.vocab import scan_old
        self.assertEqual(scan_old("item", "NUDE Fashion Bralette"), "bralette")


class TestLogging(unittest.TestCase):
    def _record(self, decision="NEW"):
        return {
            "asset_key": "2013 FW/x.jpg",
            "kind": "image",
            "tool_calls": ["inspect_asset", "get_existing_info"],
            "decision": decision,
            "model": "amazon.nova-lite-v1:0",
            "timestamps": {"started": "t0", "finished": "t1"},
            "evidence": {"observed": {
                "colour": {"value": "beige", "ref": "frame:full"}}},
        }

    def test_valid_record_passes_with_queue_flag(self):
        r = validate_record(self._record("NEW"))
        self.assertEqual(r["human_queue"], False)
        r = validate_record(self._record("CONFLICT"))
        self.assertEqual(r["human_queue"], True)

    def test_refless_observation_rejected(self):
        r = self._record()
        r["evidence"]["observed"]["colour"] = {"value": "beige", "ref": ""}
        with self.assertRaises(ValueError):
            validate_record(r)


if __name__ == "__main__":
    unittest.main()
