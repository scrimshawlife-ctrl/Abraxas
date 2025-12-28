# Adaptive State Capsule - Lifecycle Rules (Canonical)

**Version**: 1.0
**Status**: Canonical
**Purpose**: Define interpretation rules for ASC lifecycle phases without encoding behavior

---

## Lifecycle Phases

### 1. `emergent`
**Meaning**: Newly introduced component with minimal operational history

**Characteristics**:
- Low age_cycles (< 10)
- Limited exposure_events
- Unknown stability/confidence trends
- No established trust profile

**Transitions to**:
- `ascendant` (normal progression with successful invocations)
- `volatile` (if early drift detected)

---

### 2. `ascendant`
**Meaning**: Component gaining operational maturity and trust

**Characteristics**:
- Growing age_cycles (10-50)
- Increasing exposure_events
- Confidence trend: stable or increasing
- Trust index: 0.3 < trust < 0.75

**Transitions to**:
- `stable` (sustained high trust)
- `volatile` (drift flag triggered)
- `decaying` (trust decline)

---

### 3. `stable`
**Meaning**: Mature, reliable component with proven track record

**Characteristics**:
- High trust index (> 0.75)
- No drift flags
- Low pressure (< 0.4)
- Confidence trend: stable

**Influences**:
- +5% maturity bonus in slang weighting
- Priority in promotion review
- Higher governance weight

**Transitions to**:
- `volatile` (semantic drift detected)
- `decaying` (sustained trust decline)
- `fossil` (operational retirement after sustained age)

---

### 4. `volatile`
**Meaning**: Component experiencing instability or semantic drift

**Characteristics**:
- drift_flag = true (semantic instability)
- OR pressure_trend = "high"
- OR confidence_trend = "volatile"

**Influences**:
- -10% maturity penalty in slang weighting
- Increased monitoring priority
- Promotion gates blocked

**Transitions to**:
- `stable` (drift resolved, trust restored)
- `decaying` (sustained instability)

---

### 5. `decaying`
**Meaning**: Component in decline, operational relevance decreasing

**Detection Rules**:
- **Rule 1**: trust_index < 0.3 (low reliability)
- **Rule 2**: trust_trend = "decreasing" AND pressure_trend ∈ {"high", "rising"}
- **Rule 3**: confidence_trend = "decreasing" for sustained period

**Characteristics**:
- Declining trust or rising pressure
- May have sustained errors
- Operational fitness questioned

**Influences**:
- Retirement recommendation triggered
- Weighting severely reduced
- Governance review suggested

**Transitions to**:
- `fossil` (if idle + aged, per retirement heuristic)
- `ascendant` (rare recovery via fixes/updates)

---

### 6. `fossil`
**Meaning**: Retired component preserved for historical/archeological value

**Detection Rules**:
- **Rule 1**: age_cycles > 50 AND idle_days > 30 (aged + dormant)
- **Rule 2**: Manual governance retirement decision

**Characteristics**:
- No recent exposure_events (idle > 30 days)
- High age_cycles (> 50)
- Stable semantics (preserved state)
- Low/zero operational relevance

**What a Fossil IS**:
- ✅ Queryable for lineage analysis
- ✅ Queryable for historical drift comparison
- ✅ Queryable for archeological research
- ✅ Preserved in ASC with full provenance
- ✅ Available for narrative synthesis

**What a Fossil is NOT**:
- ❌ Deleted from storage
- ❌ Ignored in queries
- ❌ Unavailable for inspection
- ❌ Automatically removed

**Influences**:
- Near-zero weighting in live inference (≈ 0.01)
- Excluded from active promotion pipeline
- Included in archeology/genealogy queries
- Historical comparison baseline

**Transitions to**:
- None (terminal state in normal lifecycle)
- Can be manually resurrected via governance if needed

---

## Retirement Protocol

### Phase 1: Detection (Automated)
Retirement heuristics scan ASC index and generate recommendations:
- **Input**: `data/adaptive_state/index.json`
- **Output**: `data/adaptive_state/retirement_recommendations.json`
- **Action**: None (suggestions only)

### Phase 2: Review (Manual)
Human/governance reviews recommendations:
- Validate retirement criteria
- Check for active dependencies
- Assess historical value
- Consider successor components

### Phase 3: Decision (Governance-Gated)
If retirement approved:
1. Create migration event (if successor exists)
2. Issue governance receipt documenting decision
3. Update ASC lifecycle_phase to `fossil`
4. Update registry status (if applicable)

### Phase 4: Preservation (Deterministic)
Fossil components:
- Remain in `data/adaptive_state/rune/`
- Indexed with phase="fossil"
- Available for archeological queries
- Receive near-zero live weighting

---

## Key Principles

1. **No Automatic Deletion**: Components never disappear
2. **Recommendations, Not Actions**: Heuristics suggest, governance decides
3. **Memory Without Influence**: Fossils preserve history without affecting live systems
4. **Deterministic Rules**: All transitions based on observable metrics
5. **Governance Override**: Manual decisions always possible

---

## Implementation Notes

- Lifecycle phase transitions are **suggestions** from ASC generator
- Actual phase updates occur via deterministic rules in `tools/build_adaptive_state_capsules.py`
- Retirement recommendations are **advisory only** via `tools/retirement_recommendations.py`
- Governance receipts provide **immutable audit trail** for manual transitions

---

**End of Canonical Lifecycle Rules**
