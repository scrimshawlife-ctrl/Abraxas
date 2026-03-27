# Notion ↔ Repo Execution Plan (Remaining Coding Tasks)

Date: 2026-03-27 (UTC)
Status: initiated

## ALIGN — repo-vs-notion reality check

### Verified signals

1. **Inventory/Notion checklist remains open administratively**
   - `python abraxas/governance/inventory_report.py` reports 46 runes + 3 overlays and emits unchecked Notion catch-up checklist entries.
   - Canon metadata remains `not_computable` because `PyYAML` is unavailable in current environment.

2. **Stub surface exists, but concentrated and classifiable**
   - `python scripts/scan_stubs.py --write` refreshed `tools/stub_index.json`.
   - Current scanner output: 23 P1 markers total, concentrated in:
     - Rune operators (18)
     - Interfaces/abstract contracts (2)
     - Other explicit NotImplemented surfaces (3)

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

## SEAL

This plan converts the Notion-vs-repo delta from narrative drift into a deterministic execution sequence with concrete evidence artifacts.
