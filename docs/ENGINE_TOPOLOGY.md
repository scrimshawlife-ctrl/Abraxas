# Engine Topology

**Single source of truth:** `abraxas/engines/manifest.py`.
**Guard:** `tests/test_engine_manifest_agreement.py`.

Nothing here is authoritative prose — if this document and the manifest disagree, the
manifest wins. It exists to record *why* the labels are what they are.

## The ten engines

Yggdrasil's coordinator declared this set (`default_engines`). It is the architecture's
intended topology:

| Engine | Status | Evidence type | Implementation |
|---|---|---|---|
| `athanor` | **live** | RELATIONAL_REASONING | `abraxas.evidence.provider:AthanorAdapter` |
| `noesis` | **live** | LATENT_STRUCTURAL | `abraxas.evidence.verifiers.latent:NoesisEvidenceProvider` |
| `trutina` | **live** | CALIBRATION | `abraxas.evidence.providers.trutina:TrutinaEvidenceProvider` |
| `oracle` | **live** | RELATIONAL_REASONING | `abraxas.evidence.adapters.oracle` |
| `cypher` | **live** | RELATIONAL_REASONING | `abraxas.evidence.adapters.cypher` |
| `hyperlex` | planned | LEXICAL_SEMANTIC | test-local class only |
| `semion` | planned | SIGN_RELATION | test-local class only |
| `chronos` | planned | — | none found |
| `resonance` | planned | — | none found |
| `aether` | planned | — | **zero files in the repo** |

`yggdrasil` is the coordinator, not an engine it routes to. `mock` is a test double.

## The audit that produced these labels

Three lists existed and disagreed:

1. **`abraxas/yggdrasil/coordinator.py`** listed 10 engines (+ `yggdrasil`, `mock`).
2. **`abraxas/governance/production.py`** registered 5 — `athanor, hyperlex, semion, noesis,
   trutina` — and **all five were inline `type(...)` mock providers** whose
   `produce_evidence` called `self._mock_evidence(...)`.
3. **Reality:** only `athanor, noesis, trutina, oracle, cypher` have real
   `EvidenceProvider` implementations.

**Overlap between the production registry and reality was zero**, and `oracle` and `cypher`
— both fully implemented — were never registered at all. A stale banner in
`abraxas/evidence/__init__.py` additionally claimed "4-engine" arbitration.

That banner has been removed (a library module was printing ten lines on every import,
which is how the stale claim survived). The topology now lives in one place.

## Open item, deliberately not changed

`production.py` still registers mock providers. Switching it to the real implementations
will change arbitration output, and the mock path is very likely what current tests assert
against. That is a behaviour change, so it is scheduled separately rather than folded into
a test-debt pass. It is the highest-value remaining item in this area: production
governance currently arbitrates on fabricated evidence.

## How to promote a planned engine

1. Implement an `EvidenceProvider` emitting a canonical `EvidenceEnvelope`.
2. Move its `EngineSpec` in `abraxas/engines/manifest.py` from `PLANNED` to `LIVE` and fill
   in `implementation`.
3. `tests/test_engine_manifest_agreement.py` will then require the module to import, and
   will fail if you forget.

Never mark an engine `live` without an implementation, and never add a `planned` engine to
anything that presents engines as available.
