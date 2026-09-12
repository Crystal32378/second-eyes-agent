"""Export lineage counter-tests — a tampered local MVP must never publish.

outputs/local-mvp.json is git-ignored and locally editable, so it is not
evidence. The exporter recomputes the local MVP from the SHA-sealed
model-gate input and refuses to publish when the on-disk file disagrees.
These tests tamper with the file the three ways that would change what the
public page says (summary counts, a bucket, coverage) and assert both
halves of the contract: EXPORT STOP, and not one byte written to
ui/runtime/.
"""
import hashlib
import json
import os
import shutil
import unittest
from pathlib import Path
from unittest import mock

from tests.support import ROOT, ensure_local_mvp

RUNTIME = ROOT / "ui/runtime"
LOCAL_MVP = ROOT / "outputs/local-mvp.json"


def snapshot(d: Path) -> dict:
    """Path -> sha256 for every file under d (detects partial writes)."""
    return {str(p.relative_to(d)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(d.rglob("*")) if p.is_file()}


class TestExportLineage(unittest.TestCase):
    def setUp(self):
        from runtime.export_public import main
        self.main = main
        ensure_local_mvp()
        self.backup = LOCAL_MVP.read_bytes()
        self.assertEqual(self.main(), 0, "clean export must succeed first")
        self.before = snapshot(RUNTIME)

    def tearDown(self):
        LOCAL_MVP.write_bytes(self.backup)
        self.main()

    def assert_stopped_clean(self, label):
        rc = self.main()
        self.assertEqual(rc, 2, "{}: export must STOP".format(label))
        self.assertEqual(snapshot(RUNTIME), self.before,
                         "{}: ui/runtime changed on a stopped export".format(
                             label))
        stray = [p.name for p in RUNTIME.parent.iterdir()
                 if p.name.startswith(".runtime-stage-")]
        self.assertEqual(stray, [], "{}: staging dir left behind".format(label))

    def tamper(self, mutate):
        doc = json.loads(LOCAL_MVP.read_text(encoding="utf-8"))
        mutate(doc)
        LOCAL_MVP.write_text(json.dumps(doc, ensure_ascii=False, indent=2),
                             encoding="utf-8")

    def test_tampered_summary_stops(self):
        def m(d):
            d["summary"]["Shortlist"] = 99
            d["summary"]["Remaining"] = 0
        self.tamper(m)
        self.assert_stopped_clean("summary")

    def test_tampered_bucket_stops(self):
        def m(d):
            for it in d["items"]:
                if it["bucket"] != "Shortlist":
                    it["bucket"] = "Shortlist"
                    return
            raise AssertionError("no non-Shortlist item to tamper with")
        self.tamper(m)
        self.assert_stopped_clean("bucket")

    def test_tampered_coverage_stops(self):
        def m(d):
            slot = d["coverage"]["slots"][0]
            slot["status"] = "HAVE" if slot["status"] == "MISSING" else "MISSING"
            slot["members"] = ["FABRICATED-0001"]
            slot["count"] = 1
        self.tamper(m)
        self.assert_stopped_clean("coverage")

    def test_tampered_verdict_stops(self):
        self.tamper(lambda d: d["items"][0].__setitem__("verdict", "符合"))
        self.assert_stopped_clean("verdict")

    def test_tampered_public_ready_stops(self):
        self.tamper(lambda d: d["summary"].__setitem__("public_ready", False))
        self.assert_stopped_clean("public_ready")

    def test_unreadable_local_mvp_stops(self):
        LOCAL_MVP.write_text("{ not json", encoding="utf-8")
        self.assert_stopped_clean("corrupt json")

    def test_export_survives_missing_local_mvp(self):
        """The file is advisory: absent it, the sealed recompute still rules."""
        LOCAL_MVP.unlink()
        self.assertEqual(self.main(), 0)
        self.assertEqual(snapshot(RUNTIME), self.before,
                         "recompute-only export must be byte-identical")

    def test_published_payload_equals_recompute(self):
        from runtime.local_mvp import run as local_mvp_run
        recomputed, err = local_mvp_run()
        self.assertIsNone(err)
        public = json.loads((RUNTIME / "results.json").read_text(
            encoding="utf-8"))
        self.assertEqual(public["summary"], {
            k: recomputed["summary"][k]
            for k in ("Shortlist", "Needs Review", "Remaining", "total")})
        self.assertEqual(public["coverage"], recomputed["coverage"])
        self.assertEqual(public["sealed_sha256"], recomputed["sealed_sha256"])
        self.assertEqual([i["asset_key"] for i in public["items"]],
                         [i["asset_key"] for i in recomputed["items"]])
        for pub, rec in zip(public["items"], recomputed["items"]):
            self.assertEqual(pub["bucket"], rec["bucket"], pub["asset_key"])
            self.assertEqual(pub["evidence_state"], rec["evidence_state"],
                             pub["asset_key"])


class TestCommitAtomicity(unittest.TestCase):
    """A commit-phase I/O failure must leave the OLD bundle byte-identical.

    The interesting case is not a clean re-export of the same bytes: it is a
    DIFFERENT old bundle on disk when the swap fails. So each test first
    plants a legal-but-different previous bundle, then injects a failure at
    the exact step being tested, and asserts every planted byte is still
    there afterwards.
    """

    def setUp(self):
        from runtime import export_public
        self.mod = export_public
        ensure_local_mvp()
        self.assertEqual(self.mod.main(), 0)
        self.real = snapshot(RUNTIME)

    def tearDown(self):
        self.mod.main()
        self.assertEqual(snapshot(RUNTIME), self.real)

    def plant_old_bundle(self):
        """Make the published bundle differ from what the export produces."""
        marker = (RUNTIME / "results.json")
        doc = json.loads(marker.read_text(encoding="utf-8"))
        doc["page"] = "PREVIOUS BUNDLE — must survive a failed commit"
        marker.write_text(json.dumps(doc, ensure_ascii=False, indent=2),
                          encoding="utf-8")
        (RUNTIME / "styles.css").write_text(
            "/* previous stylesheet */\n", encoding="utf-8")
        (RUNTIME / "assets" / "PREVIOUS-ONLY.jpg").write_bytes(b"old asset")
        planted = snapshot(RUNTIME)
        self.assertNotEqual(planted, self.real, "plant did not change anything")
        return planted

    def residue(self):
        return sorted(p.name for p in RUNTIME.parent.iterdir()
                      if p.name.startswith(".runtime-stage-")
                      or p.name.startswith("runtime.backup-"))

    def test_failure_moving_new_bundle_in_rolls_back(self):
        planted = self.plant_old_bundle()
        real_rename, calls = os.rename, []

        def flaky(src, dst):
            calls.append((src, dst))
            if len(calls) == 1:            # old bundle moved aside: allow
                return real_rename(src, dst)
            if len(calls) == 2:            # new bundle moving in: fail
                raise OSError(28, "injected: no space left on device")
            return real_rename(src, dst)   # rollback: allow

        with mock.patch.object(self.mod, "_rename", flaky):
            rc = self.mod.main()
        self.assertEqual(rc, 2, "a failed commit must STOP")
        self.assertEqual(len(calls), 3, "rollback rename was not attempted")
        self.assertEqual(snapshot(RUNTIME), planted,
                         "old bundle was not restored byte-for-byte")
        self.assertEqual(self.residue(), [], "staging/backup left behind")

    def test_failure_moving_old_bundle_aside_changes_nothing(self):
        planted = self.plant_old_bundle()

        def refuse(src, dst):
            raise OSError(13, "injected: permission denied")

        with mock.patch.object(self.mod, "_rename", refuse):
            rc = self.mod.main()
        self.assertEqual(rc, 2)
        self.assertEqual(snapshot(RUNTIME), planted)
        self.assertEqual(self.residue(), [])

    def test_no_mixed_bundle_is_ever_visible(self):
        """The published dir is all-old or all-new — never half of each."""
        planted = self.plant_old_bundle()
        real_rename, calls = os.rename, []

        def flaky(src, dst):
            calls.append(1)
            if len(calls) == 2:
                raise OSError(5, "injected: I/O error")
            return real_rename(src, dst)

        with mock.patch.object(self.mod, "_rename", flaky):
            self.mod.main()
        after = snapshot(RUNTIME)
        # Every planted file is present and unchanged; no new-bundle file
        # sneaked in beside them.
        self.assertEqual(after, planted)
        self.assertIn("assets/PREVIOUS-ONLY.jpg", after)
        self.assertIn("previous stylesheet",
                      (RUNTIME / "styles.css").read_text(encoding="utf-8"))

    def test_successful_commit_replaces_the_whole_bundle(self):
        planted = self.plant_old_bundle()
        self.assertEqual(self.mod.main(), 0)
        after = snapshot(RUNTIME)
        self.assertEqual(after, self.real, "commit did not fully replace")
        self.assertNotIn("assets/PREVIOUS-ONLY.jpg", after,
                         "stale asset survived the swap")
        self.assertEqual(self.residue(), [])


if __name__ == "__main__":
    unittest.main()
