# Engine Topology

**Single source of truth:** `abraxas/engines/manifest.py`.
**Guard:** `tests/test_engine_manifest_agreement.py`.

Nothing here is authoritative prose — if this document and the manifest disagree, the
manifest wins. It exists to record *why* the labels are what they are.

## The ten engines

Yggdrasil's coordinator declared this set (`default_engines`). It is the architecture's
intended topology:

| Engine | Status | Evidence type | Implementation | Inference |
|---:|---|---|---|---|
| `athanor` | **live** | RELATIONAL_REASONING | `abraxas.evidence.provider:create_athanor_adapter` | **model-agnostic** |
| `noesis` | **live** | LATENT_STRUCTURAL | `abraxas.evidence.verifiers.latent:NoesisEvidenceProvider` | none — consumes supplied captures |
| `trutina` | **live** | CALIBRATION | `abraxas.evidence.providers.trutina:TrutinaEvidenceProvider` | none — scores given forecasts |
| `oracle` | **live** | NARRATIVE_SYNTHESIS | `abraxas.evidence.adapters.oracle:create_oracle_adapter` | **model-agnostic** |
| `cypher` | **live** | PERSISTENT_MEMORY | `abraxas.evidence.adapters.cypher:create_cypher_adapter` | none — reads the memory layer |
| `hyperlex` | **live** | LEXICAL_SEMANTIC | `abraxas.evidence.providers.hyperlex:create_hyperlex_adapter` (sibling-spec + in-tree instrument) | feature-gated package call · `~/Hyperlex/` |
| `semion` | **live** | SIGN_RELATION | `abraxas.evidence.providers.semion:create_semion_adapter` (sibling-spec + in-tree instrument) | none — consumes a sign frame · `~/Semion/` |
| `chronos` | **live** | TEMPORAL_REASONING | `abraxas.evidence.providers.chronos:create_chronos_adapter` (sibling-spec + in-tree rune compose) | none — rune orchestration · `~/Chronos/` |
| `resonance` | **live** | RESONANCE_ANALYSIS | `abraxas.evidence.providers.resonance:create_resonance_adapter` (sibling-spec + in-tree phase compose) | none — phase detectors · `~/Resonance/` |
| `aether` | planned (**in development, multimodal**) | MULTIMODAL_INTEGRATION | `abraxas.evidence.providers.aether:create_aether_adapter` (refuses via AetherNotImplemented per sibling SPEC) | n/a: refuses |

**`aether` is in development as the multimodal engine (2026-10-10).** It is the planned path for image and video meme forecasting and is exempt from the 30-day engine freeze (see [DECISIONS.md](DECISIONS.md)). As of 2026-10-10 its code is a specification and a refusing boundary only: Zero-State-LLC/Aether holds SPEC.md, KANBAN.md and a provider that raises `AetherNotImplemented` (last commit 2026-10-07); no encoder, fusion policy or checkpoint exists yet. The manifest status stays `planned` and the provider keeps refusing until a real implementation passes its own eval against the text-only baseline. The fusion policy in [docs/aether/](aether/) comes before encoders.

Implementation paths are copied from the manifest, and
`tests/test_engine_manifest_agreement.py` *resolves* each one — so a wrong path fails the
suite instead of sitting here harmlessly. Three rows above previously named a module
without its entry point; one of them (`AthanorAdapter`) exists only *inside* the factory,
so it was unreachable under that name. An earlier version of the guard imported the module
and stopped there, which is why it passed while claiming a class that did not exist.

`yggdrasil` is the coordinator, not an engine it routes to. `mock` is a test double.

## Where an engine needs a model, the model is model-agnostic

Five of the ten engines need no model at all: `noesis` consumes latent captures supplied to it, `trutina`
scores forecasts it is given, `cypher` reads the memory layer, and `chronos` and `resonance` run rune and
phase logic. `semion` consumes a sign frame. None of them has an inference step to serve.

Two need one — `athanor` (relation extraction over atoms) and `oracle` (narrative synthesis) — and both
resolve it through `abraxas.evidence.adapters.model_agnostic`:

| Connection | Identity reported | Note |
|---|---|---|
| `ABX_INFERENCE_BASE_URL` + `ABX_INFERENCE_MODEL` set | `model-agnostic/<model>` | any OpenAI-compatible endpoint |
| nothing set | `model-agnostic/offline-deterministic` | a deterministic reading, confidence **0.0** |
| a custom callable injected | its own `model_identity`, else `custom/unlabelled` | the escape hatch for a trained model |

`aether` is the third engine with an inference requirement, and it refuses: `produce_evidence()` and
`get_model_identity()` raise `AetherNotImplemented`. That refusal is the pattern working — an engine with no
model says so rather than guessing.

**No reading produced without a model carries a confidence.** The offline path yields candidates with
`confidence=0.0` and stamps `provenance["inference"] == "offline-deterministic"`; the pair is the honest
statement *here is a reading, and nothing scored it*. Both halves are asserted in
`tests/test_engines_name_no_model_they_do_not_have.py`.

Two defects prompted this, both of the same shape — a provenance field naming a model that produced nothing:

- Oracle's `_default_oracle_inference` built a `coherence_score` from word counts (`+= 0.1  # Sweet spot for
  coherence`) and published it as the envelope's **confidence**. A keyword heuristic scored as a model's
  assessment. Deleted; the model-agnostic adapter is the default.
- Athanor reported `lora-out-transfer-001-t1/checkpoint-48`. Its default path also **crashed** —
  `AttributeError: 'str' object has no attribute 'confidence'` — because the adapter was wired in as the
  default and never executed: every test injected a mock that returned objects.

### The custom models, measured

The engines above were expected to run on custom-trained adapters. Checked on 2026-10-07, from
`~/Athanor` — they cannot, and not because the weights are poor:

| Evidence | Result |
|---|---|
| `t1_bias_corrected_adapter/` contents | `adapter_config.json`, `tokenizer.json`, `chat_template.jinja` — **no weight file** |
| `git ls-files \| grep -c safetensors` (Athanor) | `0` |
| every `*adapter*` / `lora-out*` / `merged-*` dir on this machine | weight files: `0` |
| `specs/003-qwen-adapter/model-lock.json` | `"weight_downloaded": false`, `"allow_train": false`, `"status": "MODEL_REVISION_SELECTED_ENVIRONMENT_NOT_COMPUTABLE"` |
| `python -m athanor.adapter_preflight` | `{"status": "HOLD", "weights_verified": false, "training_authorized": false}` |
| `... --model-dir t1_bias_corrected_adapter` | `{"status": "INVALID", "reason": "Missing, unsafe or oversized model config"}` |
| `EXECUTION-RECEIPT.md` claims | 2 of 7 artifacts present; both *weight files* absent (see its verification note) |

The adapter directory is a freeze record, not a model: its config advertises `"inference_mode": true` with no
`adapter_model.safetensors` beside it, and names base `nvidia/Llama-3.1-Nemotron-Nano-8B-v1` while the spec it
sits near pins `Qwen/Qwen3.8-27B`. Training ran on a different host entirely (`/home/delphi`, GB10, torch
2.15.0.dev).

So the model-agnostic adapter is not a stopgap while better models arrive — **it is the only working inference
path**, and it stays the default until weights exist somewhere a consumer can reach. When they do, they arrive
through the injection point: a callable that declares its own `model_identity` and its own confidences.

## Addressable is not available

Two ideas that used to be one object. The registry now separates them:

|  Meaning | Where |
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

## Settlement records (current truth)

`EngineSpec.settlements` (added in Phase 4) defaults every engine to `unsettled` on
`empirical`/`technical`/`economic`, with empty evidence tuples.

**All five live engines claim a `technical` settlement as of 2026-10-07** — `athanor`, `cypher`,
`noesis`, `oracle` and `trutina` — each with its own cited evidence set. **No engine claims
`empirical` or `economic` on any axis**, and no planned engine claims anything. This section
previously read *"No engine claims any settlement today"*, which was true when written and is now
recorded as changed rather than quietly deleted.

**Only `technical`, and that distinction is the point.** A technical settlement says the capability
reliably meets its specification. It is silent on whether the capability beats a baseline
(`empirical`) or produces consequences anyone adopts (`economic`) — the harder claims, and the ones
still open on every engine.

The evidence sets differ widely and each manifest note states which it is rather than implying a
uniform base: `noesis` and `trutina` cite a specification, a Q1 suite and a qualification receipt;
`oracle` cites its adapter, contract and governance record; `athanor` cites only its implementation
and the conformance guard; `cypher` cites only its adapter and behavioural suite.

What exists beyond the declarations is the ENFORCEMENT, and it is what makes a claim checkable
rather than prose. Each test is named here so the claim can be verified instead of believed:

| Test | What it holds |
| --- | --- |
| `test_every_engine_declares_its_three_settlements` | every value comes from the closed set |
| `test_a_settled_settlement_must_cite_evidence` | `settled` without evidence paths is forbidden |
| `test_a_planned_engine_claims_no_empirical_settlement` | extends the manifest's planned/live invariant |
| `test_settlement_evidence_references_resolve` | every cited evidence path exists |
| `test_only_deliberately_declared_engines_claim_technical_settlement` | the declared set is pinned by equality, and every claim must be corroborated (`declared <= satisfiable`) |

`unsettled` remains the honest state for the nine axes nobody has claimed — not a stub, and not a gap
to close for its own sake.

### Corroboration, not just shape

Those four tests enforce the settlement's **shape** — the value comes from a closed set, and `settled`
must cite an evidence path. They cannot enforce that the claim is **true**: a `settled` value carrying
a plausible-looking path satisfies every one of them. Measured, not asserted — injecting a false
settlement for `athanor` (technical = `settled`, citing `tests/test_engine_manifest_agreement.py`)
leaves the shape guard entirely green:

    23 passed, 8 warnings in 0.42s

`scripts/survey_engine_settlements.py` supplies the missing half. It evaluates every engine against
the doctrine's technical-settlement criteria and *refuses to certify a settlement resting on an
unmeasured criterion*. The same injected fault:

    survey verdict: ['athanor']
    exit would be : 1

`tests/test_engine_settlement_survey.py` links the two, so a `settled` declaration must be
corroborated by the survey as well as well-formed.

Current survey state, measured. All five live engines — `athanor`, `noesis`, `trutina`, `oracle`,
`cypher` — clear `entry_point`, `conforms`, `collected_tests`, `determinism`, `provenance`, and
`canonical_artifacts`. The last three are established by *running each engine twice on identical input*
(`abraxas/engines/execution_harness.py`) and comparing the canonical content of the two envelopes, not by
inspection. `conforms` is measured the same way for the factory engines, which are built with a defined
stand-in inference callable.

**All six criteria are now measured for all five live engines, `replay` included.** Replay is measured by
persisting an envelope as a canonical artifact, reading it back, reproducing the run, and comparing
against the *reloaded* artifact — mirroring the `RuneReplayPacket` contract this repository already uses
for runes (`core/execution/replay_runner.py`). It is not determinism repeated: an envelope that survives
two in-process runs can still fail to survive persistence, and only replay sees that.

So `satisfiable` is now **true for all five live engines**: the survey would corroborate a technical
settlement for any of them. That is a capability, not a claim.

### The operator's decision: corroboration available, settlement NOT claimed

Asked and answered on 2026-10-06, when all six criteria first measured as passing: **leave the
settlements `unsettled`, record the corroboration, and revisit later.** Every engine therefore remains
`unsettled` even though the survey would now corroborate a `settled` technical claim for all five live
engines.

The reason on record is scope. The criteria are measured under **one defined input** — the harness's
deterministic stub inference callable — so the evidence supports "performs to specification on a defined
input", not universal determinism. A `Settlement` value is `settled` / `unsettled` / `not_applicable` and
cannot carry that qualification, so the qualification lives here instead. The measurement exists, is
kept honest by tests, and can be cited the moment the operator decides the scope is sufficient.

Two tests hold this line: `test_no_criterion_remains_unmeasured_for_live_engines` fails if any criterion
regresses to `?` (a lost measurement) or `no` (measured and failing), and
`test_only_deliberately_declared_engines_claim_technical_settlement` pins the declared set by equality and
requires every claim to be corroborated (`declared <= satisfiable`), so a settlement cannot be claimed for
an engine the survey cannot corroborate.
