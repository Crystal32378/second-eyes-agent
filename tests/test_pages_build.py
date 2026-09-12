"""Pages artifact tests — the published layout must resolve, not just exist.

The repo keeps workroom and runtime as siblings; the site keeps the workroom
at the existing root URL and puts the runtime viewer at /runtime/. That is a
depth change, so every cross-link is rewritten at build time. These tests
build the artifact into a temp dir and assert the layout, the rewrites, and
that no local link points at a file the artifact does not contain.
"""
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestPagesBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tools.build_pages import stage, check_links, manifest
        cls.stage, cls.check_links, cls.manifest_fn = (
            staticmethod(stage), staticmethod(check_links),
            staticmethod(manifest))
        cls.tmp = Path(tempfile.mkdtemp(prefix="pages-test-"))
        cls.out = cls.tmp / "_site"
        assert stage(cls.out) == 0
        cls.files = manifest(cls.out)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_workroom_at_root_runtime_under_runtime(self):
        for rel in ("index.html", "brief-established.html",
                    "brief-missing.html", "styles.css",
                    "runtime/index.html", "runtime/results.json",
                    "runtime/styles.css"):
            self.assertIn(rel, self.files, rel)
        # Existing root URL keeps working: root index redirects into the
        # workroom, exactly as before this change.
        root = (self.out / "index.html").read_text(encoding="utf-8")
        self.assertIn("brief-established.html", root)
        # No nested ui/ or workroom/ prefix leaked into the artifact.
        self.assertFalse([f for f in self.files if f.startswith("workroom/")])
        self.assertFalse([f for f in self.files if f.startswith("ui/")])

    def test_all_six_runtime_assets_present(self):
        assets = [f for f in self.files if f.startswith("runtime/assets/")]
        self.assertEqual(len(assets), 6, assets)

    def test_cross_links_rewritten_for_site_depth(self):
        for page in ("brief-established.html", "brief-missing.html"):
            text = (self.out / page).read_text(encoding="utf-8")
            self.assertIn('href="runtime/"', text)
            self.assertNotIn('href="../runtime/"', text)
        runtime = (self.out / "runtime/index.html").read_text(encoding="utf-8")
        self.assertIn('href="../brief-established.html"', runtime)
        self.assertNotIn('href="../workroom/', runtime)

    def test_every_local_link_resolves(self):
        self.assertEqual(self.check_links(self.out), [])

    def test_link_checker_catches_a_broken_link(self):
        """The checker must fail on a bad link, not pass vacuously."""
        tmp = Path(tempfile.mkdtemp(prefix="pages-neg-"))
        try:
            out = tmp / "_site"
            self.assertEqual(self.stage(out), 0)
            page = out / "brief-established.html"
            page.write_text(page.read_text(encoding="utf-8").replace(
                'href="runtime/"', 'href="runtime-typo/"'), encoding="utf-8")
            errors = self.check_links(out)
            self.assertTrue(errors)
            self.assertIn("runtime-typo", " ".join(errors))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_workflow_triggers_on_runtime_changes(self):
        wf = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
        for path in ('"ui/workroom/**"', '"ui/runtime/**"',
                     '"tools/build_pages.py"'):
            self.assertIn(path, wf, path)
        self.assertIn("tools/build_pages.py --out _site", wf)
        self.assertIn("path: _site", wf)
        self.assertNotIn("path: ui/workroom", wf)


if __name__ == "__main__":
    unittest.main()
