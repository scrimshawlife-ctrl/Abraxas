# Notion ↔ Repo Execution Plan (Remaining Coding Tasks)

Date: 2026-03-27 (UTC)
Status: wave_5_completed (2026-04-09)

## OPEN — rescan pulse (2026-03-27 follow-up)

Rescan objective: re-validate remaining Notion task pressure after Wave 4 and initiate the next coding closure.

### Fresh scan signals

1. **Runtime TODO marker in rune scaffold**  
   - Resolved in follow-up: no longer emitted by `rune_registry_gate.py`.
2. **Kernel stub retirement still open**  
   - `abraxas/core/stub_oracle_engine.py` remained env-gated but not scope-bounded.
3. **Source adapter / Decodo closure still partially open**  
   - `cache_only_stub` and fallback-heavy online paths still visible in repo scan outputs.

### Wave 5 tasks (ranked)

1. **Kernel stub scope-bound gate (initiated this commit)**
   - Require explicit allow + explicit scope (`test|dev`) for stub oracle execution.
2. **Adapter lane closure continuation**
   - Reduce default reliance on cache-only adapters; keep policy-tagged fallback only.
3. **Decodo/source live-path hardening**
   - Continue replacing deferred/stub semantics with explicit live/fallback/blocked envelopes.

## ALIGN — repo-vs-notion reality check

### Verified signals

1. **Inventory/Notion checklist remains open administratively**
   - `python abraxas/governance/inventory_report.py` reports 46 runes + 3 overlays and emits unchecked Notion catch-up checklist entries.
   - Canon metadata remains `not_computable` because `PyYAML` is unavailable in current environment.

2. **Stub surface exists, but concentrated and classifiable**
   - `python scripts/scan_stubs.py --write` refreshed `tools/stub_index.json`.
   - Current scanner output: 4 P1 markers total, concentrated in:
     - Rune operators (0)
     - Interfaces/abstract contracts (2)
     - Other explicit NotImplemented surfaces (2)

3. **Online source stack is partially live, partially fallback-oriented**
   - `abx/online_sourcing.py` already builds deterministic Decodo request envelopes and has direct-http/search/rss fallback routing.
   - `abx/online_resolver.py` already executes deterministic URL probing and anchor creation for `decodo/direct_http/search_lite/rss` providers.
   - `abraxas/sources/adapters/cache_only_stub.py` still exists and remains exported in adapter registry.

### Remaining coding tasks (repo-grounded)

1. **Adapter lane closure (highest impact)**
   - Reduce/remove `CacheOnlyAdapter` as default path where network-backed deterministic adapters already exist.
   - Add explicit policy gates and provenance reason codes when cache-only mode is used intentionally.

2. **Decodo execution hardening**
   - Unify Decodo availability/capability checks between sourcing and resolver path.
   - Add explicit transport outcome states (`executed_live`, `executed_fallback`, `blocked_policy`) to resolver report for Notion parity.

3. **Rune operator implementation triage**
   - Separate intentional abstract guards from true implementation gaps in `tools/stub_index.json` (scanner currently counts both).
   - Prioritize non-governance operator gaps that block strict execution runs.

4. **Notion closure automation**
   - Convert this plan + scanner output into machine-readable completion artifact so Notion updates are evidence-backed.

---

## ASCEND — execution plan

### Wave 1 (now → next commit window)
- Build a **gap taxonomy**: `intentional_abstract` vs `implementation_gap` vs `policy_block`.
- Add resolver outcome fields for decodo/fallback distinction.
- Add/extend tests validating new outcome semantics.

### Wave 2
- Replace cache-only adapter use-sites with network-first adapters where safe.
- Preserve deterministic fallback behavior with explicit provenance tags.

### Wave 3
- Burn down highest-value operator implementation gaps from triaged list.
- Keep strict-execution guardrails; remove accidental stubs, not governance constraints.

### Wave 4
- Emit Notion sync artifact (JSON/MD) directly from repo state.
- Mark completed Notion tasks with links to code/test evidence.

---

## INITIATION LOG (executed this session)

- Ran inventory report to verify current notion checklist pressure surface.
- Refreshed stub index (`tools/stub_index.json`) from live repository scan.
- Established phased execution sequence above and set status to **initiated**.
- Added resolver transport outcome semantics (`executed_live`, `executed_fallback`, `blocked_policy`) for Notion parity.
- Added Decodo capability envelope (`online_allowed`, `decodo_available`) to keep sourcing/resolver capability checks aligned.
- Added `scripts/build_stub_taxonomy_artifact.py` and emitted `docs/artifacts/notion_stub_taxonomy.json` (Wave 1 taxonomy artifact).
- Added regression tests for Decodo outcome semantics and taxonomy classification.
- Wave 2 advance: manifest discovery now supports explicit `cache_only_mode` policy gating with provenance reason codes.
- Wave 2 advance: default manifest retrieval path now prefers live bulk fetch and only falls back to cache on bulk failure.
- Wave 2 advance: offline execute-plan packets now stamp explicit cache-only policy reason codes.
- Wave 3 advance: burned down strict missing-input operator gaps for NO_CAUSAL_ASSERT / NO_DOMAIN_PRIOR / PROVENANCE_SEAL / TEMPORAL_NORMALIZE / TVM_FRAME with deterministic `not_computable_detail` envelopes.
- Wave 3 advance: refreshed `tools/stub_index.json` and reduced tracked stubs from 23 to 18.
- Wave 4 advance: emitted deterministic Notion sync artifact `docs/artifacts/notion_sync_status.json` from repo evidence.
- Wave 4 advance: additional operator-gap burn-down reduced tracked stubs from 18 to 11 and refreshed sync artifacts.
- Wave 4 advance: documentation + strict-envelope refinements reduced tracked stubs from 11 to 6.
- Wave 4 advance: acquisition-layer strict-mode envelopes removed final operator stub marker; tracked stubs now 5.
- Wave 4 advance: taxonomy classifier now treats detector/narrative abstract base stubs as intentional abstractions; implementation-gap count reduced to 1.
- Wave 4 advance: kernel unrouted fallback moved to deterministic not_computable envelope and wired additional handlers; tracked stubs now 4.
- Wave 4 completion: sync artifact now auto-resolves `status.wave` to `wave_4_completed` when actionable implementation/policy gaps are zero.
- Wave 5 initiation: tightened `stub_oracle_engine` gating to require explicit scope bounds (`ABRAXAS_STUB_ORACLE_SCOPE=test|dev`) in addition to allow-flag and added coverage tests.
- Wave 5 completion: adapter lane closure + decodo capability hardening + closure automation are now evidenced by `docs/artifacts/notion_next_steps.json` (`all_wave5_ranked_tasks_completed=true`) and `docs/artifacts/notion_sync_status.json` (`status.wave=wave_5_completed`).

## SEAL

This plan converts the Notion-vs-repo delta from narrative drift into a deterministic execution sequence with concrete evidence artifacts.
