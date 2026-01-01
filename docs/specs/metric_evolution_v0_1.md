# Metric Evolution Track v0.1 — Specification

**Status**: Implemented
**Version**: 0.1
**Created**: 2025-12-26
**Purpose**: Safe, gated metric evolution via MW/AAlmanac proposals, sandbox testing, and stabilization

---

## Overview

**Metric Evolution Track** enables Abraxas to propose, test, and promote new metrics/operators/parameter tweaks based on observed deltas from domain subsystems.

**Core Innovation**: Every candidate requires sandbox proof and stabilization window before promotion. Params auto-apply; metrics/operators create implementation tickets.

---

## System Architecture

```
Domain Deltas → Candidate Generation → Sandbox Testing → Stabilization → Promotion
     ↓                ↓                      ↓                ↓             ↓
AALMANAC/MW     Rule-based           In-memory test    N consecutive    Action:
INTEGRITY       proposals            Score deltas      passes           - Param override
BACKTEST        Max 10/run           Pass criteria     Reset on fail    - Impl ticket
```

---

## Components

### 1. Source Vector Map Registry

**Purpose**: Discovery registry mapping semantic nodes to OSH allowlist sources.

**NOT a scraper**: Only maps topics to existing allowlist entries.

**Schema**: `data/vector_maps/source_vector_map_v0_1.yaml`

```yaml
nodes:
  - node_id: "ai_deepfake_policy"
    domain: "INTEGRITY"
    allowlist_source_ids: ["rss_nyt_tech", "rss_wired_security"]
    cadence_hint: "daily"
    narrative_affinity: ["N1_primary"]
    enabled: true
```

**Validation**:
- Node IDs unique
- Domains valid (INTEGRITY, PROPAGANDA, AALMANAC, MW)
- All source_ids exist in allowlist
- No duplicate sources per node

**API**: `abraxas/online/vector_map_loader.py`

```python
from abraxas.online.vector_map_loader import load_vector_map, validate_vector_map

vm = load_vector_map(path)
is_valid, errors = validate_vector_map(vm, allowlist_spec)
```

---

### 2. Candidate Generation

**Purpose**: Generate metric/operator/param_tweak candidates from domain deltas.

**Constraints**:
- Max 10 candidates per run
- Max 4 per source domain
- Deterministic rules (no ML)
- Must provide rationale + expected improvement

**Candidate Kinds**:
1. **METRIC**: New metric (e.g., "term_coupling")
2. **OPERATOR**: New SLANG operator (e.g., "semantic_distance")
3. **PARAM_TWEAK**: Parameter override (e.g., confidence threshold)

**Generation Rules**:

| Source | Delta | Candidate | Example |
|--------|-------|-----------|---------|
| AALMANAC | term_velocity > 0.8 | METRIC | term_coupling_deepfake |
| AALMANAC | frequency_spike > 3x | PARAM_TWEAK | frequency_damping_misinformation |
| MW | synthetic_saturation Δ > 0.15 | PARAM_TWEAK | ssi_dampening_multiplier |
| MW | cluster_split | METRIC | cluster_stability_X |
| INTEGRITY | SSI velocity > 0.10 | PARAM_TWEAK | confidence_threshold_H72H |
| INTEGRITY | trust_surface Δ < -0.20 | METRIC | trust_floor_metric |
| BACKTEST | 3+ MISS on trigger | PARAM_TWEAK | threshold_relax_X |

**Schema**: `abraxas/evolution/schema.py`

```python
class MetricCandidate(BaseModel):
    candidate_id: str
    kind: CandidateKind  # METRIC, OPERATOR, PARAM_TWEAK
    source_domain: SourceDomain  # AALMANAC, MW, INTEGRITY, BACKTEST
    name: str
    description: str
    rationale: str
    expected_improvement: Dict[str, Any]  # e.g., {"brier_delta": -0.05}
    target_horizons: List[str]  # e.g., ["H72H", "H30D"]
    protected_horizons: List[str]  # Cannot regress
    priority: int  # 1-10
```

**API**: `abraxas/evolution/candidate_generator.py`

```python
from abraxas.evolution.candidate_generator import generate_candidates_from_deltas

candidates = generate_candidates_from_deltas(
    aalmanac_deltas={"term_velocities": {"deepfake": {"velocity": 0.85}}},
    mw_deltas={"synthetic_saturation": {"delta": 0.18}},
    integrity_deltas={"ssi_trend": {"velocity": 0.12}},
    run_id="daily_run_001"
)
```

**Ledger**: `out/evolution_ledgers/candidates.jsonl` (hash-chained)

---

### 3. Sandbox Execution

**Purpose**: Test candidates against hindcast data before promotion.

**Safety**:
- All changes in-memory only (no disk writes)
- Requires historical data (no online fetching)
- Must prove improvement on target horizons
- Cannot regress protected horizons

**Workflow**:
1. Load candidate
2. **For PARAM_TWEAK**: Apply override in-memory, re-run backtest/forecast
3. **For METRIC/OPERATOR**: Validate spec only (implementation requires ticket)
4. Compare scores before/after
5. Check pass criteria
6. Return SandboxResult

**Pass Criteria**:
- Improvement ≥ 10% (configurable)
- No regressions > 2% on protected horizons (configurable)
- Cost increase ≤ 50% (configurable)

**Schema**: `abraxas/evolution/schema.py`

```python
class SandboxResult(BaseModel):
    sandbox_id: str
    candidate_id: str
    run_at: str
    hindcast_window_days: int
    cases_tested: int
    score_before: Dict[str, float]  # e.g., {"brier_avg": 0.25}
    score_after: Dict[str, float]   # e.g., {"brier_avg": 0.20}
    score_delta: Dict[str, float]   # e.g., {"brier_delta": -0.05}
    passed: bool
    pass_criteria: Dict[str, bool]
    failure_reasons: List[str]
```

**API**: `abraxas/evolution/sandbox.py`

```python
from abraxas.evolution.sandbox import run_candidate_sandbox

result = run_candidate_sandbox(candidate, run_id="test_run_001")

print(f"Passed: {result.passed}")
print(f"Score delta: {result.score_delta}")
```

**Ledger**: `out/evolution_ledgers/sandbox.jsonl` (hash-chained)

---

### 4. Stabilization Window

**Purpose**: Track consecutive sandbox passes to ensure stability.

**Requirements**:
- N consecutive passes required (default: 3)
- One failure resets counter
- Tracks full run history

**Schema**: `abraxas/evolution/schema.py`

```python
class StabilizationWindow(BaseModel):
    candidate_id: str
    window_size: int = 3
    consecutive_passes: int
    consecutive_failures: int
    run_history: List[Dict[str, Any]]

    def is_stable(self) -> bool:
        return self.consecutive_passes >= self.window_size
```

**Storage**: `data/evolution/stabilization_windows/{candidate_id}.json`

---

### 5. Promotion Gate

**Purpose**: Validate and promote candidates that pass stabilization.

**Validation**:
1. Check stabilization window (N consecutive passes)
2. Latest result must pass
3. At least one passing sandbox result

**Promotion Actions**:

| Kind | Action | Output |
|------|--------|--------|
| PARAM_TWEAK | Write to override file | `data/evolution/param_overrides.yaml` |
| METRIC | Create implementation ticket | `data/evolution/implementation_tickets/{ticket_id}.json` |
| OPERATOR | Create implementation ticket | `data/evolution/implementation_tickets/{ticket_id}.json` |

**Schema**: `abraxas/evolution/schema.py`

```python
class PromotionEntry(BaseModel):
    promotion_id: str
    candidate_id: str
    promoted_at: str
    kind: CandidateKind
    name: str
    action_type: str  # "param_override" or "implementation_ticket"
    action_details: Dict[str, Any]
    stabilization_window: Dict[str, Any]
    sandbox_results_summary: Dict[str, Any]
```

**API**: `abraxas/evolution/promotion_gate.py`

```python
from abraxas.evolution.promotion_gate import promote_candidate

promotion = promote_candidate(
    candidate,
    sandbox_results,
    promoted_by="promotion_gate_v0_1"
)

print(f"Action: {promotion.action_type}")
print(f"Details: {promotion.action_details}")
```

**Ledger**: `out/evolution_ledgers/promotions.jsonl` (hash-chained)

---

## Storage Structure

```
data/
  vector_maps/
    source_vector_map_v0_1.yaml           # Discovery registry
  evolution/
    candidates/                            # Individual candidate JSONs
      cand_{kind}_{domain}_{ts}_{hash}.json
    stabilization_windows/                 # Stabilization tracking
      {candidate_id}.json
    implementation_tickets/                # Manual implementation tasks
      ticket_{ts}_{hash}.json
    param_overrides.yaml                   # Auto-applied parameter tweaks

out/
  evolution_ledgers/
    candidates.jsonl                       # Hash-chained candidate log
    sandbox.jsonl                          # Hash-chained sandbox results
    promotions.jsonl                       # Hash-chained promotions
```

---

## Example Workflow

### Full Candidate Lifecycle

```python
from abraxas.evolution.candidate_generator import generate_candidates_from_deltas
from abraxas.evolution.sandbox import run_candidate_sandbox
from abraxas.evolution.promotion_gate import PromotionGate
from abraxas.evolution.store import EvolutionStore

# 1. Generate candidates from deltas
aalmanac_deltas = {
    "term_velocities": {"deepfake": {"velocity": 0.85, "frequency": 120}}
}

candidates = generate_candidates_from_deltas(
    aalmanac_deltas=aalmanac_deltas,
    run_id="daily_run_20251226"
)

# 2. Save candidate
store = EvolutionStore()
candidate = candidates[0]
store.save_candidate(candidate)
store.append_candidate_ledger(candidate)

# 3. Run sandbox (3 times for stabilization)
sandbox_results = []
for i in range(3):
    result = run_candidate_sandbox(candidate, run_id=f"run_{i}")
    store.append_sandbox_ledger(result)
    sandbox_results.append(result)

# 4. Check promotion eligibility
gate = PromotionGate(store=store)
can_promote, reasons = gate.can_promote(candidate, sandbox_results)

if can_promote:
    # 5. Promote
    promotion = gate.promote(candidate, sandbox_results)
    print(f"✓ Promoted: {promotion.promotion_id}")
    print(f"  Action: {promotion.action_type}")
else:
    print(f"✗ Cannot promote: {reasons}")
```

---

## Determinism Guarantees

✅ **Candidate Generation**: Deterministic rules, no randomness
✅ **Candidate IDs**: Hash-based from (kind, domain, timestamp)
✅ **Sandbox Execution**: Reproducible from hindcast data
✅ **Stabilization Tracking**: Exact consecutive pass/fail counting
✅ **Promotion Actions**: Deterministic file writes
✅ **Ledger Recording**: Hash-chained, canonical JSON

**Replayability**: Full pipeline reproducible from ledgers + deltas

---

## Safety Mechanisms

### 1. Bounded Generation
- Max 10 candidates per run
- Max 4 per source domain
- Prevents metric sprawl

### 2. Sandbox Proof
- Every candidate must improve scores in sandbox
- No promotion without evidence
- In-memory testing (no side effects)

### 3. Stabilization Window
- Requires N consecutive passes (default: 3)
- One failure resets counter
- Ensures stability over time

### 4. Protected Horizons
- Candidates cannot regress protected horizons
- Regression tolerance: 2% (configurable)
- Prevents short-term optimization at long-term cost

### 5. Manual Review for Complexity
- METRIC/OPERATOR → implementation tickets
- PARAM_TWEAK → auto-apply (lowest risk)
- Human review for high-impact changes

---

## Testing

**19 tests, all passing**

- `tests/test_evolution_system.py` (19 tests)
  - Vector map loading and validation
  - Candidate generation from all sources
  - Max limit enforcement
  - Store save/load operations
  - Ledger chain integrity
  - Sandbox execution (param tweak, metric, operator)
  - Pass criteria checking
  - Stabilization window tracking
  - Promotion gate validation
  - Override file creation
  - Ticket creation
  - Unstable candidate rejection

---

## Configuration

### Vector Map

**File**: `data/vector_maps/source_vector_map_v0_1.yaml`

```yaml
nodes:
  - node_id: "ai_deepfake_policy"
    domain: "INTEGRITY"
    allowlist_source_ids: ["rss_nyt_tech", "rss_wired_security"]
    cadence_hint: "daily"
    narrative_affinity: ["N1_primary"]
    enabled: true

settings:
  max_nodes_active: 10
  min_allowlist_sources_per_node: 1
  max_allowlist_sources_per_node: 5
```

### Sandbox Config

```python
SandboxConfig(
    hindcast_window_days=90,
    min_cases_required=5,
    improvement_threshold=10.0,  # 10% improvement required
    regression_tolerance=0.02,   # Allow 2% regression
    cost_multiplier_max=2.0      # Max 2x cost increase
)
```

### Promotion Criteria

```python
PromotionCriteria(
    require_stabilization=True,
    stabilization_window_size=3,       # 3 consecutive passes
    min_improvement_pct=10.0,          # 10% improvement
    allow_regressions=False,
    max_cost_increase_pct=50.0,
    auto_promote_param_tweaks=True,    # Auto-apply params
    auto_promote_metrics=False,        # Tickets for metrics
    auto_promote_operators=False       # Tickets for operators
)
```

---

## Rent Manifests

- `data/rent_manifests/metrics/source_vector_map_v0_1.yaml`
- `data/rent_manifests/metrics/candidate_generation_v0_1.yaml`
- `data/rent_manifests/metrics/sandbox_execution_v0_1.yaml`
- `data/rent_manifests/metrics/promotion_gate_v0_1.yaml`

All manifests declare:
- **Improves**: Specific capabilities (semantic_discovery, metric_adaptability, etc.)
- **Measurable by**: Concrete metrics (node_coverage, sandbox_pass_rate, etc.)
- **Thresholds**: Conservative start (registry loads, ledgers exist, etc.)

---

## Why This Is Non-Commodity

| Standard ML Platforms | Abraxas Evolution Track |
|-----------------------|-------------------------|
| Auto-tune hyperparams | Rule-based candidate generation |
| Black-box optimization | Full provenance (delta → candidate → sandbox → promotion) |
| No stability check | Stabilization window (N consecutive passes) |
| Instant deployment | Sandbox proof required |
| No audit trail | Hash-chained ledgers |
| Vulnerable to drift | Protected horizons + regression bounds |

**Audit Question**: "Why was parameter X changed to Y?"

**Abraxas Answer**: See `promotions.jsonl@promotion_id=promo_XYZ` for:
- Candidate rationale (from domain delta)
- Sandbox proof (3 consecutive passes, score deltas)
- Stabilization window (run history)
- Exact action taken (override file + value)

**Standard Platform Answer**: "Model decided."

---

## Evolution Path

### v0.1 (Implemented)
✅ Source vector map registry (discovery, not scraping)
✅ Rule-based candidate generation (AALMANAC, MW, Integrity, Backtest)
✅ Max 10 candidates/run, max 4/source
✅ In-memory sandbox testing
✅ Score delta comparison (before/after)
✅ Stabilization window (3 consecutive passes)
✅ Promotion actions (param override, implementation tickets)
✅ Hash-chained ledgers
✅ 19 comprehensive tests

### v0.2 (Future)
- Auto-generate candidates from MW cluster evolution
- Multi-horizon consistency validation
- Sandbox against live production replay
- Cost tracking (time/memory per candidate)
- A/B testing framework for promoted changes

### v0.3 (Future)
- Meta-evolution: evolve candidate generation rules
- Feedback loop: track promoted change impact
- Rollback mechanism for failed promotions
- Adaptive stabilization window (based on candidate risk)

---

**End of Specification**
