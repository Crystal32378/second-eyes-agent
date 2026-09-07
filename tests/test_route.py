"""Rerunnable routing contract tests — no model calls, no network.

Run:  python3 -m unittest discover -s tests -v   (from repo root)

Covers the THREE routing states plus degenerate inputs (which fold into
UNKNOWN), closed-vocab enforcement, and the evidence_ref requirement:
a legal token WITHOUT a verifiable ref is discarded.
"""
import unittest

from agent.loop import route


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

    def test_unknown_old_prose_non_comparable(self):
        self.assertEqual(
            route({"observed": obs(colour="beige"),
                   "old": {"colour": "很有故事感"}}),
            "UNKNOWN")

    def test_unknown_no_common_field(self):
        # Gate-blocking case: disjoint fields must NOT clear.
        self.assertEqual(
            route({"observed": obs(item="dress"),
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


if __name__ == "__main__":
    unittest.main()
