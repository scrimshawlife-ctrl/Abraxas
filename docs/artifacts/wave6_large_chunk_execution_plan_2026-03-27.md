# Wave 6 Large-Chunk Execution Plan — 2026-03-27

Status: initiated

## OPEN — pressure map

Remaining pressure after Wave 5 is no longer raw TODO count; it is **naming/runtime coherence**, **determinism evidence loops**, and **Notion/repo execution rhythm**.

## ALIGN — large chunk sequence

### Chunk A — Runtime gate canonicalization (initiated)
- Canonicalize N-run gate entrypoint under `scripts/n_run_gate_runtime.py`.
- Retain legacy `scripts/dozen_run_gate_runtime.py` as compatibility shim.
- Keep behavior deterministic and output semantics unchanged.

### Chunk B — Behavioral guardrail coverage (initiated)
- Test CLI input gate (`--runs >= 1`) through `main()` path.
- Test persisted run-count note writes through patched persistence boundary.
- Test legacy shim mapping to canonical module.

### Chunk C — Repetition proof loop (queued)
- Execute target test module 10 consecutive runs pre-PR.
- Execute one end-to-end 10-run gate command and verify PASS envelope.

### Chunk D — TODO closure continuation (queued)
- Continue decodo/source lane hardening in acquisition + resolver paths.
- Emit updated evidence artifact tied to notion sync status.

## ASCEND — initiation marker

- Wave 6 initiated with Chunks A/B active in this commit window.
- Chunk C executes before PR publish gate.

## SEAL

Large chunks preserve ABX-Core compression: fewer moving names, stronger test provenance, stable execution rhythm.
