# TODO Handling Plan — 2026-03-27

Status: active

## OPEN — current queue

1. Decodo/source lane hardening still needs completion in acquisition + resolver edges.
2. Cache-only adapter mode must stay policy-gated and provenance-labeled.
3. Wave 6 repetition proof loop (Chunk C) is not yet fully recorded as evidence.
4. Notion/repo sync artifacts require deterministic regeneration after each chunk.
5. Runtime/ERS coverage still needs a targeted uplift.

## ALIGN — execution constraints

- Preserve deterministic semantics (no hidden fallback paths).
- Every fallback path must emit an explicit reason code.
- Evidence artifacts must be generated from repository state, not manual summaries.
- Prefer incremental chunk closure over broad unspecific refactors.

## ASCEND — build plan

### Phase 1: Re-validate TODO surface (same day)
- Run TODO and stub scans.
- Confirm actionable implementation gaps are non-zero before coding.
- Save scan outputs to dated artifacts.

### Phase 2: Resolve highest-pressure technical items
- Finalize decodo/source outcome parity between sourcing and resolver.
- Tighten cache-only mode usage under explicit policy flags only.
- Add/refresh tests validating transport outcome + reason-code behavior.

### Phase 3: Close evidence loop
- Execute Wave 6 Chunk C repetition checks (10x targeted module + one end-to-end gate run).
- Persist PASS/FAIL envelopes in artifacts.
- Regenerate `docs/artifacts/notion_sync_status.json` from current repo state.

### Phase 4: Coverage and stabilization
- Add focused tests for `abraxas/runtime/` and `abraxas/ers/` boundaries.
- Re-run targeted suites and confirm deterministic outputs.
- Update TODO list and move completed items to archive.


## ASCEND+ — six-chunk execution spine

- **Chunk A:** Runtime gate canonicalization guardrails (`tests/test_dozen_run_gate_runtime.py`).
- **Chunk B:** Behavioral guardrail coverage (`tests/test_online_decodo_flow.py`).
- **Chunk C:** Repetition proof loop (`N` pytest repetitions + `N`-run gate).
- **Chunk D:** TODO closure artifact regeneration (TODO marker scan + stub scan + taxonomy + notion sync).
- **Chunk E:** Verification pass (`tests/test_stub_taxonomy_artifact.py` + `scripts/verify_wave6_artifacts.py`).
- **Chunk F:** Runtime/ERS stabilization checks (`tests/test_runtime_infrastructure.py` + `tests/test_ers_invariance_gate.py`).

## CLEAR — done criteria

- Active TODO list contains only roadmap items or policy-intentional work.
- Decodo/source + adapter behavior emits deterministic, machine-readable outcomes.
- Repetition proof and sync artifacts are current and committed.
- Runtime/ERS coverage trend is increased and documented.

## SEAL

This plan keeps TODO handling measurable: scan -> prioritize -> execute -> prove -> sync.
