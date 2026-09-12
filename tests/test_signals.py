"""Signal declaration validation tests — no model calls."""
import json
import unittest
from pathlib import Path

from runtime.signals import validate_signals

ROOT = Path(__file__).resolve().parents[1]
KEYS = ["BACK-5F20", "IG-262", "IG-277", "IMG-4489", "ROBE-5059",
        "WEAR-8106"]


def entry(signals, sources):
    return {"signals": signals, "signal_sources": sources}


class TestValidateSignals(unittest.TestCase):
    def test_real_file_valid(self):
        doc = json.loads((ROOT / "fixtures/smallset/signals.json")
                         .read_text(encoding="utf-8"))
        rep = validate_signals(doc, KEYS)
        self.assertTrue(rep["ok"], rep["errors"])

    def test_long_edge_forbidden(self):
        doc = {"signals": {k: entry({"long_edge": 1400}, {}) for k in KEYS}}
        rep = validate_signals(doc, KEYS)
        self.assertFalse(rep["ok"])
        self.assertTrue(any("forbidden" in e for e in rep["errors"]))

    def test_nonbool_people_rejected(self):
        doc = {"signals": {
            k: entry({"has_people": ("yes" if k == "IG-262" else None)},
                     {"has_people": "x"} if k == "IG-262" else {})
            for k in KEYS}}
        rep = validate_signals(doc, KEYS)
        self.assertFalse(rep["ok"])
        self.assertTrue(any("has_people" in e for e in rep["errors"]))

    def test_declared_signal_without_source_rejected(self):
        doc = {"signals": {
            k: entry({"sku": "NUDE-01"}, {}) for k in KEYS}}
        rep = validate_signals(doc, KEYS)
        self.assertFalse(rep["ok"])
        self.assertTrue(any("strict source" in e for e in rep["errors"]))

    def test_key_mismatch_rejected(self):
        doc = {"signals": {"BACK-5F20": entry({}, {}),
                           "EXTRA": entry({}, {})}}
        rep = validate_signals(doc, KEYS)
        self.assertFalse(rep["ok"])
        self.assertTrue(any("missing signals" in e for e in rep["errors"]))
        self.assertTrue(any("not in sealed results" in e
                            for e in rep["errors"]))

    def test_signals_list_rejected_without_crash(self):
        doc = {"signals": {
            k: ({"signals": ["has_people"], "signal_sources": {}}
                if k == "IG-262" else entry({}, {})) for k in KEYS}}
        rep = validate_signals(doc, KEYS)
        self.assertFalse(rep["ok"])
        self.assertTrue(any("signals must be an object" in e
                            for e in rep["errors"]))

    def test_sources_string_rejected_without_crash(self):
        doc = {"signals": {
            k: ({"signals": {}, "signal_sources": "docs/x.md"}
                if k == "IG-262" else entry({}, {})) for k in KEYS}}
        rep = validate_signals(doc, KEYS)
        self.assertFalse(rep["ok"])
        self.assertTrue(any("signal_sources must be an object" in e
                            for e in rep["errors"]))


if __name__ == "__main__":
    unittest.main()
