# Abraxas

Deterministic symbolic intelligence for operator-grade interpretation, synthesis, and routing.

Abraxas converts bounded runtime/domain signals into:
- detector family outputs,
- fused interpretation,
- synthesis state + next-step guidance,
- routing recommendations,
- artifact-linked diagnostics.

---

## What Abraxas does

Abraxas is a deterministic decision surface over symbolic/runtime signals. It is designed to be:
- **Deterministic**: explicit rule ladders, no probabilistic hidden ranking.
- **Bounded**: compact summaries and limited reason surfaces.
- **Provenance-linked**: outputs tied to run/artifact context.
- **Operator-visible**: fusion, synthesis, routing, and health surfaces are rendered in one console.

Core flow:

`INPUT CONTEXT -> DETECTORS -> FUSION -> SYNTHESIS -> ROUTING -> OUTPUT CARD + ARTIFACTS`

---

## Core feature set

### 1) Detector families
- Pressure / Friction
- Motif / Recurrence
- Instability / Drift
- Anomaly / Gap

Each detector emits labels, reasons, and bounded summaries with deterministic precedence.

### 2) Fusion engine
- Compresses detector state into a single fused interpretation.
- Emits `fused_label`, `compressed_fusion_reason`, and bounded interpretation summary.
- Includes signal sufficiency-aware degradation to avoid overreach on thin context.

### 3) Synthesis layer
- Produces `synthesis_label`, reasons, blockers, and next step.
- Enforces explicit blocker dominance and precedence notes.
- Prevents optimistic output when blocker/sufficiency constraints dominate.

### 4) Routing layer
- Produces pipeline recommendation and rule-aligned reason detail.
- Distinguishes review-preferred, ready-preferred, and less-blocked branches.
- Exposes `routing_reason_detail` and manual override messaging.

### 5) Operator console surfaces
- Final Abraxas Output Card
- Domain logic workspace (incl. sufficiency + compressed fusion)
- Synthesis summary + precedence note
- Routing summary + reason detail
- Reporting and viz render summaries

### 6) Diagnostics and verification artifacts
- Weakness exposure artifacts (before)
- Weakness exposure + fix verification artifacts (before/after)
- Demo-ready compact artifact pack

---

## Demo artifact pack (v5.4)

Representative 3-case demo pack generated from validated diagnostics:

- JSON: `data/diagnostics/20260329t203413z.demo_artifact_pack.json`
- Markdown: `data/diagnostics/20260329t203413z.demo_artifact_pack.md`

Cases included:
1. `CASE_MINIMAL_SIGNAL` (graceful degradation under thin signal)
2. `CASE_CONTRADICTORY_SIGNAL` (conflict resolution + review-oriented routing)
3. `CASE_EDGE_BINDING` (binding/linkage stress with explicit blocker handling)

Companion validation artifacts:
- `data/diagnostics/20260329t202641z.weakness_exposure_fix.json`
- `data/diagnostics/20260329t202641z.weakness_exposure_fix.md`

---

## Quick start

### Python environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Run targeted refinement tests

```bash
pytest -q webpanel/test_operator_console_refinement.py
```

### Open operator surface (project-dependent run command)

Use the project’s existing webpanel runtime entrypoint in your environment, then navigate to the operator console route.

---

## Repository map (high-signal paths)

- `webpanel/operator_console.py` — detector/fusion/synthesis/routing/viewstate logic
- `webpanel/templates/operator_console.html` — operator UI surfaces
- `webpanel/test_operator_console_refinement.py` — targeted deterministic behavior tests
- `data/diagnostics/` — tracked diagnostics and demo artifacts
- `artifacts_seal/abraxas_diagnostics/` — generated run-linked diagnostic artifacts

---

## Current status

Interpretive integrity and adversarial verification are in place with deterministic before/after diagnostics.

Latest diagnostic verdict (v5.4 casepack): **READY_FOR_DEMO**.

---

## License

See `LICENSE`.
