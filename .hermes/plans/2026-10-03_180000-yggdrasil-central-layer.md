# Plan: Yggdrasil as Central Decision Layer — Architecture Refactor

**Goal**: Refactor Abraxas architecture so Yggdrasil (rune registry + ritual engine + topology router) is the true central decision layer, with the 12-engine evidence system as subordinate producers.

---

## Current Architecture Issues

1. **Abraxas ProductionOrchestrator** acts as flat peer-arbitrator for 12 engines
2. **Yggdrasil** is relegated to shadow projection (`projection_only: true`, `inference_authority: false`)
3. **Rune registry** exists but isn't the coordination authority
4. **Ritual execution pipeline** (`ritual_execution` in registry.json) is defined but not driven by Yggdrasil

---

## Target Architecture

### Yggdrasil (Central Coordinator)
- **Rune Registry** — Source of truth for all symbolic state
- **Ritual Engine** — Drives `ritual_execution` pipeline (runes → engines → storage)
- **Topology Router** — `audit → hash → validate → route` with `inference_authority: true`
- **Evidence Collection** — Pulls from 12 engines as subordinate producers

### Abraxas Kernel (Subordinate)
- **Evidence Producers** — 12 engines produce `EvidenceEnvelope` for Yggdrasil
- **Verifiers** — Quality checks for Yggdrasil consumption
- **Governance** — 6-gate system feeds Yggdrasil, doesn't decide

### 12 Engines (Subordinate Producers)
- Register with Yggdrasil rune registry
- Produce evidence on demand from Yggdrasil ritual engine
- No autonomous arbitration

---

## Step-by-Step Tasks

### Phase 1: Yggdrasil Core Upgrade

#### Task 1.1: Update Yggdrasil Topology to Central Authority
**File**: `/Users/appliedalchemylabs/Abraxas/scripts/run_yggdrasil_runtime.py`
- Change `inference_authority: true`
- Change `projection_only: false`
- Add `central_coordinator: true`
- Add `evidence_layer: "abraxas"` field

**Verify**:
```bash
cd /Users/appliedalchemylabs/Abraxas && python scripts/run_yggdrasil_runtime.py
# Expected: inference_authority=true, central_coordinator=true
```

#### Task 1.2: Create Yggdrasil Central Coordinator Module
**File**: `/Users/appliedalchemylabs/Abraxas/abraxas/yggdrasil/__init__.py`
- `YggdrasilCoordinator` class with:
  - `rune_registry` — canonical rune state
  - `ritual_engine` — drives `ritual_execution` pipeline
  - `topology_router` — audit→hash→validate→route
  - `evidence_collector` — pulls from 12 engines
  - `governance_hook` — receives 6-gate results

**Verify**:
```bash
cd /Users/appliedalchemylabs/Abraxas && python -c "from abraxas.yggdrasil import YggdrasilCoordinator; print('OK')"
```

#### Task 1.3: Update Yggdrasil Registry Entry
**File**: `/Users/appliedalchemylabs/Abraxas/.abraxas/registry.json`
- Update `"runes"` module to include `central_coordinator: true`
- Add `yggdrasil_central` module with full authority
- Update `ritual_execution` pipeline to be Yggdrasil-driven

---

### Phase 2: Abraxas Kernel Demotion

#### Task 2.1: Rename ProductionOrchestrator → EvidenceCollector
**File**: `/Users/appliedalchemylabs/Abraxas/abraxas/governance/production.py`
- Rename class `ProductionOrchestrator` → `EvidenceCollector`
- Remove arbitration logic (keep evidence collection only)
- Add `collect_for_yggdrasil(claim, context)` method
- Output: list of `EvidenceEnvelope` for Yggdrasil consumption

#### Task 2.2: Update 12 Engine Registrations
**File**: `/Users/appliedalchemylabs/Abraxas/abraxas/governance/production.py`
- Engines register with `YggdrasilCoordinator.rune_registry`
- EvidenceCollector gets engines from Yggdrasil, not local registry

#### Task 2.3: Remove Direct Arbitration
**File**: `/Users/appliedalchemylabs/Abraxas/abraxas/governance/production.py`
- Remove `arbitrate()`, `arbitrate_batch()` from EvidenceCollector
- Remove `SixGateGovernor` from EvidenceCollector (Yggdrasil handles governance)
- Keep 6-gate as verification step for evidence quality

---

### Phase 3: Engine Re-registration

#### Task 3.1: Update All 12 Engine Adapters
**Files**: Each engine's `compat/abraxas/__init__.py`
- Add `register_with_yggdrasil(yggdrasil_coordinator)` method
- Remove direct `ProviderRegistry` registration
- Engine produces evidence only when Yggdrasil requests

#### Task 3.2: Create Yggdrasil Engine Registry
**File**: `/Users/appliedalchemylabs/Abraxas/abraxas/yggdrasil/registry.py`
- `YggdrasilEngineRegistry` — canonical registry
- Engines register via rune-binding
- Supports dynamic engine discovery

---

### Phase 4: Pipeline Integration

#### Task 4.1: Yggdrasil-Driven Ritual Execution
**File**: `/Users/appliedalchemylabs/Abraxas/abraxas/yggdrasil/ritual.py`
- `RitualEngine.execute_ritual(claim, context)`:
  1. Run rune ritual (get today's runes)
  2. Yggdrasil topology: audit → hash → validate → route
  3. For each engine in topology: request evidence
  4. Collect evidence → 6-gate verification
  5. Route to storage / next stage

#### Task 4.2: Update pipeline in registry.json
**File**: `/Users/appliedalchemylabs/Abraxas/.abraxas/registry.json`
- `ritual_execution` steps driven by Yggdrasil
- Remove standalone `abraxas` module as decision maker
- Add `yggdrasil_central` as orchestrator

---

### Phase 5: Cypher Memory Integration

#### Task 5.1: Cypher as Yggdrasil Memory Layer
**File**: `/Users/appliedalchemylabs/Abraxas/abraxas/yggdrasil/memory.py`
- `CypherMemoryLayer` integrates with Yggdrasil topology
- Memory writes go through Yggdrasil governance
- Ritual history stored in Cypher Timechain

---

### Phase 6: Tests & Validation

#### Task 6.1: Yggdrasil Central Test
**File**: `/Users/appliedalchemylabs/Abraxas/tests/yggdrasil/test_central_coordinator.py`
```python
def test_yggdrasil_is_central():
    coord = YggdrasilCoordinator()
    assert coord.inference_authority == True
    assert coord.projection_only == False
    assert len(coord.rune_registry.engines) == 12
```

#### Task 6.2: Full Pipeline Test
**File**: `/Users/appliedalchemylabs/Abraxas/tests/yggdrasil/test_full_ritual.py`
```python
def test_full_ritual_execution():
    coord = YggdrasilCoordinator()
    result = coord.execute_ritual("Test claim", {"domain": "audio"})
    assert result.decision in ["ACCEPT", "VERIFY", "RECOMPUTE", "ESCALATE", "ABSTAIN"]
    assert result.yggdrasil_topology.graph_hash
    assert len(result.evidence_collected) == 12
```

#### Task 6.3: Audio Benchmark with Yggdrasil
Run existing audio benchmark but driven by Yggdrasil ritual engine.

---

## Risks & Tradeoffs

| Risk | Mitigation |
|------|------------|
| Breaking existing Abraxas API | Version bump to v4.0.0; maintain backwards compat shim |
| Engine adapter changes | Do one engine at a time; keep Abraxas EvidenceCollector as fallback during transition |
| Ritual execution latency | Parallelize evidence collection; cache rune rituals |
| Governance integration | Yggdrasil subscribes to 6-gate events; doesn't replace them |

---

## Execution Order

```
Phase 1 (Yggdrasil Core) → Phase 2 (Abraxas Demotion) → Phase 3 (Engine Re-reg) 
→ Phase 4 (Pipeline Integration) → Phase 5 (Cypher) → Phase 6 (Tests)
```

Each phase produces working increment.

---

## Open Questions

1. **Backwards compatibility** — Keep old `ProductionOrchestrator` as deprecated shim?
2. **Rune ritual source** — Use existing `scripts/run_yggdrasil_runtime.py` or TypeScript `runes.ts`?
3. **Real-time requirements** — Does Yggdrasil need streaming or batch is sufficient?

---

## Next Action

Execute Phase 1 (Yggdrasil Core Upgrade) first.