# Plan — the four unclaimed settlements, and Semion's seven open decisions

**Date**: 2026-10-07 · **Status**: Part 1 EXECUTING, Part 2 is a decision brief
**Repo**: `Abraxas` (`abraxas/engines/manifest.py`, `tests/test_engine_settlement_survey.py`, `KANBAN.md`)

---

## Goal

1. **Part 1** — claim the technical settlement for the four live engines that are measured, passing and
   unclaimed (`athanor`, `noesis`, `trutina`, `cypher`), each with cited evidence, and keep the guard that
   constrains such claims honest.
2. **Part 2** — supply the *evidence* each of Semion's seven remaining open decisions needs, without
   resolving any of them: they are operator/data-governance calls, and Semion's own docs state the
   behavioural tightenings they imply are deliberately not shipped.

## Current context / assumptions

- `oracle` already holds the first technical settlement (this session). Only `technical` is claimed there;
  empirical and economic stay unsettled, and the same applies to the four below.
- `scripts/survey_engine_settlements.py` is the corroborator. Measured now, from its own field:
  `athanor`, `noesis`, `trutina`, `oracle`, `cypher` → `technical_satisfiable=True`, every criterion `yes`.
- A settlement MUST cite evidence, and every cited path must EXIST (`test_settlement_evidence_references_resolve`).
- `tests/test_engine_settlement_survey.py` pins `DECLARED_TECHNICAL_SETTLEMENTS` by equality and asserts
  `declared <= satisfiable`.
- **Trap avoided while measuring**: a probe that compares criteria to `'present'` reports `False` for
  everything, because the survey's constant is `'yes'`. Read `technical_satisfiable` itself.

---

## Part 1 — the four claims

### 1.1 Evidence sets (all paths verified to exist)

| engine | implementation | cited evidence |
|---|---|---|
| `athanor` | `abraxas/evidence/provider.py:create_athanor_adapter` | `abraxas/evidence/provider.py`, `tests/test_engine_manifest_agreement.py` |
| `noesis` | `abraxas/evidence/verifiers/latent.py:NoesisEvidenceProvider` | `abraxas/evidence/verifiers/latent.py`, `abraxas/evidence/noesis_latent_v1.spec.md`, `abraxas/evidence/test_noesis_q1.py`, `abraxas/evidence/noesis_q1_receipt.json` |
| `trutina` | `abraxas/evidence/providers/trutina.py:TrutinaEvidenceProvider` | `abraxas/evidence/providers/trutina.py`, `abraxas/evidence/trutina_calibration_v1.spec.md`, `abraxas/evidence/test_trutina_q1.py`, `abraxas/evidence/trutina_q1_receipt.json` |
| `cypher` | `abraxas/evidence/adapters/cypher.py:create_cypher_adapter` | `abraxas/evidence/adapters/cypher.py`, `tests/test_cypher_enhanced.py` |

**`athanor`'s set is the thinnest, and the note must say so.** There is no athanor-specific spec, fixture or
receipt in this tree — its work lives in its own repository. What holds the claim up is the parametrised
conformance guard plus the survey's measured criteria, and the claim should name that rather than imply an
evidence base it does not have.

### 1.2 Tasks

1. Add `settlements=Settlement(technical=SETTLED, technical_evidence=(...))` to each of the four `_spec`
   entries in `abraxas/engines/manifest.py`, with a note stating what is claimed and what is not.
2. Update `DECLARED_TECHNICAL_SETTLEMENTS` in `tests/test_engine_settlement_survey.py` to the five-engine
   set. The test's own message requires the update in the same commit as the claim.
3. Run the survey: expect `corroborated: ['athanor','cypher','noesis','oracle','trutina']`, exit 0.
4. Run `scripts/test_ratchet.sh`; commit; push; verify CI.

### 1.3 Verification

- `python scripts/survey_engine_settlements.py` → exit **0**, all five corroborated.
- `pytest tests/test_engine_manifest_agreement.py tests/test_engine_settlement_survey.py` → all pass.
- Ratchet: failures 0, collected count unchanged (no tests added), `OK: within baseline`.

---

## Part 2 — Semion's seven remaining decisions (deny-by-default: evidence only)

Each row: what it asks, what was **measured** from here, and what still needs their named reviewer.
Nothing below is resolved by this plan.

### DEC-001 — does E-S3 gate an experimental run, naming weights, or both?
**Measured**: nothing from Abraxas — no semion run, weights or machine is referenced here.
**Needed by them**: "exact action, artifact, machine, data hash, and sentence" (their register's words).
**Recommendation**: keep `name_gate false`; treat run permission and release proof as separate grants.

### DEC-002 — full 300 split, or the preferred 242-row HQ pool?
**Measured**: nothing — the pool lives in their private pack, not here.
**Recommendation**: their safe treatment is already right (preserve split assignments; never train held
NC/test rows; recompute floors on the actual selected subset rather than borrowing full-pool counts).

### DEC-003 — should explicit NC dominate heuristic hints? **← a defect, not just a question**
**Measured** (reproduced against their `src/semion/classify.py`):

| input | result |
|---|---|
| explicit `classification: "icon"` | `icon`, `is_sign=True`, `epistemic=OBSERVED` |
| explicit `classification: "NOT_COMPUTABLE"` | `symbol`, `is_sign=True`, **`epistemic=OBSERVED`** |
| explicit NC **plus** an index hint | `index`, `is_sign=True`, **`epistemic=OBSERVED`** |
| no label, one hint | `index`, `is_sign=False`, `epistemic=NOT_COMPUTABLE` |
| no label, two hints | `mixed`, `is_sign=False`, `epistemic=NOT_COMPUTABLE` |

**The finding**: `_class_from_atom` honours an explicit label only when it is one of
`{icon, index, symbol, mixed}`. An explicit **NC** is not in that set, so it falls through to the hint scan —
and the result is stamped `OBSERVED`. A source that says *"I cannot classify this"* is therefore upgraded to
a confident, observed label. The inversion is stark: hints alone yield `NOT_COMPUTABLE`, while the explicit
refusal yields `OBSERVED`.
**Do NOT patch `classify.py`**: Semion's own `docs/START_HERE.md` says the proposed behavioural tightening
*"is explicitly not shipped"*. This is evidence for the decision.
**Recommendation**: treat explicit NC as terminal (short-circuit before hints), and route contradictory
labels to review rather than letting a hint win — their register's own safe treatment.

### DEC-004 — consumer action enum and `SemiosisFrame.v1` schema
**Resolved from Abraxas's side this session: it cannot be closed here.** Abraxas has **no**
`SemiosisFrame.v1` consumer; the export exists but nothing consumes it, so there is no consumer schema to
pin. Semion's `specs/contracts.md` already states the consequence — *"Unknown consumer schema: compatibility
NOT_COMPUTABLE."*
**Also recorded**: a name collision — Abraxas has an unrelated `action_type` field in the evolution
subsystem, so wiring by field name would be a silent semantic error.

### DEC-005 — what evidence warrants `OBSERVED` for a class?
**Measured**: the same code path as DEC-003 already stamps `OBSERVED` from an explicit label, and the
register notes `corpus_ref` presence is treated as sufficient elsewhere. The minimum bar that would make
`OBSERVED` mean something is independently referenced label evidence — source existence and label
correctness tracked separately, which is their proposed treatment.
**Recommendation**: adopt their proposal; the DEC-003 measurement above is the concrete case that shows why
label presence alone cannot carry `OBSERVED`.

### DEC-006 — T0/T1 comparison when T0 reads labels
**Measured**: nothing from here; this is an evaluation-protocol call.
**Recommendation**: their proposal (label-hidden feature-parity benchmark plus a separate adapter-fidelity
test, no score until the protocol is frozen) is the only version that does not reward the leak.

### DEC-007 — retention, access and licence scope for the private corpus
**Measured**: Abraxas has dependency/readiness policies (`dependency_surface_policy.v0.yaml`,
`readiness_policy.v1.yaml`, `.aal/policy.json`) but **no data-licensing policy to cite**, so nothing here
can supply the scope. Fully theirs.
**Related precedent worth knowing**: Athanor's `README.md` lists *"copyright dumps"* among its anti-goals,
and its corpus-derived fixture sits untracked rather than committed — a sibling project's answer to the same
question, not a rule for Semion.

### DEC-008 — which router swap/replay, dual-use reviews and scoped approvals are current?
**Measured**: Abraxas contains **no runtime Semion wiring** — the only references are the Q1 fixtures and
the instrument added this session. So no router swap involving Semion is present here.
**Recommendation**: report historical claims only, as their safe treatment already says.

---

## Risks, tradeoffs, open questions

- **Claiming four at once dilutes the precedent.** `oracle`'s claim was deliberately one engine wide so the
  first claim would be a precedent. Claiming four now is defensible only because each is independently
  corroborated and individually cited — and because the guard asserts `declared <= satisfiable`, so a claim
  that stops being corroborated fails rather than lingering.
- **`athanor`'s thin evidence set** is the weakest of the five. The claim is honest only if the note says so;
  otherwise it reads as an evidence base it does not have.
- **Settlement ≠ quality.** `technical` says the engine reliably meets its specification. It says nothing
  about usefulness. Nine of ten engines remain unsettled on empirical and economic, which is the honest state.
- **Semion's register stays open.** Seven of eight rows remain the operator's or a named reviewer's; the
  deliverable here is evidence, not resolution. The DEC-003 measurement is the one that changes shape: it is
  a reproducible defect, and the decision is which way to tighten it.
