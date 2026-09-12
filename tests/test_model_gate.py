"""Model-gate guard tests — no model calls, no credentials needed.

All guards under test trigger before any model object is built:
wrong count and video entries must stop with exit 2.
"""
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import runtime.run_smallset_gemini as gate_mod
from runtime.run_smallset_gemini import main

ROOT = Path(__file__).resolve().parents[1]


def tmp_manifest(d, keys, suffix=".jpg"):
    photos = []
    for k in keys:
        f = Path(d) / "{}{}".format(k, suffix)
        f.write_bytes(b"gate-bytes-" + k.encode())
        sha = hashlib.sha256(f.read_bytes()).hexdigest()
        photos.append({"asset_key": k, "path": str(f), "sha256": sha,
                       "old_label": "none"})
    doc = {"brief": "briefs/brief-v1.json",
           "ref_convention": "workroom:frame-full", "photos": photos}
    mp = os.path.join(d, "manifest.json")
    Path(mp).write_text(json.dumps(doc), encoding="utf-8")
    return mp


def run_main(*argv):
    with patch.object(sys, "argv", ["run_smallset_gemini.py"] + list(argv)):
        return main()


class TestModelGateGuards(unittest.TestCase):
    def test_count_guard(self):
        with tempfile.TemporaryDirectory() as d:
            mp = tmp_manifest(d, ["ONLY-ONE"])
            out = os.path.join(d, "out.json")
            with patch.object(gate_mod, "MANIFEST_PATH", Path(mp)):
                rc = run_main("--out", out)
            self.assertEqual(rc, 2)
            self.assertFalse(os.path.exists(out))

    def test_video_prescan(self):
        with tempfile.TemporaryDirectory() as d:
            keys = ["V-{:02d}".format(i) for i in range(6)]
            mp = tmp_manifest(d, keys, suffix=".mp4")
            out = os.path.join(d, "out.json")
            with patch.object(gate_mod, "MANIFEST_PATH", Path(mp)):
                rc = run_main("--out", out)
            self.assertEqual(rc, 2)
            self.assertFalse(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
