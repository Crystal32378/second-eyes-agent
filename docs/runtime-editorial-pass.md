# Runtime viewer — editorial integration pass

Branch `ui/runtime-editorial`. Presentation only. Not merged, not deployed.

## What changed

Only `ui/runtime/index.html`. The page now uses the workroom's own design
system and information architecture instead of a grid of engineering cards.

| | before (deployed `main`) | after (this branch) |
|---|---|---|
| layout | one flat `auto-fill` grid, six equal cards | `workwall`: shortlist wall + review desk aside, quiet shelf below |
| first visual layer | state tag and trace string | photograph, then the reason it landed there |
| shortlist | equal card | one larger card, laid out as a spread on wide screens |
| needs review | equal cards in the same grid | the workroom's `question` desk on the right |
| remaining | equal cards | a quieter shelf under the wall |
| SHA / refs / sources / observed | printed on every card | one `Evidence details` disclosure per card |
| coverage | a sentence | the workroom's coverage tiles, MISSING keeps the `gap` mark |

Nothing else in the repo was touched: `results.json`, the exporter, the
atomic bundle, Pages packaging, the replay input, the sealed lineage and
every existing test contract are unchanged.

## What is still read from results.json

Every number and every placement. The page hardcodes no count, no bucket and
no coverage slot:

- `summary` -> the three zone numbers and the standfirst
- `bucket` -> which zone a photograph is rendered in
- `coverage.slots` -> the coverage tiles, the `HAVE` members, the MISSING
  note, and the candidate slot label on the shortlist card
- `reason`, `pending`, `observed`, `signal_sources`, `manifest.sha256`,
  `evidence_state`, `verdict` -> card copy and the evidence disclosure
- `brief_id`, `sealed_sha256` -> the run facts strip

Recorded run: Shortlist 1 / Needs Review 2 / Remaining 3. Coverage:
hero / product HAVE (ROBE-5059); detail / detail MISSING, not guessed.

## Two display-only tables, both declared in the page

- `GLOSS` — an English reading beside a bilingual observed token
  (`colour=藍 [blue]`). The payload keeps `藍` verbatim; tests assert both
  directions.
- `CAPTION` — the workroom's own names for the same six files (byte-identical
  copies, same SHAs), plus their alt text. They are captions, never identity:
  the asset key is printed beside every caption and is what the evidence
  binds to. An unlisted key falls back to showing its key.

Neither table touches `results.json` or any exported file.

## One deliberate divergence from the workroom stylesheet

The workroom hides `.asset-code` below 1100px. The runtime page overrides
that: this is an evidence page, so a reader has to be able to tie the
photograph on screen back to the lineage data, and the caption is a name we
wrote rather than identity. Per Fu's 2026-09-13 ruling the key is set
quieter on small screens (8px, muted, 75% opacity) rather than hidden. All
other CSS is the shared stylesheet, which stays byte-identical
(`test_stylesheet_identical`).

## Proof that captions are inert

`tests/test_caption_is_inert.py` (11 tests) holds the line structurally:
`CAPTION` is reachable from exactly two helpers that return a string; zones
come from `d.items.filter(i => i.bucket === b)`; coverage comes from
`d.coverage.slots`; no line that mentions a caption may also mention
`bucket`, `coverage`, `slots`, `status`, `summary`, `filter(` or `slotOf`;
no caption may name an asset absent from the payload; an uncaptioned key
falls back to showing the key; and the asset key is emitted beside the
caption in both card layouts.

Behavioural check, run in a browser against the staged artifact: every
caption was replaced with a deliberately wrong, rotated one
(`"BACK-5F20": ["WRONG CAPTION FOR IG-262", ...]`) and the page re-rendered.
Shortlist / Needs Review / Remaining membership, the three counts, both
coverage tiles and the standfirst came back **identical**. Captions move
nothing.

(The first version of that probe scraped asset keys out of the cards' free
text, so the wrong captions matched its own regex and it reported a false
failure. It now reads the `Photograph:` field. Worth recording: a check can
be vacuously red as easily as vacuously green.)

## Not added, on purpose

- No ranking, score, hero winner or ordering claim. Zones come from buckets.
- No `Ask:` line, confirmed by Fu's 2026-09-13 ruling. The workroom's review
  cards name who to ask; `resolver` is deliberately not in the public
  payload, so naming one here would be invented. The card says what is
  needed, not who owes it. When resolver becomes a sourced publishing fact
  supplied by an owner or editor, it can enter the public contract and the
  line can follow. `test_no_resolver_and_no_invented_owner` fails if either
  appears before then.
- No new runtime capability, no endpoint, no live language.

## Verification

Rendered by headless Chromium against the staged Pages artifact.

| page | 1440x900 | 390x844 |
|---|---|---|
| root | 1440 = 1440 | 390 = 390 |
| brief-established | 1440 = 1440 | 390 = 390 |
| brief-missing | 1440 = 1440 | 390 = 390 |
| runtime | 1440 = 1440 | 390 = 390 |

`documentElement.scrollWidth === clientWidth` everywhere, zero elements past
the viewport, zero console errors, 6/6 images loaded. Measured again with all
six `Evidence details` forced open: still no overflow at either width.

Full suite 125/125 PASS.

Screenshots: `docs/qa/editorial/`.

## Comparing the two

- Before (deployed `main`): https://crystal32378.github.io/second-eyes-agent/runtime/
- After (this branch), served locally:

```bash
python3 tools/build_pages.py --out _site
python3 -m http.server 8080 -d _site   # then /runtime/ and /brief-established.html
```

The workroom page is in the same artifact, so the two can be compared by
clicking between them exactly as a reader would.
