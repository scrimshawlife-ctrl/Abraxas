# Sibling repositories

This repository is the **execution and proof** surface for the Abraxas system (`.abraxas/` registry, gap-closure, rune receipts, `abx` CLI).

Doctrine, candidate architecture, Governance V3, atlas, and continuity spine live in [`scrimshawlife-ctrl/Abraxas-v2.0`](https://github.com/scrimshawlife-ctrl/Abraxas-v2.0).

## Hyperlex (semantic instrumentation)

[`scrimshawlife-ctrl/Hyperlex`](https://github.com/scrimshawlife-ctrl/Hyperlex) provides **HYPERLEX_INSTRUMENT_V1** as a versioned shadow dependency:

```text
text → Hyperlex observe() → HyperlexObservation → abraxas.evidence.hyperlex_instrument
```

- Integration doc: [`docs/integration/hyperlex_instrument_v1.md`](integration/hyperlex_instrument_v1.md)
- Adapter: `abraxas.evidence.hyperlex_instrument`
- Subsystem: `hyperlex_instrument_v1` (lane `shadow`)
- Feature flag: `ABX_HYPERLEX_INSTRUMENT` (default **off**)
- Authority: `HYPERLEX_OUTPUT != SEMANTIC_TRUTH` · `influence_policy=NONE` · `valid_for_forecast=false`
- Roles allowed: `OBSERVATION` | `EVIDENCE` | `SHADOW_SIGNAL` only

Hyperlex does not mint Abraxas canonical state, gold, or authorization.

## Binding

- One system, two remotes. Do not smash-merge.
- Module headings in this README such as rune-layer and adaptive-sandbox are local proof versions. They do not activate Abraxas-v2.0 candidate posture.
- SHADOW landings (`influence_policy=NONE`) are not promotion.
- First-gate for code in this repo remains the code-drop envelope (`.abraxas/templates/code_drop_envelope.md`). Not `intent/`.
- Notion owners: Master System + Core Directive (pattern “v2.0”); Master Index stamped 2026-09-04.
