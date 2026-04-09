# Oracle Signal Layer v2 — Vertical Runtime Proof Spine (2026-04-08)

## Objective
Operationalize canon-defined Oracle Signal Layer v2 behavior as an advisory-first interpretation runtime with strict authority/advisory separation, receipts, and digest-first invariance.

## Scope / lane / subsystem / class
- **Scope:** contracts + runtime + advisory framework + MIRCL + trend seam + proof surfaces + invariance + tests + docs
- **Lane:** `forecast-active` / `shadow` input metadata, interpretation-only authority scope
- **Subsystem:** `oracle_signal_layer_v2`
- **Change class:** `forecast_active_change`

## Input envelope law
`OracleSignalInputEnvelope.v2` is the only accepted runtime input and must include:
- `signal_sources` (enumerated)
- `payload` (opaque hashable object)
- `context` (bounded fields)
- `metadata` (tier, lane, provenance flags)

Runtime split is explicit:
- hashable core fields
- display-only fields
- not-computable trigger fields

## Runtime chain
1. Normalize/validate input envelope
2. Compress/dedupe/bound/decay deterministic operators
3. Build authority payload (`authority_scope=interpretation_only`)
4. Invoke advisory registry (MIRCL + trend) in allowlist order
5. Emit final output with boundary marker
6. Compute digest triplet (`input_hash`, `authority_hash`, `full_hash`)
7. Emit validator summary + invariance summary + ledger row

## Advisory boundary law
- Authority payload is immutable post-build.
- Advisory attachments are downstream-only and isolated.
- MIRCL and trend adapters cannot alter authority fields by API shape.
- Missing advisory inputs produce visible `NOT_COMPUTABLE` + `computable=false`.

## MIRCL bounded payload fields
- `meaning_pressure`
- `narrative_instability`
- `perception_drift`
- `meaning_state_summary`
- `reality_state`
- `dominant_controller`
- `key_constraints`

## Entrypoints
```bash
PYTHONPATH=. python scripts/run_oracle_signal_layer_v2.py --input docs/artifacts/oracle_signal_input_envelope_sample.v2.json
PYTHONPATH=. python scripts/run_oracle_signal_layer_v2_invariance.py --input docs/artifacts/oracle_signal_input_envelope_sample.v2.json --repeats 12
```

## Proof surfaces
- `out/oracle_signal_layer_v2/oracle_signal_layer_output_<run_id>.json`
- `out/oracle_signal_layer_v2/oracle_invariance_<run_id>.json`
- `out/oracle_signal_layer_v2/oracle_validator_summary_<run_id>.json`
- `out/ledger/oracle_signal_layer_v2_runs.jsonl`
