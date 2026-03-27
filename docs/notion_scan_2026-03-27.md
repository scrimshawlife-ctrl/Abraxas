# Notion Scan — Abraxas Subsystems Needing Coding

Date: 2026-03-27 (UTC)
Scope: Subsystems, ABX-Runes, runtime surfaces that are still stubbed/placeholder or flagged as active roadmap work.

## 1) Notion catch-up status (inventory-driven)

From `python abraxas/governance/inventory_report.py`:

- Runes discovered: 46
- Overlays discovered: 3
- Notion Catch-up checklist currently emits unchecked entries for all rune registry entries and overlay registry entries.
- Canon metadata is `not_computable` because `PyYAML` is unavailable in this environment.

Implication: Notion documentation sync appears incomplete (or intentionally open) across runes/overlays and canon metadata.

## 2) ABX-Runes that still need coding attention

### 2.1 Direct stub implementation still present

- `abraxas/runes/operators/acquisition_layer.py`
  - Contains explicit stub paths and simulated adapter responses (`/stub/raw`, `/stub/parsed`, `{"stub": ...}`).
  - Includes comments indicating placeholder behavior for bulk fetch/manifest candidates.

### 2.2 Runtime enforcement for stubbed rune operators

- `abraxas/runes/invoke.py`
  - Raises `RuneStubError` and emits `stub_blocked` statuses when operators/contracts are stubbed.

Implication: ABX-Runes contract layer is enforcing correctness, but at least one operator family (acquisition layer) still needs full implementation wiring.

## 3) Runtime surfaces still needing coding

### 3.1 Bus runtime remains a stub

- `abx/bus/runtime.py`
  - Module-level docstring and functions identify this runtime as stubbed.
  - `process_payload` returns status `"stub"` and a replacement-needed message.

### 3.2 Chat runtime uses deterministic stub

- `abx/ui/chat_engine.py`
  - Current behavior noted as deterministic stub using pipeline payload echo-style behavior.

### 3.3 Kernel/oracle fallback stub still active in core path

- `abraxas/core/stub_oracle_engine.py`
  - Contains explicit notes to replace stub with real oracle output.
- `abraxas/kernel/dispatcher.py`
  - Routes to `_stub_engine_adapter` for fallback paths.

Implication: Core runtime contracts exist, but production-grade runtime behavior is still partially scaffolded in bus/chat/oracle fallback layers.

## 4) Subsystems still needing coding (high-signal list)

- `abraxas/aal/neon_genie_adapter.py`
  - Reports `"Neon-Genie overlay not yet integrated (stub mode)"` and contains internal stub invocation.
- `server/abraxas/upgrade_spine/adapters/*.py`
  - Multiple adapters return `patch_plan_stub(...)` flows (shadow/evogate/rent/drift).
- `abx/online_resolver.py` and `abx/online_sourcing.py`
  - Decodo execution/sourcing still marked as stub-oriented in current implementation comments.
- `abraxas/sources/adapters/*.py`
  - Several adapters are cache-only stubs (JPL/CLDR/NOAA/NIST/Tomsk).

## 5) Cross-check against repo roadmap doc

`CLAUDE.md` indicates:

- Active work still includes roadmap features (`Resonance Narratives`, `UI Dashboard`, `Multi-Domain Analysis expansion`).
- Technical debt still open: remaining placeholder comments + expanding test coverage.
- Also notes 4 remaining ABX-Runes coupling exceptions in `abx/cli.py` (documented as acceptable CLI composition imports).

Implication: Even after major migrations, runtime maturity and feature completeness are still in-progress.

## 6) Suggested next coding pass (ordered)

1. Replace acquisition-layer rune stubs with real adapter/storage wiring.
2. Replace bus runtime stub (`abx/bus/runtime.py`) with deterministic production path + tests.
3. Complete Neon-Genie external overlay integration to remove stub mode.
4. Eliminate stub oracle fallback from default kernel execution path.
5. Convert upgrade-spine `patch_plan_stub` adapters into live planners.
6. Close remaining placeholder/test-coverage debt in runtime + ERS modules.

