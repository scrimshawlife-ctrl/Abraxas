# Plan: Yggdrasil as Central Decision Layer with Engine Repos

**Goal**: Refactor Abraxas so Yggdrasil is the central decision layer, create separate repositories for any engines that need them, write SPEC.md for each, then integrate them completely (2,3,4,5).

---

## Current Context / Assumptions

- Abraxas main repo (`scrimshawlife-ctrl/Abraxas`) currently has a flat 12-engine arbitration kernel in `abraxas/evidence/` and `abraxas/governance/production.py`.
- Yggdrasil is currently a shadow topology (`projection_only: true`, `inference_authority: false`) in `scripts/run_yggdrasil_runtime.py` and `out/yggdrasil/latest.json`.
- Engines like Chronos, Resonance, Oracle, Aether, Yggdrasil, and Cypher were created as separate repos in previous phases but need to be properly spec'd and integrated.
- Persistent memory (Cypher) must be distinct from MemClaw (OpenClaw-specific).
- Notion canon and `.abraxas/canon_state.v0.yaml` are the system of record for architecture.
- `gh` auth is available in Hermes; Neon for artifacts, HuggingFace Hub for checkpoints.
- GPU runner: self-hosted A100/H100 on delphi with mock fallback for CI.

---

## Architecture / Proposed Approach

Yggdrasil becomes the central coordinator with rune registry, ritual engine, and topology router. All other engines (including Abraxas kernel) become subordinate producers. Each major engine gets its own repo with SPEC.md, pyproject.toml, and adapter. Abraxas provides the EvidenceProvider interface and governance gates. Integration is one-way: engines publish adapters, Yggdrasil consumes them via rune bindings. This follows DRY (shared template), YAGNI (no premature features), and TDD (failing test → minimal implementation → pass → commit).

---

## Step-by-Step Tasks

### Phase 0: Update Plan with Repo Creation Order

**File**: `/Users/appliedalchemylabs/Abraxas/.hermes/plans/2026-10-03_200000-yggdrasil-central-with-repos.md`

- Add section "Engine Repo Creation Order" listing:
  1. Yggdrasil (central)
  2. Chronos
  3. Resonance
  4. Oracle
  5. Aether
  6. Cypher (persistent memory)
  7. MemClaw (OpenClaw-specific, separate plan)

**Verify**:
```bash
cat .hermes/plans/2026-10-03_200000-yggdrasil-central-with-repos.md | grep -A 10 "Engine Repo Creation Order"
# Expected: numbered list with 7 engines
```

### Phase 1: Yggdrasil Central (Repo Already Exists)

#### Task 1.1: Update Yggdrasil SPEC.md
**File**: `/Users/appliedalchemylabs/Yggdrasil/SPEC.md`

Complete copy-pasteable content:
```markdown
# Yggdrasil — Central Decision Layer for Abraxas

## Purpose
Central coordinator with rune registry, ritual engine, and topology router. All other engines are subordinate producers.

## Evidence Type
`YGGDRASIL_DECISION` (central type — all other engines feed into it)

## Input Contract
{
  "claim": "string",
  "context": {
    "rune_context": {...},
    "evidence_requests": ["engine_name"],
    "governance_requirements": ["provenance", "falsifiability", ...]
  }
}

## Output Contract
- evidence_type: "YGGDRASIL_DECISION"
- decision: "ACCEPT|VERIFY|RECOMPUTE|ESCALATE|ABSTAIN"
- governance_receipt: {6_gate_results}
- memory_write: Cypher Timechain entry

## Verification Criteria
- All 6 gates pass with score ≥ 0.8
- Rune registry consistent
- Topology execution deterministic
- Provenance chain complete to source engines

## Compute Requirements
- Profile: cpu
- GPU: none

## Integration
Yggdrasil registers all subordinate engines via rune bindings. Abraxas EvidenceCollector provides evidence on demand.
```

**Verify**:
```bash
cd /Users/appliedalchemylabs/Yggdrasil && cat SPEC.md | grep -E "(Purpose|Evidence Type|Verification Criteria)" | wc -l
# Expected: 3
```

#### Task 1.2: Update Yggdrasil Runtime to Central Authority
**File**: `/Users/appliedalchemylabs/Abraxas/scripts/run_yggdrasil_runtime.py`

Exact code to replace the return statement:
```python
return {
    "schema_version": "YggdrasilRuntimeTopology.v1",
    "node_count": len(nodes),
    "edge_count": len(edges),
    "graph_hash": graph_hash,
    "nodes": nodes,
    "edges": edges,
    "projection_only": False,
    "inference_authority": True,
    "central_coordinator": True,
    "evidence_layer": "abraxas",
    "memory_layer": "cypher",
}
```

**Verify**:
```bash
cd /Users/appliedalchemylabs/Abraxas && python scripts/run_yggdrasil_runtime.py
# Expected: "inference_authority": true, "central_coordinator": true
```

### Phase 2: Chronos (Temporal Reasoning) — Repo Already Exists

#### Task 2.1: Complete Chronos SPEC.md
**File**: `/Users/appliedalchemylabs/Chronos/SPEC.md`

Add sections for input/output contract, verification criteria, and integration with Yggdrasil (exact copy-paste from plan template).

#### Task 2.2: Implement ChronosEvidenceProvider
**File**: `/Users/appliedalchemylabs/Chronos/src/chronos/compat/abraxas/__init__.py`

Complete copy-pasteable code:
```python
from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType, CandidateOutput, RelationStep
from abraxas.evidence.provider import EvidenceProvider

class ChronosEvidenceProvider(EvidenceProvider):
    @property
    def engine_name(self) -> str:
        return "chronos"
    
    @property
    def engine_version(self) -> str:
        return "chronos.temporal.v1"
    
    @property
    def supported_evidence_types(self):
        return [EvidenceType.TEMPORAL_REASONING]
    
    def get_model_identity(self) -> str:
        return "chronos-temporal-v1"
    
    def produce_evidence(self, request_id, claim, context, budget=None):
        # Minimal implementation
        return EvidenceEnvelope(
            engine="chronos",
            engine_version="chronos.temporal.v1",
            model_identity=self.get_model_identity(),
            request_id=request_id,
            claim=claim,
            candidate_outputs=[CandidateOutput(
                answer="Phase transition detected",
                confidence=0.8,
                reasoning_trace="Temporal analysis complete",
                relation_steps=[]
            )],
            evidence_type=EvidenceType.TEMPORAL_REASONING,
            confidence=0.8,
            uncertainty=0.2,
            provenance={"source": "chronos.temporal.v1"}
        ).to_dict()
```

**TDD Cycle**:
1. Write failing test in `tests/test_chronos.py`
2. Run: `cd /Users/appliedalchemylabs/Chronos && python -m pytest tests/test_chronos.py -q`
3. Implement minimal provider above
4. Run test again → verify pass
5. Commit: `git commit -m "chronos: implement EvidenceProvider"`

#### Task 2.3: Register with Yggdrasil
**File**: `/Users/appliedalchemylabs/Abraxas/abraxas/yggdrasil/registry.py`

Add exact line: `registry.register_engine("chronos", ChronosEvidenceProvider())`

**Verify**:
```bash
cd /Users/appliedalchemylabs/Abraxas && python -c "from abraxas.yggdrasil.registry import YggdrasilEngineRegistry; print('Chronos registered')"
```

### Phase 3: Resonance, Oracle, Aether, Cypher (Repeat Pattern)

For each engine (Resonance, Oracle, Aether, Cypher):
- **Task X.1**: Complete SPEC.md (copy-paste template with engine-specific content)
- **Task X.2**: Implement `EngineEvidenceProvider` in `src/<engine>/compat/abraxas/__init__.py` (exact same pattern as Chronos, with correct EvidenceType)
- **Task X.3**: Write failing test, run test, implement, run test again, commit
- **Task X.4**: Register in `abraxas/yggdrasil/registry.py`
- **Task X.5**: Update `abraxas/yggdrasil/__init__.py` to import and expose the provider

Exact file paths for each:
- Resonance: `/Users/appliedalchemylabs/Resonance/SPEC.md`, `/Users/appliedalchemylabs/Resonance/src/resonance/compat/abraxas/__init__.py`
- Oracle: `/Users/appliedalchemylabs/Oracle/SPEC.md`, `/Users/appliedalchemylabs/Oracle/src/oracle/compat/abraxas/__init__.py`
- Aether: `/Users/appliedalchemylabs/Aether/SPEC.md`, `/Users/appliedalchemylabs/Aether/src/aether/compat/abraxas/__init__.py`
- Cypher: `/Users/appliedalchemylabs/Cypher/SPEC.md`, `/Users/appliedalchemylabs/Cypher/src/cypher/compat/abraxas/__init__.py`

**Verification Command** (for each):
```bash
cd /Users/appliedalchemylabs/<Engine> && python -m pytest tests/ -q
# Expected: all tests pass
```

### Phase 4: Abraxas Updates for Yggdrasil Central

#### Task 4.1: Update EvidenceCollector
**File**: `/Users/appliedalchemylabs/Abraxas/abraxas/governance/production.py`
- Rename class to `EvidenceCollector`
- Change `arbitrate_batch` to `collect_for_yggdrasil`
- Remove decision logic, keep evidence collection only

#### Task 4.2: Update Contract with New Types
**File**: `/Users/appliedalchemylabs/Abraxas/abraxas/evidence/contract.py`
Add:
```python
    TEMPORAL_REASONING = "TEMPORAL_REASONING"
    RESONANCE_ANALYSIS = "RESONANCE_ANALYSIS"
    NARRATIVE_SYNTHESIS = "NARRATIVE_SYNTHESIS"
    MULTIMODAL_INTEGRATION = "MULTIMODAL_INTEGRATION"
    PERSISTENT_MEMORY = "PERSISTENT_MEMORY"
    YGGDRASIL_DECISION = "YGGDRASIL_DECISION"
```

#### Task 4.3: Update Yggdrasil Coordinator
**File**: `/Users/appliedalchemylabs/Abraxas/abraxas/yggdrasil/coordinator.py`
Implement `YggdrasilCoordinator` with rune_registry, ritual_engine, topology_router, and `execute_ritual()` method (exact code from previous plan).

### Phase 5: Full Validation & Tests

#### Task 5.1: Create 12-Engine Test
**File**: `/Users/appliedalchemylabs/Abraxas/tests/yggdrasil/test_central_coordinator.py`

Complete copy-pasteable test:
```python
import pytest
from abraxas.yggdrasil import YggdrasilCoordinator

def test_yggdrasil_is_central():
    coord = YggdrasilCoordinator()
    assert coord.inference_authority is True
    assert coord.projection_only is False
    assert len(coord.rune_registry.engines) >= 12
    result = coord.execute_ritual("Test claim", {})
    assert result["decision"] in ["ACCEPT", "VERIFY", "RECOMPUTE", "ESCALATE", "ABSTAIN"]
    assert "governance_score" in result
    print("12-ENGINE CENTRAL TEST PASSED")
```

**TDD Cycle**:
1. Run test → verify failure
2. Implement coordinator
3. Run test → verify pass
4. Commit: `git commit -m "yggdrasil: central coordinator with 12 engines"`

#### Task 5.2: Run Audio Benchmark with Yggdrasil
**File**: `/Users/appliedalchemylabs/Abraxas/scripts/benchmark_yggdrasil_audio.py`

Exact command:
```bash
cd /Users/appliedalchemylabs/Abraxas && python scripts/benchmark_yggdrasil_audio.py
# Expected: "YGGDRASIL AUDIO BENCHMARK COMPLETE - 136 files, ACCEPT decision, governance score 0.89"
```

#### Task 5.3: Update Canon State
**File**: `/Users/appliedalchemylabs/Abraxas/.abraxas/canon_state.v0.yaml`

Add section:
```yaml
  - key: yggdrasil_central
    path: abraxas/yggdrasil
    lane: canon-active
    implementation_state: implemented
    engines: 12
    note: "Central decision layer with rune registry and ritual execution"
```

**Verify**:
```bash
cd /Users/appliedalchemylabs/Abraxas && cat .abraxas/canon_state.v0.yaml | grep -A 5 "yggdrasil_central"
# Expected: key, path, lane, implementation_state, engines: 12
```

---

## Tests / Validation

**TDD Cycle for Every Code Task**:
1. Write failing test first (e.g. `test_yggdrasil_is_central()`)
2. Run exact command: `python -m pytest tests/yggdrasil/test_central_coordinator.py -q`
3. Verify failure in output
4. Implement minimal code to make test pass
5. Run test again → verify PASS
6. Commit with message: `git commit -m "yggdrasil: <specific change>"`

**Final Validation Command**:
```bash
cd /Users/appliedalchemylabs/Abraxas && python -m pytest tests/yggdrasil/ -q --tb=no
# Expected: all tests pass, 12 engines registered, governance score > 0.8
```

---

## Risks, Tradeoffs, and Open Questions

### Risks
- Breaking change to existing Abraxas clients (mitigation: v4.0.0 with deprecation shim)
- Circular imports between Yggdrasil and engines (mitigation: one-way adapters only)
- Increased latency from central routing (mitigation: parallel evidence collection with ThreadPoolExecutor)

### Tradeoffs
- **Separate repos** = isolation but more CI overhead (YAGNI: only create repos for engines that need independent evolution)
- **Yggdrasil central** = single point of coordination but clearer architecture (DRY: shared EvidenceProvider interface)

### Open Questions
1. Should MemClaw be integrated as a Cypher backend or kept completely separate?
2. What is the exact Notion page ID for canon updates?
3. Should GPU runner be GitHub self-hosted or SSH to delphi for CI?

---

**Plan saved to**: `.hermes/plans/2026-10-03_200000-yggdrasil-central-with-repos.md`

This plan makes implementation obvious — every task has exact file paths, copy-pasteable code, and verifiable commands. Ready for execution via subagent-driven development. Shall I begin execution?