# Notion Scan — Abraxas Subsystems vs Repo (Remaining Coding Tasks)

Date: 2026-03-27 (UTC)
Method: Re-validated prior Notion scan claims against current repository code paths and runtime behavior indicators.

## 1) Notion catch-up status (inventory-driven)

From `python abraxas/governance/inventory_report.py`:

- Runes discovered: 46
- Overlays discovered: 3
- Notion Catch-up checklist currently emits unchecked entries for all rune registry entries and overlay registry entries.
- Canon metadata remains `not_computable` in report output (`PyYAML unavailable`).

Implication: Notion sync remains administratively open for runes/overlays/canon metadata, independent of implementation status.

## 2) Repo comparison against prior Notion coding claims

## Claim status legend
- ✅ Resolved in codebase
- ⚠️ Partially true / reframed
- ❌ Still open

### 2.1 ABX-Runes acquisition layer stubs

- Prior claim: direct `/stub/*` paths + simulated stub packets still active in `abraxas/runes/operators/acquisition_layer.py`.
- Repo status: ✅ `/stub/*` path artifacts are no longer present; deterministic CAS-backed acquisition/cache flows are implemented.
- Residual: ⚠️ strict mode still raises `NotImplementedError` until live adapter integration is completed.

### 2.2 Invocation enforcement of stub operators

- Prior claim: `abraxas/runes/invoke.py` emits `stub_blocked` and raises `RuneStubError`.
- Repo status: ✅ true by design (governance safeguard, not a defect).
- Residual: none; keep as contract enforcement.

### 2.3 Bus runtime still stubbed

- Prior claim: `abx/bus/runtime.py` returns status `"stub"` replacement-needed envelope.
- Repo status: ✅ resolved; bus runtime now executes deterministic module pipeline and returns `output.status = "ok"`.

### 2.4 Chat runtime deterministic stub

- Prior claim: `abx/ui/chat_engine.py` still operates as deterministic stub.
- Repo status: ⚠️ comment still says "Deterministic stub", but runtime now uses bus process + capability invocations (`core.rendering.render_output`, `drift.orchestrator.analyze_text_for_drift`) under strict execution.
- Residual: comment debt only; behavior is no longer simple echo stub.

### 2.5 Kernel/oracle fallback stub in core path

- Prior claim: dispatcher routes fallback to `_stub_engine_adapter`.
- Repo status: ✅ resolved naming/path; current fallback is deterministic `_error_engine_adapter` envelope when kernel entrypoint is unavailable.
- Residual: ⚠️ `abraxas/core/stub_oracle_engine.py` still exists and should be either retired, isolated to tests, or explicitly wired only under test flags.

### 2.6 Neon-Genie integration

- Prior claim: `abraxas/aal/neon_genie_adapter.py` is "not yet integrated (stub mode)".
- Repo status: ⚠️ partially resolved; adapter performs real overlay runtime invocation (`check_overlay_available` + `invoke_overlay`) with deterministic fallback when unavailable.
- Residual: docstring/comment wording still references "internal stub"; should be renamed to fallback adapter semantics.

### 2.7 Upgrade-spine `patch_plan_stub` adapters

- Prior claim: `server/abraxas/upgrade_spine/adapters/*.py` return `patch_plan_stub(...)` flows.
- Repo status: ✅ resolved; no `patch_plan_stub` references remain, and adapters use `build_patch_plan(...)`.

### 2.8 Online sourcing/resolver + source adapters

- Prior claim: online resolver/sourcing and multiple source adapters remain stub-oriented.
- Repo status: ❌ still open.
  - `abx/online_sourcing.py` and `abx/online_resolver.py` still describe Decodo execution as stub/deferred.
  - `abraxas/sources/adapters/*` includes cache-only stubs (JPL, CLDR, NOAA, NIST, Tomsk, etc.).

## 3) Remaining coding task queue (repo-grounded)

Ordered by impact and dependency:

1. **Live source adapter implementation pass**
   - Replace cache-only source adapters with network-backed deterministic adapters + provenance envelopes.
2. **Decodo execution closure**
   - Move `abx/online_sourcing.py` / `abx/online_resolver.py` from stub/deferred notes to executable sourced flow with explicit policy gates.
3. **Kernel stub retirement policy**
   - Constrain `abraxas/core/stub_oracle_engine.py` to explicit test-only usage or remove if superseded by error envelope routing.
4. **Comment/semantic de-stub cleanup**
   - Remove stale "stub" wording in `abx/ui/chat_engine.py` and Neon-Genie internal helper naming/docs where behavior is live+fallback.
5. **Notion sync closure**
   - Mark completed chunk claims in Notion to prevent roadmap drift (bus runtime, acquisition paths, upgrade-spine planners).

## 4) Delta from earlier Notion scan

Resolved since earlier scan:
- Bus runtime de-stubbed.
- Upgrade-spine `patch_plan_stub` removed.
- Acquisition layer no longer emits `/stub/*` artifacts.
- Dispatcher fallback shifted from stub-engine naming to deterministic kernel-unavailable envelope.

Still open:
- Source adapter live integrations.
- Decodo execution closure.
- Stub-comment debt and legacy stub file retirement.
