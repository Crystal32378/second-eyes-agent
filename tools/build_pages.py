#!/usr/bin/env python3
"""Stage the GitHub Pages artifact — workroom at root, runtime at /runtime/.

The repo keeps the two pages as siblings (`ui/workroom/`, `ui/runtime/`) so
they cross-link with `../`. The published site keeps the workroom at the
existing root URL, which puts the two at DIFFERENT depths, so the handful of
cross-links are rewritten here — mechanically, from an explicit table. An
`../` reference that is not in the table stops the build rather than shipping
a link that would 404 only in production.

After staging, every local href/src in the artifact is resolved against the
staged tree; anything that does not land on a real file stops the build.

Usage (from repo root):
  python3 tools/build_pages.py --out _site
  python3 tools/build_pages.py --out _site --print-manifest
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
WORKROOM = ROOT / "ui/workroom"
RUNTIME = ROOT / "ui/runtime"

# Explicit, reviewable rewrite table: (staged file, from, to).
# Repo layout  ui/workroom/x.html -> ../runtime/     (sibling)
# Site layout  /x.html            -> runtime/        (child)
LINK_REWRITES = {
    "brief-established.html": [('href="../runtime/"', 'href="runtime/"')],
    "brief-missing.html": [('href="../runtime/"', 'href="runtime/"')],
    "runtime/index.html": [
        ('href="../workroom/brief-established.html"',
         'href="../brief-established.html"'),
    ],
}

LOCAL_REF = re.compile(r'(?:href|src)="([^"#][^"]*)"')
META_REFRESH = re.compile(r'content="\s*\d+\s*;\s*url=([^"]+)"', re.I)
# Files the viewer fetches at runtime: not an href/src, so named explicitly.
FETCHED = ("runtime/results.json",)


def fail(msg: str) -> int:
    print("PAGES BUILD STOP: {}".format(msg))
    return 2


def stage(out: Path) -> int:
    if not WORKROOM.is_dir():
        return fail("missing {}".format(WORKROOM))
    if not RUNTIME.is_dir():
        return fail("missing {}".format(RUNTIME))
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(WORKROOM, out)
    shutil.copytree(RUNTIME, out / "runtime")

    for rel, rewrites in LINK_REWRITES.items():
        f = out / rel
        if not f.is_file():
            return fail("rewrite target missing: {}".format(rel))
        text = f.read_text(encoding="utf-8")
        for old, new in rewrites:
            hits = text.count(old)
            if hits < 1:
                return fail("{}: rewrite {!r} matched nothing — the page "
                            "changed, re-check LINK_REWRITES".format(rel, old))
            text = text.replace(old, new)
            print("  rewrote {} x{} in {}".format(old, hits, rel))
        f.write_text(text, encoding="utf-8")
    return 0


def check_links(out: Path) -> list:
    """Every local href/src must resolve to a file inside the artifact."""
    errors = []
    for page in sorted(out.rglob("*.html")):
        rel = page.relative_to(out)
        text = page.read_text(encoding="utf-8")
        for ref in LOCAL_REF.findall(text) + META_REFRESH.findall(text):
            parsed = urlparse(ref)
            if parsed.scheme or parsed.netloc or ref.startswith("//"):
                continue  # external, not ours to resolve
            target = unquote(parsed.path)
            if not target:
                continue
            if target.startswith("/"):
                errors.append("{}: absolute path {!r} breaks on a project "
                              "Pages sub-path".format(rel, ref))
                continue
            dest = (page.parent / target).resolve()
            if dest.is_dir():
                dest = dest / "index.html"
            try:
                dest.relative_to(out.resolve())
            except ValueError:
                errors.append("{}: {!r} escapes the artifact root".format(
                    rel, ref))
                continue
            if not dest.is_file():
                errors.append("{}: {!r} -> {} (missing)".format(
                    rel, ref, dest.relative_to(out.resolve())))
    # The site must answer at its root.
    if not (out / "index.html").is_file():
        errors.append("artifact root has no index.html")
    if not (out / "runtime/index.html").is_file():
        errors.append("artifact has no runtime/index.html")
    for rel in FETCHED:
        if not (out / rel).is_file():
            errors.append("fetched-at-runtime file missing: {}".format(rel))
    return errors


def manifest(out: Path) -> list:
    return sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_site")
    ap.add_argument("--print-manifest", action="store_true")
    args = ap.parse_args()
    out = (ROOT / args.out) if not Path(args.out).is_absolute() else Path(args.out)

    rc = stage(out)
    if rc:
        return rc
    errors = check_links(out)
    if errors:
        shutil.rmtree(out, ignore_errors=True)
        return fail("unresolved links:\n  - " + "\n  - ".join(errors))

    files = manifest(out)
    print("staged {} files to {}".format(len(files), out))
    print("root URL -> index.html; runtime -> runtime/index.html")
    if args.print_manifest:
        for f in files:
            print("  {}".format(f))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
