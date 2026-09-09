# Public-demo replacement set — SUPERSEDED (executed as HEAD 472832b)

SUPERSEDED NOTE 2026-09-09: direct inspection found one fully visible eye
in REEL-032, so the borderline keep was rejected; the final approved
replacement is BACK-5F20. Kept for audit trail only — see
docs/demo-derivatives.md for the executed manifest.

# Public-demo replacement set — PROPOSAL (NOT yet applied, for Fu review)

Rule (Crystal, supplied project decision — not a model inference):
**NO CLEARLY IDENTIFIABLE FULL FACE.** Allowed: product-only, flat lays,
details, packaging, hanging products, cropped on-body, full-face-not-visible
(eyes obscured/out of frame OK; chin/mouth/jaw tolerated when not presented
for identity). Exclude: unobstructed full faces, recognizable portrait
framing, minors, people in mirrors/screens/backgrounds, legible third-party
logos/editorial, private info, anything requiring guessing.

Explicitly approved example (Crystal): `IG Reel/華麗年代/810662E2-3A19-428F-AB8A-C5909FC4B928.jpg`
(2340×2519 vertical, eyes covered by hand — verified by direct inspection).
Selection ≠ copyright or model-release clearance (see rule 6 of task).

## Audit of current 12 (Kimi set)

KEEP (7) — no face, no logo issues:
- IG-262, IG-277, IG-072, IG-256, IG-245, REEL-045: product/flatlay/detail/packaging
- REEL-050 (IMG_4491.JPG): back view, no face (back-strap detail)

BORDERLINE, Fu decides (1):
- REEL-032: eyes fully outside frame, nose/mouth/chin visible in a lace
  product close-up. Same class as the approved example; keep or replace.

EXCLUDE (4):
- REEL-022 (12.jpg): unobstructed full face, recognizable → OUT
- REEL-044 (AB823328): recognizable portrait framing (one eye + full face
  readable) → OUT
- REEL-035 (video poster): face visible IN A MIRROR → explicitly excluded
  by rule → OUT
- IG-223 (627A5150-28.jpg): legible third-party logos (LV monogram bag,
  Chloé glasses) + editorial text → OUT (not a face issue)

## Proposed replacements (4, all directly inspected)

1. REEL-022 slot (outdoor context) → `IG Reel/華麗年代/IMG_4489.PNG`
   Outdoor, vertical, face obscured by raised arm/hair. Same shoot family.
2. REEL-044 slot (wearing context) → `IG Reel/華麗年代/810662E2-3A19-428F-AB8A-C5909FC4B928.jpg`
   Crystal-approved. Vertical on-body, eyes covered. (Approval = supplied
   decision; do NOT describe as identity-verified/anonymous/cleared.)
3. REEL-035 slot (vertical motion source) → `IG Reel/華麗年代/華麗年代黑色.mp4`
   (poster @1.0s verified: NUDE box + hand, no face. CORRECTION 2026-09-09:
   first draft named 灰色.mp4 from a misattributed hash filename; re-pull
   per named file shows 灰色 @1.0s is a full face → rejected, 粉色 @1.0s is
   a partial but recognizable face → rejected conservative. Slot re-labels
   to packaging-in-motion at execution.)
4. IG-223 slot (robe flatlay) → `IG/絲柔光璨長袍/627A5059-17.jpg`
   Blue robe hanging, no people, no third-party marks. (Siblings rejected:
   …065-18 has a face on a background TV screen; …074-19 has legible
   editorial print; …562-1/…599-4 carry unbranded-but-ambiguous leather goods.)

Reviewed spares (same family, clean, unused): 5C063594 (no-face on-body),
5E5716F2 (torso close-up), 5F205533 (back view).

Resulting mix: product ×4, flatlay/detail ×3, packaging ×3 (incl. video),
vertical ×3, obscured-face on-body ×3. No minors encountered. Nothing here
asserts clearance; UI keeps "No release or clearance assessment".

## Execution (ONLY after Fu approval)

Derivatives per Kimi spec (EXIF-oriented, proportional resize, no crop,
no content painted out), new IDs, HTML ref swap, re-screenshot, commit.
No originals modified. No backend/Batch A/fixture/vocab/model changes.
