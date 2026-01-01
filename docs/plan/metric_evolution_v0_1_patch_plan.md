# Metric Evolution Track v0.1 — Patch Plan

**Status**: Active Development
**Version**: 0.1
**Created**: 2025-12-26
**Purpose**: Safe, gated dynamic metric evolution via sandbox testing and stabilization

---

## Doctrine

**"Metrics are hypotheses. Promotion requires proof."**

**Metric Evolution Track** = Closed-loop system for discovering, testing, and promoting new metrics/operators:

1. **Propose**: MW/AAlmanac identify patterns → generate metric candidates
2. **Sandbox**: Test candidates via hindcast/backtest → measure score deltas
3. **Gate**: Require score improvement + no regressions + stabilization window
4. **Promote**: Approved candidates → parameter overrides OR implementation tickets

**Non-Negotiable**: No candidate touches production without sandbox proof + stabilization.

---

## Where Evolution Fits in Pipeline

```
Existing Spine:
SRR → SMEM/SIW → OSH → Domain Ledgers → τ/MW/Integrity/AAlmanac
                                ↓
                            FBE Update → Backtest → Scoreboard
                                ↓
                        Active Learning (failures → proposals)

NEW Addition (Metric Evolution):
MW/AAlmanac Deltas
        ↓
   [Candidate Generator]  ← Pattern recognition
        ↓
   Candidate Proposals (max 10/run)
        ↓
   [Sandbox Executor]  ← Hindcast/backtest with overrides
        ↓
   Score Delta Comparison (before/after)
        ↓
   [Promotion Gate]  ← Stabilization window (3 consecutive runs)
        ↓
   Parameter Overrides OR Implementation Tickets
```

**Integration Points**:
1. **After Domain Ledgers**: Read MW/AAlmanac deltas to propose candidates
2. **Sandbox**: Reuses backtest infrastructure + scoreboard metrics
3. **Promotion**: Writes to `data/forecast/overrides/` OR creates tickets
4. **Scheduler**: New steps after `score_forecasts`

---

## Candidate Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                   METRIC EVOLUTION TRACK                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  MW/AAlmanac Delta (pattern detected)                       │
│         ↓                                                    │
│  Candidate Proposal (hypothesis)                            │
│         ↓                                                    │
│  Sandbox Testing (before/after scores)                      │
│         ↓                                                    │
│  Score Delta Evaluation (improvement? regressions?)         │
│         ↓                                                    │
│  Stabilization Window (3 consecutive runs pass)             │
│         ↓                                                    │
│  Promotion Gate (strict criteria)                           │
│         ↓                                                    │
│  IF param_tweak: Write override file                        │
│  IF metric/operator: Create implementation ticket           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Candidate States

1. **PROPOSED**: Generated from delta, not yet sandboxed
2. **SANDBOX_PASS**: Passed initial sandbox (score improvement)
3. **SANDBOX_FAIL**: Failed sandbox (no improvement or regression)
4. **STABILIZING**: Passed initial, awaiting N consecutive runs
5. **APPROVED**: Passed stabilization, ready for promotion
6. **PROMOTED**: Applied to production (param override) OR ticket created (metric/operator)
7. **REJECTED**: Failed stabilization or promotion gate

---

## Source Vector Map Registry

### Purpose

**NOT a scraper** - a registry of "where to look" for discovery.

Maps semantic nodes (topics/themes) to OSH allowlist sources:
- **Discovery**: "What sources relate to AI policy?"
- **Coverage**: "Which narratives/segments does this source inform?"
- **Cadence**: "How often should we check this?"

### Schema

**File**: `data/vector_maps/source_vector_map_v0_1.yaml`

```yaml
nodes:
  - node_id: "ai_deepfake_policy"
    domain: "INTEGRITY"
    narratives: ["N1_primary", "N2_counter"]
    segments: ["core", "peripheral"]
    tags: ["deepfake", "policy", "verification"]
    allowlist_source_ids: ["rss_nyt_tech"]  # References OSH allowlist
    cadence_hint: "daily"
    notes: "Structural + institutional sources for long-horizon regime updates"

  - node_id: "slang_emergence_stream"
    domain: "AALMANAC"
    narratives: ["N2_counter"]
    segments: ["core"]
    tags: ["slang", "meme", "lexicon"]
    allowlist_source_ids: []  # Often manual offline entries
    cadence_hint: "daily"
    notes: "Online sources only via allowlist exports"

  - node_id: "propaganda_coordination"
    domain: "INTEGRITY"
    narratives: ["N1_primary"]
    segments: ["core"]
    tags: ["propaganda", "coordination", "inauthentic"]
    allowlist_source_ids: ["rss_security_blogs"]
    cadence_hint: "weekly"
    notes: "Threat intelligence + research publications"
```

**Validation**:
- `node_id` unique
- `domain` in known set (MW/AALMANAC/INTEGRITY/TAU/etc.)
- `allowlist_source_ids` reference existing OSH sources (if provided)

---

## Candidate Types

### MetricCandidate

```python
class CandidateKind(Enum):
    METRIC = "metric"              # New metric formula
    OPERATOR = "operator"          # New operator/transform
    PARAM_TWEAK = "param_tweak"    # Parameter adjustment

class MetricCandidate:
    candidate_id: str              # Deterministic hash
    kind: CandidateKind
    title: str                     # "Long-horizon SSI dampening increase"
    description: str               # Full rationale

    proposed_by: str               # "AALMANAC"|"MW"|"INTEGRITY"|"MANUAL"
    topic_key: Optional[str]       # Links to FBE topic if relevant
    domain: str                    # Which domain this affects
    segment: str                   # "core"|"peripheral"
    narrative: str                 # "N1_primary"|"N2_counter"

    inputs: List[str]              # Signal fields / existing metrics
    outputs: List[str]             # New metric IDs / operator IDs

    rationale: Dict[str, Any]      # Evidence (term velocity, MW shift, etc.)
    risk_notes: Dict[str, Any]     # Integrity exposure, manipulation risk

    proposed_thresholds: Dict      # Optional thresholds
    rent_manifest_draft_path: Optional[str]

    created_ts: datetime
    provenance: Dict
```

### SandboxResult

```python
class SandboxResult:
    candidate_id: str
    sandbox_run_id: str

    before_scores: Dict            # Brier/log/calibration before candidate
    after_scores: Dict             # Brier/log/calibration after candidate
    delta_scores: Dict             # Improvement deltas

    cost_observed: Dict            # Time/memory measurements
    pass_gate: bool                # Did it meet promotion criteria?

    notes: List[str]
    provenance: Dict
```

---

## Candidate Generation Rules

### From AAlmanac Delta

**Trigger**: New/accelerating term crosses velocity threshold

**Proposal**:
```python
if term.velocity > threshold and term.novelty == "HIGH":
    candidate = MetricCandidate(
        kind=METRIC,
        title=f"Term coupling metric: {term.term_handle}",
        proposed_by="AALMANAC",
        domain="AALMANAC",
        topic_key=f"term_cluster:{term.term_handle}",
        outputs=[f"term_coupling::{term.term_handle}"],
        rationale={
            "term_handle": term.term_handle,
            "velocity": term.velocity,
            "novelty": term.novelty,
            "evidence_count": term.occurrence_count
        },
        risk_notes={
            "narrative_content_exposed": True,  # Long-horizon impact limited
            "ssi_sensitivity_required": True
        }
    )
```

**Bounds**:
- Max 4 candidates from AAlmanac per run
- Only if novelty >= MED
- Only if velocity crosses recent mean + 2σ

### From MW Shift

**Trigger**: MW indicates increased synthetic_saturation or propaganda_pressure

**Proposal**:
```python
if mw_shift.magnitude > threshold and mw_shift.type == "INTEGRITY_RISK":
    candidate = MetricCandidate(
        kind=PARAM_TWEAK,
        title=f"Increase SSI dampening for {horizon}",
        proposed_by="MW",
        domain="FORECAST",
        outputs=["forecast.ssi_dampening_multiplier"],
        rationale={
            "mw_shift_magnitude": mw_shift.magnitude,
            "ssi_trend": "increasing",
            "affected_horizons": ["H1Y", "H5Y"]
        },
        risk_notes={
            "conservative_only": True,  # Only increases dampening, never decreases
        }
    )
```

### From Integrity Delta

**Trigger**: SSI rising + quarantined sources dominating

**Proposal**:
```python
if integrity.ssi > threshold and integrity.quarantine_ratio > 0.6:
    candidate = MetricCandidate(
        kind=PARAM_TWEAK,
        title="Increase integrity filtering for long horizons",
        proposed_by="INTEGRITY",
        domain="FORECAST",
        outputs=["forecast.long_horizon_min_confidence"],
        rationale={
            "ssi": integrity.ssi,
            "quarantine_ratio": integrity.quarantine_ratio,
            "affected_horizons": ["H1Y", "H2Y", "H5Y"]
        }
    )
```

**Global Bounds**:
- Max 10 candidates total per run
- Max 4 per source (AALMANAC, MW, INTEGRITY)
- Candidate ID: hash of (kind + domain + segment + narrative + outputs + date)

---

## Sandbox Testing

### Approach

**Goal**: Prove "would this candidate improve scoreboard metrics?"

**Method** (v0.1 minimal):
1. Identify impacted backtest cases (by domain/horizon)
2. Compute **baseline scores** (current config)
3. Apply **candidate override** (in-memory only, no global mutation)
4. Recompute scores
5. Compare delta: `after - before`

### Supported Overrides (v0.1)

**Param tweaks only** (metrics/operators need implementation first):

```python
overrides = {
    "forecast.ssi_dampening_multiplier_by_horizon": {
        "H1Y": 1.2,  # 20% more dampening
        "H5Y": 1.4   # 40% more dampening
    },
    "forecast.long_horizon_min_confidence": "HIGH",  # Require HIGH confidence
    "smem.long_horizon_quarantine_required": True    # If supported
}
```

**Pass to FBE update**:
```python
updated = apply_influence_to_ensemble(
    ensemble, influences, integrity_snapshot,
    overrides=overrides  # NEW parameter
)
```

### Sandbox Gate Criteria

```python
def passes_sandbox_gate(delta_scores, candidate):
    # 1. Improvement threshold
    if delta_scores.brier_delta < -0.005:  # Lower is better
        improvement = True
    elif delta_scores.calibration_error_delta < -0.02:
        improvement = True
    else:
        improvement = False

    # 2. No regressions on protected horizons
    protected = ["H72H", "H30D"]  # Short-term accuracy critical
    if candidate.affects_horizons not in protected:
        # Allowed to change long horizons only
        pass
    else:
        # Must not worsen short horizons
        if any(delta_scores[h].brier_delta > 0.01 for h in protected):
            return False

    # 3. Cost bounds
    if delta_scores.time_delta_pct > 0.20:  # >20% slower
        return False

    return improvement
```

---

## Stabilization Window

### Purpose

Prevent "lucky run" promotions. Require consistency.

### Mechanism

**Requirement**: Candidate must pass sandbox on **N consecutive runs** (default N=3)

**Storage**: `data/run_state/stabilization/<candidate_id>.json`

```json
{
  "candidate_id": "cand_ssi_dampening_h5y_abc123",
  "required_runs": 3,
  "consecutive_passes": [
    {"run_id": "run_20251226_120000", "passed": true},
    {"run_id": "run_20251227_120000", "passed": true},
    {"run_id": "run_20251228_120000", "passed": false}  // RESET!
  ],
  "current_streak": 0,  // Reset to 0 on any failure
  "status": "STABILIZING"
}
```

**Rules**:
- First sandbox pass → status = "STABILIZING", streak = 1
- Each subsequent pass → streak += 1
- Any failure → streak = 0, must restart
- streak == required_runs → status = "APPROVED", ready for promotion

---

## Promotion Actions

### Param Tweak Promotion

**Action**: Write to parameter override file

**File**: `data/forecast/overrides/long_horizon_overrides.yaml`

```yaml
# Auto-generated from promoted candidate: cand_ssi_dampening_h5y_abc123
# DO NOT EDIT MANUALLY - managed by evolution track

overrides:
  ssi_dampening_multiplier_by_horizon:
    H1Y: 1.2
    H5Y: 1.4

provenance:
  promoted_at: "2025-12-29T12:00:00Z"
  candidate_id: "cand_ssi_dampening_h5y_abc123"
  stabilization_runs: 3
  sandbox_delta_brier_avg: -0.008
  ledger_anchor: "promotions.jsonl@step_hash=xyz789"
```

**Integration**: FBE update reads this file at runtime:
```python
# In abraxas/forecast/update.py
overrides = load_overrides_if_exists()  # Reads long_horizon_overrides.yaml
apply_influence_to_ensemble(..., overrides=overrides)
```

### Metric/Operator Promotion (v0.1)

**Action**: DO NOT auto-generate code (too risky)

**Instead**: Create implementation ticket

**File**: `data/evolution/implementation_tickets/<candidate_id>.md`

```markdown
# Implementation Ticket: Term Coupling Metric

**Candidate ID**: cand_term_coupling_doppelganger_abc123
**Status**: APPROVED, awaiting implementation
**Priority**: MED

## Specification

**Metric**: `term_coupling::digital_doppelganger`
**Domain**: AALMANAC + FORECAST
**Inputs**:
- AAlmanac term handle: "digital_doppelganger"
- Occurrence count, velocity, novelty

**Outputs**:
- Coupling strength [0, 1]
- Forecast ensemble for H72H/H30D

## Rationale

Term "digital_doppelganger" crossed velocity threshold (3.2σ above mean).
Novelty: HIGH. Sandbox testing showed -0.012 Brier improvement on H72H.

## Files to Create

1. `abraxas/aalmanac/metrics/term_coupling.py`
   - Function: `compute_term_coupling(term_handle, ctx) -> float`

2. `data/rent_manifests/metrics/term_coupling_digital_doppelganger.yaml`
   - Claim: Improves H72H accuracy
   - Proof: Sandbox results + backtest cases

## Testing

- Create `tests/test_term_coupling_metric.py`
- Golden output: `tests/golden/aalmanac/term_coupling_output.json`

## Provenance

- Proposed by: AALMANAC
- Sandbox runs: 3 consecutive passes
- Promotion date: 2025-12-29
- Ledger anchor: promotions.jsonl@step_hash=xyz789
```

**Manual Review**: Team reviews ticket, implements if approved

---

## Ledgers (Append-Only)

### Candidates Ledger

**Path**: `out/evolution_ledgers/candidates.jsonl`

```json
{
  "timestamp": "2025-12-26T14:00:00Z",
  "type": "candidate_proposed",
  "run_id": "run_20251226_140000",
  "candidate_id": "cand_ssi_dampening_h5y_abc123",
  "kind": "param_tweak",
  "proposed_by": "MW",
  "domain": "FORECAST",
  "topic_key": null,
  "outputs": ["forecast.ssi_dampening_multiplier"],
  "summary_hash": "sha256_of_full_candidate",
  "prev_hash": "abc123...",
  "step_hash": "def456..."
}
```

### Sandbox Ledger

**Path**: `out/evolution_ledgers/sandbox_runs.jsonl`

```json
{
  "timestamp": "2025-12-26T15:00:00Z",
  "type": "sandbox_run",
  "sandbox_run_id": "sandbox_cand_ssi_dampening_h5y_abc123_run_1",
  "candidate_id": "cand_ssi_dampening_h5y_abc123",
  "before_scores_hash": "sha256_of_before",
  "after_scores_hash": "sha256_of_after",
  "delta_brier_avg": -0.008,
  "delta_log_avg": -0.012,
  "pass_gate": true,
  "prev_hash": "def456...",
  "step_hash": "ghi789..."
}
```

### Promotions Ledger

**Path**: `out/evolution_ledgers/promotions.jsonl`

```json
{
  "timestamp": "2025-12-29T12:00:00Z",
  "type": "promotion",
  "promotion_id": "prom_cand_ssi_dampening_h5y_abc123",
  "candidate_id": "cand_ssi_dampening_h5y_abc123",
  "promotion_action": "param_override",  // or "implementation_ticket"
  "stabilization_runs_passed": 3,
  "override_file_hash": "sha256_of_override_file",
  "prev_hash": "ghi789...",
  "step_hash": "jkl012..."
}
```

---

## Integration with Scheduler

### Daily Run Plan Update

**File**: `data/run_plans/daily_v0_1.yaml`

```yaml
steps:
  # ... existing steps (srr, smem, siw, tau, mw, integrity, update_fbe, score_forecasts) ...

  - id: propose_candidates
    enabled: true
    module: "abraxas.evolve.pipeline"
    function: "run_step_propose_candidates"
    args:
      max_candidates: 10
      max_per_source: 4

  - id: sandbox_candidates
    enabled: true
    module: "abraxas.evolve.pipeline"
    function: "run_step_sandbox_candidates"
    args:
      cases_dir: "data/backtests/cases"
      max_to_run: 5  # Limit sandbox runs per execution
      strict: false  # Allow experimental candidates

  - id: decide_promotions
    enabled: true
    module: "abraxas.evolve.pipeline"
    function: "run_step_decide_promotions"
    args:
      stabilization_runs_required: 3
      auto_promote_param_tweaks: true
      auto_promote_metrics: false  # Require manual review
```

**Artifacts per run**:
- `out/runs/<run_id>/evolution/proposals.json`
- `out/runs/<run_id>/evolution/sandbox.json`
- `out/runs/<run_id>/evolution/promotions.json`

---

## Architecture

```
abraxas/
├── evolve/
│   ├── __init__.py
│   ├── types.py              # MetricCandidate, SandboxResult, CandidateKind
│   ├── candidate_generator.py  # Propose from deltas
│   ├── store.py              # Save/load candidates, ledgers
│   ├── sandbox.py            # Sandbox executor
│   ├── promotion.py          # Promotion gate + stabilization
│   └── pipeline.py           # Scheduler step runners
├── online/
│   └── vector_map_loader.py  # Load/validate vector map registry

data/
├── vector_maps/
│   └── source_vector_map_v0_1.yaml
├── evolution/
│   ├── candidates/
│   │   └── <candidate_id>.json
│   └── implementation_tickets/
│       └── <candidate_id>.md
├── forecast/
│   └── overrides/
│       └── long_horizon_overrides.yaml  # Promoted param tweaks
└── run_state/
    └── stabilization/
        └── <candidate_id>.json

out/
└── evolution_ledgers/
    ├── candidates.jsonl
    ├── sandbox_runs.jsonl
    └── promotions.jsonl
```

---

## Determinism Guarantees

✅ **Candidate Generation**: Rule-based, deterministic from deltas
✅ **Candidate IDs**: Hash-based (kind + domain + outputs + date)
✅ **Sandbox Testing**: Deterministic score computation
✅ **Promotion Gate**: Fixed criteria, boolean logic
✅ **Stabilization**: Consecutive run counting (deterministic)
✅ **Ledger Recording**: Hash-chained, canonical JSON

**No ML. No randomness. Fully replayable from ledgers.**

---

## Why This Is Safe

### Guards Against Metric Sprawl

1. **Bounded Proposals**: Max 10/run, max 4/source
2. **Sandbox Required**: Must prove improvement before consideration
3. **Stabilization Window**: Must pass 3 consecutive runs
4. **Regression Protection**: Cannot worsen protected horizons
5. **Manual Review**: Metrics/operators require implementation tickets (not auto-generated)

### Guards Against Manipulation

1. **SSI Dampening**: All candidates inherit integrity awareness
2. **Risk Notes**: Candidates marked with exposure (narrative_content, ssi_sensitivity)
3. **Long-Horizon Scoping**: Param tweaks primarily affect H1Y/H5Y (less vulnerable to short-term manipulation)
4. **Offline OSH**: Online sources only via allowlist (existing boundary)

### Audit Trail

Every promotion traceable:
```
AAlmanac Delta → Candidate Proposal → Sandbox Test (3 runs) → Promotion → Override File
      ↓               ↓                    ↓                    ↓            ↓
  delta.jsonl  candidates.jsonl  sandbox_runs.jsonl  promotions.jsonl  overrides.yaml
```

---

## Evolution Path

### v0.1 (This Patch)
✅ Candidate generation (AALMANAC, MW, INTEGRITY)
✅ Sandbox testing (param tweaks only)
✅ Stabilization window (3 consecutive runs)
✅ Param override promotion (auto)
✅ Metric/operator tickets (manual review)

### v0.2 (Future)
- Semantic topic discovery (auto MW cluster → FBE ensemble)
- Branch proposal candidates (new branches for existing ensembles)
- Multi-candidate A/B testing in sandbox
- Auto-implementation for low-risk metrics (with stricter gates)

### v0.3 (Future)
- Meta-evolution (which proposal strategies work best)
- Ensemble structure evolution (branch count, p distributions)
- Cross-domain coupling metrics
- Active learning integration (failures → candidates)

---

**End of Patch Plan**
