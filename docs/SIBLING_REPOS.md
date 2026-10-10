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

## The engine fleet

Each engine also has its own repository. Until 2026-10-07 this document named only Hyperlex, which is how an
audit of engine completion came to list two engines as having *no repository at all* — they had repositories
that had simply never been cloned to the machine doing the measuring. The map belongs here.

| engine | repository | what Abraxas holds |
|---|---|---|
| `athanor` | `Athanor` | adapter in `abraxas/evidence/provider.py` (built inside the factory) |
| `trutina` | `Trutina` | provider + spec + Q1 suite + receipt under `abraxas/evidence/` |
| `noesis` | `Noesis` | provider + spec + fixtures + receipt under `abraxas/evidence/` |
| `hyperlex` | `Hyperlex` | instrument `abraxas/evidence/hyperlex_instrument.py` |
| `semion` | `Semion` | instrument `abraxas/evidence/semion_instrument.py` (added 2026-10-07) |
| `oracle` | `Oracle` | adapter `abraxas/evidence/adapters/oracle.py` + contract + subsystem record |
| `cypher` | `Cypher` | adapter `abraxas/evidence/adapters/cypher.py` + the memory layer it manages |
| `chronos` | `Chronos` | adapter `abraxas/evidence/providers/chronos.py` + rune composition (SCAN→ALIGN→OVERLAY→PACKET) |
| `resonance` | `Resonance` | adapter `abraxas/evidence/providers/resonance.py` + phase detectors (PhaseAlignment + Coupling) |
| `aether` | `Aether` | nothing — its repository holds a spec and a provider that raises |

### The rule that keeps this from becoming two implementations

**An engine repository holds the spec, the entry point, and the boundary tests — never a second
implementation of something Abraxas already has.** Two shapes follow from that, and they are not
interchangeable:

- **Abraxas owns the implementation** (`oracle`, `cypher`, `noesis`, `trutina`, `athanor`): the repository's
  `compat/abraxas/` bridge *resolves* the canonical factory or class, and its tests assert the wrapped
  object's **module path** is Abraxas's. A local reimplementation fails a test rather than quietly creating a
  second source of truth.
- **The engine owns the machinery and Abraxas consumes it** (`resonance` composes the in-tree phase
  detectors; `semion` consumes a `semion.sign.v1` frame). Semion states the direction itself: *"Semion does
  not import Abraxas. Abraxas may consume this dict at RUNE.SEMIOSIS.CHAIN."* A classifier added to
  Abraxas's Semion instrument would invert a declared dependency as well as duplicate one.

`resonance` is the case that shows why both shapes exist: it has code in Abraxas but **no adapter**, so there
was nothing to delegate to and its repository composes rather than resolves.

### Why the repositories are not dependencies of this one

An engine marked `planned` stays `planned` even when its repository is complete, because the manifest's
`live` criterion is that a real provider **resolves from this tree** — and none of these ten repositories is
an installed dependency. Promotion is a decision to wire one in, not a consequence of a repository existing.

## Binding

- One system, two remotes. Do not smash-merge.
- Module headings in this README such as rune-layer and adaptive-sandbox are local proof versions. They do not activate Abraxas-v2.0 candidate posture.
- SHADOW landings (`influence_policy=NONE`) are not promotion.
- First-gate for code in this repo remains the code-drop envelope (`.abraxas/templates/code_drop_envelope.md`). Not `intent/`.
- Notion owners: Master System + Core Directive (pattern “v2.0”); Master Index stamped 2026-09-04.
