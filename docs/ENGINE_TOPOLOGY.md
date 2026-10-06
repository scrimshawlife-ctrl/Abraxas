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

## The production mock-provider item — CLOSED 2026-10-06

This section previously read *"production.py still registers mock providers … production
governance currently arbitrates on fabricated evidence"*, and called itself the highest-value
remaining item. **That was stale, and it caused a wrong recommendation** — a switch was
proposed for something already switched.

The actual state:

| Claim | Reality |
|---|---|
| production registers mock providers | `initialize(use_mocks=False)` is the **default** and resolves the manifest's `live` engines into real providers |
| mocks are the norm | `use_mocks=True` is an explicit legacy branch documented *"exists for tests and nothing else"*; its only caller anywhere is `tests/test_production_engine_wiring.py` |
| nothing guards this | `test_production_engine_wiring.py` asserts the default registers no mocks and that planned engines report UNHEALTHY; `test_production_arbitration_e2e.py` was written to guard it |

**Lesson worth keeping:** a status document is a claim, not evidence. This one contradicted
the code it described, and the contradiction survived because nothing resolves a doc against
the thing it documents — unlike the manifest's entry points, which a test does resolve.

### Fabricated evidence in the streaming path — RESOLVED 2026-10-06

Jev **abstained** on this (top confidence 0.39, below the 0.65 floor; `delete_path` a 0.52
plurality), scoring `present_risk 0.43`, `doc-only sufficient 0.24`,
`apply_autonomously 0.19` — so it went to the operator rather than being applied.

The operator directed a best-practice fix; the option taken was **rewire**, for reasons the
manifest itself supplies:

| Option | Why not |
|---|---|
| `delete_path` | would remove a capability worth building rather than fix it |
| `mark_unsupported` | *"a name with no implementation is worse than an absent one"* — the manifest's own words about `aether` |
| `document_only` | Jev scored it 0.04, and it leaves a hazard guarded only by accident |

`_process_stream_item` no longer constructs an envelope. It calls `_collect_evidence` — the
same path `run_pipeline` uses. **One evidence path now, not two.**

`ProductionOrchestrator._collect_evidence` is the only place the orchestrator obtains
evidence, and it cannot synthesise any: an engine that raises is recorded `DEGRADED` and
contributes nothing, so failure yields an **absence** rather than a fabricated result.
Unhealthy engines are skipped rather than asked, so health can actually withhold evidence.
With no usable engine the streaming path records `ABSTAIN` with `engines_used: []`.

Guard: `tests/test_governance_evidence_provenance.py` —

1. a **static scan** asserting every literal engine name in a governance-built envelope is
   declared in the manifest — this is what caught `engine="stream"`, and it fails if the
   pattern reappears anywhere under `abraxas/governance/`, reachable or not;
2. a **count** asserting the layer has exactly one construction site (the declared test
   double), counted rather than line-pinned so an unrelated edit above it cannot cause a
   false failure;
3. two **behavioural** tests over the streaming path, including the no-usable-engine case.



## How to promote a planned engine

1. **Check the engine's own spec first.** `hyperlex` and `semion` are *not* promotion
   candidates, even though `production.py` claims them and an earlier version of the
   manifest called hyperlex "the closest to promotion". `hyperlex_instrument.py`'s
   `promote_to_canonical_state()` *always* raises, and `TestHYPERLEX_Q1_PromotionBlocked`
   asserts that block; semion has no instrument module at all. Both are deliberate SHADOW
   surfaces. Promoting either means changing its authority boundary first — writing an
   `EvidenceProvider` is not sufficient, and would contradict the spec that blocks it.
2. Implement an `EvidenceProvider` emitting a canonical `EvidenceEnvelope`.
3. Move its `EngineSpec` in `abraxas/engines/manifest.py` from `PLANNED` to `LIVE` and fill
   in `implementation` — which the manifest will then require to resolve.
4. `tests/test_engine_manifest_agreement.py` will require the module to import, and will
   fail if you forget.

Never mark an engine `live` without an implementation, and never add a `planned` engine to
anything that presents engines as available.

The second half of that rule is now mechanical rather than editorial: registration derives
its lifecycle from this manifest, and `is_engine_available` is true only for `ACTIVE`. A
planned engine cannot be presented as available without editing the manifest itself.
