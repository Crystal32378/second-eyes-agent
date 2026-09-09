# Second Eyes — Architecture (as implemented)

> Read this diagram with the legend. Dashed nodes are **presentation-only**:
> they appear in the static Publishing Workroom mock and in copy, but no
> runtime connection exists. Solid nodes are implemented and tested.

```mermaid
flowchart TB
    subgraph INPUT["Inputs (read-only)"]
        SYN["Synthetic fixtures<br/>fixtures/synthetic (SHA-pinned)"]
    end

    subgraph AGENT["Strands agent layer (implemented)"]
        LOOP["agent/loop.py<br/>5-step loop + pure route()<br/>CLEAR / CONFLICT / UNKNOWN / NEW"]
        PROV["agent/providers.py<br/>Gemini via Vertex AI<br/>model describes only"]
        VOCAB["runtime/vocab.py<br/>FROZEN closed vocabularies<br/>CJK substring scan"]
        RUNNER["runtime/run_synthetic_gemini.py<br/>fresh Agent per fixture<br/>video = BLOCKED_UNSUPPORTED"]
    end

    subgraph EVIDENCE["Evidence & records (implemented)"]
        REFS["attached evidence_ref per selection<br/>ref-less selections discarded"]
        LOG["runtime/logging.py<br/>validate_record + human_queue flags"]
        OUT["outputs/*.jsonl (local)<br/>raw responses + routing + usage"]
    end

    subgraph UI["Static Publishing Workroom UI (implemented)"]
        WR["ui/workroom/brief-established.html<br/>ui/workroom/brief-missing.html"]
        SYNUI["ui/index.html<br/>synthetic 4-state viewer"]
    end

    HUMAN(["Human review boundary<br/>CONFLICT + UNKNOWN ask<br/>NEW filed quiet, CLEAR filed"])

    subgraph FUTURE["Presentation-only — NOT wired"]
        direction TB
        BRIEF["publishing brief parsing"]
        RUN400["400-photo / 382-image live shortlist run"]
        DEDUP["near-duplicate clustering"]
        COV["Coverage computation"]
        POP["automatic SHORTLIST / NEEDS REVIEW / REMAINING population"]
        FINAL3["final-three handoff"]
        VID["video adapter"]
        REEL["Reel Crew handoff"]
    end

    SYN --> RUNNER
    RUNNER --> PROV
    PROV --> LOOP
    VOCAB --> LOOP
    LOOP --> REFS
    REFS --> LOG
    LOG --> OUT
    LOG --> HUMAN
    WR -.->|mock placements only| POP
    WR -.->|illustrative, non-additive| COV
    BRIEF -.->|no parser| RUN400

    style FUTURE fill:#f4f1eb,stroke-dasharray:5 5
    style BRIEF fill:#fff,stroke-dasharray:5 5
    style RUN400 fill:#fff,stroke-dasharray:5 5
    style DEDUP fill:#fff,stroke-dasharray:5 5
    style COV fill:#fff,stroke-dasharray:5 5
    style POP fill:#fff,stroke-dasharray:5 5
    style FINAL3 fill:#fff,stroke-dasharray:5 5
    style VID fill:#fff,stroke-dasharray:5 5
    style REEL fill:#fff,stroke-dasharray:5 5
```

## What's real vs what's mock

| Layer | Status | Evidence |
|---|---|---|
| Strands agent loop + pure `route()` | Implemented, 15/15 tests | `agent/loop.py`, `tests/test_route.py` |
| Gemini provider (Vertex, image only) | Implemented, live smoke OK | `agent/providers.py`, `runtime/check_gemini.py` |
| Fresh-agent-per-fixture isolation | Implemented | `runtime/run_synthetic_gemini.py` |
| Evidence refs + validated run records | Implemented | `runtime/logging.py`, local `outputs/` |
| Frozen vocabularies | Implemented + frozen pre-run | `runtime/vocab.py` freeze note |
| Synthetic fixtures (6, SHA-pinned) | Implemented | `fixtures/synthetic/` |
| Publishing Workroom static pages | Implemented (mock placements) | `ui/workroom/`, `ui/index.html` |
| Brief parsing / live 400-run / clustering / coverage / auto-population / final-three / video adapter / Reel Crew handoff | Presentation-only | `docs/shortlist-brief.md` (spec, no runner) |

## Key contracts

- The model describes; **only `route()` decides** (structural, not prompt-based).
- Selections without an attached `evidence_ref` are discarded, never routed.
- Closed vocabularies are frozen; post-run additions are forbidden.
- Synthetic fixtures prove plumbing only — never accuracy.
- No brief = no clearance basis; every photo is 待確認 at best.
