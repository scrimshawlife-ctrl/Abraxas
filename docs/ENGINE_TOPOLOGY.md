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
| `athanor` | **live** | RELATIONAL_REASONING | `abraxas.evidence.provider:create_athanor_adapter` |
| `noesis` | **live** | LATENT_STRUCTURAL | `abraxas.evidence.verifiers.latent:NoesisEvidenceProvider` |
| `trutina` | **live** | CALIBRATION | `abraxas.evidence.providers.trutina:TrutinaEvidenceProvider` |
| `oracle` | **live** | RELATIONAL_REASONING | `abraxas.evidence.adapters.oracle:create_oracle_adapter` |
| `cypher` | **live** | RELATIONAL_REASONING | `abraxas.evidence.adapters.cypher:create_cypher_adapter` |
| `hyperlex` | planned | LEXICAL_SEMANTIC | test-local class only |
| `semion` | planned | SIGN_RELATION | test-local class only |
| `chronos` | planned | — | none found |
| `resonance` | planned | — | none found |
| `aether` | planned | — | **zero files in the repo** |

Implementation paths are copied from the manifest, and
`tests/test_engine_manifest_agreement.py` *resolves* each one — so a wrong path fails the
suite instead of sitting here harmlessly. Three rows above previously named a module
without its entry point; one of them (`AthanorAdapter`) exists only *inside* the factory,
so it was unreachable under that name. An earlier version of the guard imported the module
and stopped there, which is why it passed while claiming a class that did not exist.

`yggdrasil` is the coordinator, not an engine it routes to. `mock` is a test double.

## Addressable is not available

Two ideas that used to be one object. The registry now separates them:

| | Meaning | Where |
|---|---|---|
| **addressable** | the name is registered, so topology and tooling can see it | `registry.is_engine_registered` |
| **available** | a real `EvidenceProvider` exists and it may produce evidence | `registry.is_engine_available` |

Registration derives its lifecycle from this manifest (`status_for`), so the
live/planned distinction survives into the registry: live → `ACTIVE`, planned →
`PLANNED`, non-engines (`yggdrasil`, `mock`, individual rune capabilities) → `REGISTERED`.

Before this, every name was stamped `REGISTERED`, which made `aether` — which has zero
files in the repo — indistinguishable from `athanor`. `YggdrasilCoordinator.arbitrate_evidence`
also only logged a warning for an unknown engine and then arbitrated anyway; it now
**fails closed** and returns `Decision.REJECT`.

Guard: `tests/test_engine_lifecycle_registration.py`.

Registration is also deterministic: the coordinator used to store a wall clock in the
metadata that feeds the rune hash, so the same engine hashed differently on every process
start. The hash now goes through `abraxas/core/canonical.py` — the repo's single canonical
authority — and timestamps come from an injectable clock.


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

The second half of that rule is now mechanical rather than editorial: registration derives
its lifecycle from this manifest, and `is_engine_available` is true only for `ACTIVE`. A
planned engine cannot be presented as available without editing the manifest itself.
