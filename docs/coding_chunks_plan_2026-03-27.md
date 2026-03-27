# Abraxas Coding Chunk Plan (Start)

Date: 2026-03-27 (UTC)
Purpose: Execute backlog in large implementation chunks to reduce drift and preserve deterministic progress.

## Chunk Architecture

### Chunk 1 — Runtime Core De-stub (COMPLETED)
Scope:
- Replace `abx/bus/runtime.py` stub processing with deterministic module pipeline.
- Keep interface compatibility for `abx/ui/chat_engine.py` (`frame.meta.frame_id`, `frame.output.message`).
- Add targeted unit tests for determinism + module selection behavior.

Acceptance Gate:
- No `"status": "stub"` bus output for standard payloads.
- Same payload -> same frame id + same output.
- Explicit `selected_modules` respected and ordered deterministically.

### Chunk 2 — Rune Acquisition Operators (IN PROGRESS)
Scope:
- Replace `abraxas/runes/operators/acquisition_layer.py` stub IO paths and simulated responses.
- Wire real adapter/storage hooks with deterministic manifest-only behavior.

Acceptance Gate:
- No `/stub/*` paths emitted.
- Operators pass strict execution without `RuneStubError` for acquisition family.

### Chunk 3 — Overlay Runtime Integration (IN PROGRESS)
Scope:
- Complete Neon-Genie external overlay wiring (`abraxas/aal/neon_genie_adapter.py`).
- Remove "stub mode" runtime branch for configured deployments.

Acceptance Gate:
- Overlay availability + invocation path succeeds when configured.
- Deterministic fallback remains explicit when overlay unavailable.

### Chunk 4 — Kernel Fallback De-stub (IN PROGRESS)
Scope:
- Reduce default dependency on `abraxas/core/stub_oracle_engine.py` in dispatcher paths.
- Ensure production oracle pipeline is default route under normal config.

Acceptance Gate:
- Stub oracle path only used in explicit test/fallback mode.

### Chunk 5 — Upgrade Spine Adapters Activation (COMPLETED)
Scope:
- Replace `patch_plan_stub(...)` pathways in upgrade-spine adapters with live plan builders.

Acceptance Gate:
- Shadow/Evogate/Rent/Drift adapters emit real patch plans under valid input.

### Chunk 6 — Coverage + Drift Hardening (COMPLETED)
Scope:
- Expand tests for runtime + ERS priority modules.
- Burn down remaining placeholder comments in non-critical paths.

Acceptance Gate:
- Meaningful coverage increase for runtime + ERS modules and passing targeted suites.

## Execution Order
1. Chunk 1 (start now)
2. Chunk 2
3. Chunk 3
4. Chunk 4
5. Chunk 5
6. Chunk 6


## Progress Log
- 2026-03-27: Chunk 1 completed (deterministic bus runtime + tests).
- 2026-03-27: Chunk 2 started (acquisition de-stub, CAS cache index, perf/compress compatibility hardening).
- 2026-03-27: Added regression tests for perf ledger serialization compatibility and zstd→gzip decompression fallback.
- 2026-03-27: Chunk 3 started with deterministic Neon-Genie fallback generation path (no stub-mode null outputs).

- 2026-03-27: Chunk 4 started with deterministic kernel-unavailable envelope replacing silent stub fallback in dispatcher.
- 2026-03-27: Chunk 5 started by replacing upgrade-spine adapter patch_plan_stub outputs with live patch-plan operations.
- 2026-03-27: Chunk 6 started with coverage hardening for upgrade-spine live patch-plan operations.
- 2026-03-27: Removed final patch_plan_stub helper; upgrade-spine now uses build_patch_plan exclusively.
- 2026-03-27: Added de-stub regression guard test for critical files (blocks /stub/, stub mode, patch_plan_stub reintroduction).
- 2026-03-27: Added deterministic tests for acquisition cache-index replay and patch-plan builder plan_id stability.
- 2026-03-27: Completed chunk 6 hardening gates (de-stub regression guard + acquisition index determinism + patch-plan determinism tests).
- 2026-03-27: Aligned acquisition cache index path to CAS root via ABRAXAS_ROOT-aware layout helpers.

- 2026-03-27: Initiated Notion↔Repo closure track; refreshed `tools/stub_index.json` and created `docs/notion_execution_plan_2026-03-27.md` with Wave 1-4 sequencing.
