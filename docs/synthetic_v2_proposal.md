# Synthetic v2 proposal — for Opus review BEFORE generating anything

Status: PROPOSAL ONLY. No fixtures generated, no runs, no vocab changes.
v1 corpus is sealed: its content/descriptions/expectations contradict each
other (subject-vs-background colour undefined), so v1 scores are VOID for
observation correctness. Plumbing-only conclusion stands.

## 1. The v1 error (sealed, not patched)

- CLEAR-01 claims "unambiguous subject" with old beige — but if the dark
  rectangle is the subject, the correct colour is black.
- CONFLICT-01 assumes observed=beige without defining background vs subject.
- UNKNOWN-01 is genuinely observable-as-black; demanding NONE was dishonest.
- Patching with "colour = subject colour" and re-running would silently
  invalidate existing expectations = tuning to answers. Hence v2 from scratch.

## 2. Definitions (frozen with the proposal, before any v2 pixels exist)

- **Subject**: the single central foreground shape. All colour/item
  observations refer to the SUBJECT ONLY. Background is explicitly out of
  scope and must never determine a selection.
- **Observable**: a field is observable iff the subject occupies a bounded,
  contiguous region covering >= ~10% of the frame AND its attribute is
  uniform across that region. Otherwise NONE.
- **Prompt change** (syn-obs-v2, locked pre-generation): the observation
  instruction names the subject explicitly —
  "Describe ONLY the single central foreground object. Ignore the background."
  Wording locked here; any later edit = syn-obs-v3 + full re-run.

## 3. Proposed v2 fixtures (6: 4 image + 2 video-shapes as images)

Video stays BLOCKED_UNSUPPORTED on the Gemini path; v2 videos are staged
as multi-frame image sequences ONLY IF the runner gains frame support —
otherwise v2 ships image-only and video waits for Nova. (Opus to rule.)

| id | subject | old label | expected | why unambiguous |
|----|---------|-----------|----------|-----------------|
| V2-CLEAR-01 | solid beige circle, 40% frame, gray bg | colour=beige | CLEAR | one subject, bg contrast, old matches |
| V2-CLEAR-02 | solid red triangle, 40% frame, gray bg | colour=red | CLEAR | same, exercises red path |
| V2-CONFLICT-01 | solid beige circle (same file as V2-CLEAR-01) | colour=red | CONFLICT | identical pixels, only old differs — isolates routing |
| V2-UNKNOWN-01 | uniform 50% gray, no bounded shape | (none) | UNKNOWN | no subject by definition → NONE/NONE/NONE |
| V2-NEW-01 | solid blue square, 40% frame, gray bg | (none) | NEW | observed + unlabelled → NEW per rules |
| V2-NEW-02 | same file as V2-NEW-01 | colour=blue | CLEAR | same pixels as NEW-01 + matching old → CLEAR; proves label, not pixels, flips the state |

Note V2-NEW-02/V2-CLEAR discipline: reusing one file across two cases is
declared upfront (tests the label's role, not hidden tuning).

## 4. Review checklist for Opus

- [ ] Subject/background split is airtight (no v1-style ambiguity)?
- [ ] 10% + uniformity threshold principled or arbitrary?
- [ ] Video: frame-sequences now, or image-only v2?
- [ ] UNKNOWN staged as featureless gray — can a model honestly return
      all-NONE, or does this repeat the UNKNOWN-01 trap?
- [ ] Anything here peeks at Batch A or evaluator data? (Must be: no.)

On PASS: generate fixtures → SHA-pin → lock prompt v2 → full fresh-agent
run → report. On any FAIL: revise proposal, never the generated pixels.
