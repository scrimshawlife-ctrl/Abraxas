# AAL-Core Active Plan Surface

This file is the append-first execution queue for implementation runs.

## Operating Contract
- Keep updates incremental; avoid rewriting historical entries.
- Add new tasks under the active queue with date + owner + status.
- Move finished items to `Completed` with closure notes and linkage references.

## Active Queue

### P0 — Validator Artifact Linkage Closure
- **Status:** ACTIVE
- **Intent:** ensure rune execution artifacts link cleanly into validator/ledger surfaces.
- **Definition of done:** linkage fields populated or explicitly marked unresolved with reasons.

### P0 — Proof-Run Correlation Pointer Completion
- **Status:** ACTIVE
- **Intent:** complete correlation pointer propagation across run outputs.
- **Definition of done:** all execution artifacts include correlation pointer set semantics (present, empty, or unresolved reason).

### P1 — Rune-Aware Validator Surfacing
- **Status:** ACTIVE
- **Intent:** surface rune_id and phase-aware status in validator-facing summaries.
- **Definition of done:** validator layer can index or display per-rune execution outcomes.

### P1 — Execution Artifact Generation Integration
- **Status:** ACTIVE
- **Intent:** route execution-producing paths through a shared rune artifact envelope.
- **Definition of done:** new execution paths use wrapper-generated schema-aligned artifacts.

### P2 — Operator UI Spine Follow-up
- **Status:** CONDITIONAL
- **Intent:** only pursue if current roadmap still requires operator-facing execution trace surfaces.
- **Definition of done:** explicit go/no-go decision and scoped UI task list.

## Completed
- *(append completed items here; do not delete historical record)*
- 2026-03-28 — ABX-Rune compliance probe path added (`aal_core/runes/compliance_probe.py`) with deterministic `RUNE.INGEST` artifact emission to `artifacts_seal/runs/compliance_probe/<run_id>.artifact.json`.
- 2026-03-28 — Correlation-linkage compliance probe added via `--linkage-mode` (`absent|present|not_computable`) with deterministic local test linkage provenance and explicit structural handling for empty/non-computable linkage.
