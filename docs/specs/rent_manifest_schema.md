# Rent Manifest Schema — Canonical Specification

**Version**: 0.1
**Status**: Canonical
**Created**: 2025-12-26
**Purpose**: Define the structure of rent manifests for metrics, operators, and artifacts

---

## Overview

Every new metric, operator, or artifact in Abraxas must have a **rent manifest** - a YAML file that declares:
1. What it improves (measurable benefits)
2. What it costs (compute/time/entropy)
3. How it's proven (tests, golden files, ledger deltas)

This document defines the canonical schema for all three manifest types.

---

## Manifest Types

### 1. MetricRentManifest
### 2. OperatorRentManifest
### 3. ArtifactRentManifest

---

## Common Fields (All Manifest Types)

All manifests share these required fields:

```yaml
id: str                      # Unique identifier (snake_case)
kind: str                    # "metric" | "operator" | "artifact"
domain: str                  # "MW" | "AALMANAC" | "TAU" | "INTEGRITY" | "TER" | "SOD" | "ROUTING" | "SCHEDULER" | "GOVERNANCE"
description: str             # Human-readable description (1-3 sentences)
owner_module: str            # Python module path (e.g., "abraxas.metrics.tau.tau_latency")
version: str                 # Semantic version (e.g., "0.1")
created_at: str              # ISO 8601 date (YYYY-MM-DD)
```

---

## MetricRentManifest

**Purpose**: Declares a new metric that measures some aspect of Abraxas behavior.

### Schema

```yaml
id: str                      # e.g., "tau_latency"
kind: "metric"
domain: str                  # Domain this metric belongs to
description: str
owner_module: str            # Python module implementing this metric

# What this metric consumes and produces
inputs: list[str]            # Metric IDs or signal field names used as inputs
outputs: list[str]           # Metric IDs produced/updated by this metric

# Cost model: expected computational cost
cost_model:
  time_ms_expected: int      # Expected runtime in milliseconds
  memory_kb_expected: int    # Expected memory usage in KB
  io_expected: str           # "none" | "read" | "write" | "read_write"

# Rent claim: what this metric improves and how it's measurable
rent_claim:
  improves: list[str]        # e.g., ["replayability", "auditability", "prediction_calibration"]
  measurable_by: list[str]   # e.g., ["ledger_delta_rate", "golden_test", "backtest_pass_rate"]
  thresholds: dict           # e.g., {"backtest_pass_rate_min": 0.70}

# Proof: how this metric's value is proven
proof:
  tests: list[str]           # Pytest node IDs (e.g., "tests/test_tau.py::test_tau_latency")
  golden_files: list[str]    # Paths to golden files (must exist or be created by tests)
  ledgers_touched: list[str] # Ledger paths that this metric reads/writes

version: str                 # "0.1"
created_at: str              # "2025-12-26"
```

### Example

```yaml
id: "tau_latency"
kind: "metric"
domain: "TAU"
description: "Measures the temporal latency between MW term creation and TAU signal incorporation"
owner_module: "abraxas.metrics.tau.tau_latency"

inputs: ["mw_terms", "tau_signals"]
outputs: ["tau_latency_ms"]

cost_model:
  time_ms_expected: 25
  memory_kb_expected: 512
  io_expected: "read"

rent_claim:
  improves: ["temporal_auditability", "prediction_calibration"]
  measurable_by: ["golden_test", "ledger_delta_rate"]
  thresholds:
    ledger_delta_rate_min: 0.05

proof:
  tests:
    - "tests/test_tau_metrics.py::test_tau_latency_computation"
    - "tests/test_tau_metrics.py::test_tau_latency_golden"
  golden_files:
    - "tests/golden/metrics/tau_latency_output.json"
  ledgers_touched:
    - "out/temporal_ledgers/tau_ledger.jsonl"

version: "0.1"
created_at: "2025-12-26"
```

---

## OperatorRentManifest

**Purpose**: Declares a new operator that transforms or routes signals/data within Abraxas.

### Schema

Inherits all MetricRentManifest fields, plus:

```yaml
operator_id: str             # Unique operator ID (same as 'id' but explicit)

# TER integration: edges in the Temporal Event Router graph
ter_edges_claimed: list[dict]
  # Each edge is: {"from": str, "to": str}
  # e.g., [{"from": "mw_ingress", "to": "tau_processor"}]
  # These must be a subset of actual TER edges if TER spec exists
```

### Example

```yaml
id: "srr_router"
kind: "operator"
domain: "ROUTING"
description: "Scenario Router routes incoming scenarios to appropriate handlers based on priority and domain"
owner_module: "abraxas.operators.routing.srr_router"
operator_id: "srr_router"

inputs: ["scenario_envelope", "routing_rules"]
outputs: ["routed_scenario", "routing_decision"]

cost_model:
  time_ms_expected: 15
  memory_kb_expected: 256
  io_expected: "read"

rent_claim:
  improves: ["routing_determinism", "auditability"]
  measurable_by: ["golden_test", "routing_decision_log"]
  thresholds:
    routing_accuracy_min: 0.95

proof:
  tests:
    - "tests/test_srr_router.py::test_routing_logic"
    - "tests/test_srr_router.py::test_routing_golden"
  golden_files:
    - "tests/golden/operators/srr_router_decisions.json"
  ledgers_touched:
    - "out/routing_ledgers/srr_decisions.jsonl"

ter_edges_claimed:
  - from: "scenario_ingress"
    to: "srr_router"
  - from: "srr_router"
    to: "scenario_handler"

version: "0.1"
created_at: "2025-12-26"
```

---

## ArtifactRentManifest

**Purpose**: Declares a new artifact (file, report, ledger, etc.) produced by Abraxas.

### Schema

Inherits common fields, plus:

```yaml
artifact_id: str             # Unique artifact ID (same as 'id' but explicit)

# Outputs: what files/paths this artifact produces
output_paths: list[str]      # e.g., ["out/reports/integrity_brief.md"]

# Uniqueness claim: what makes this artifact non-commodity
uniqueness_claim: list[str]  # e.g., ["requires_hash_chain", "contains_deltas", "provenance_linked"]
```

### Example

```yaml
id: "integrity_brief"
kind: "artifact"
domain: "INTEGRITY"
description: "Daily integrity brief summarizing ledger health, delta counts, and anomaly flags"
owner_module: "abraxas.artifacts.integrity_brief"
artifact_id: "integrity_brief"

inputs: ["ledger_health_metrics", "delta_counts", "anomaly_flags"]
outputs: ["integrity_brief_md", "integrity_brief_json"]

cost_model:
  time_ms_expected: 100
  memory_kb_expected: 2048
  io_expected: "write"

rent_claim:
  improves: ["operational_transparency", "auditability", "anomaly_detection"]
  measurable_by: ["golden_test", "artifact_completeness_check"]
  thresholds:
    artifact_sections_min: 5

proof:
  tests:
    - "tests/test_integrity_brief.py::test_brief_generation"
    - "tests/test_integrity_brief.py::test_brief_golden"
  golden_files:
    - "tests/golden/artifacts/integrity_brief_sample.md"
  ledgers_touched:
    - "out/temporal_ledgers/integrity_ledger.jsonl"

output_paths:
  - "out/reports/integrity_brief.md"
  - "out/reports/integrity_brief.json"

uniqueness_claim:
  - "requires_hash_chain"
  - "contains_deltas"
  - "provenance_linked"

version: "0.1"
created_at: "2025-12-26"
```

---

## Field Definitions

### `domain`
Valid values:
- `MW`: Meaning Weave
- `AALMANAC`: Adaptive Almanac
- `TAU`: Temporal Alignment Utility
- `INTEGRITY`: Data integrity and hash chains
- `TER`: Temporal Event Router
- `SOD`: Signal Orchestration Director
- `ROUTING`: Scenario routing
- `SCHEDULER`: Task scheduling
- `GOVERNANCE`: Rent enforcement and auditing

### `cost_model.io_expected`
Valid values:
- `none`: No file I/O
- `read`: Reads from disk/ledgers
- `write`: Writes to disk/ledgers
- `read_write`: Both reads and writes

### `rent_claim.improves`
Suggested values (not exhaustive):
- `replayability`: Makes past runs reproducible
- `auditability`: Makes decisions traceable
- `prediction_calibration`: Improves forecast accuracy
- `temporal_alignment`: Improves timing synchronization
- `routing_determinism`: Makes routing predictable
- `operational_transparency`: Makes system state visible
- `anomaly_detection`: Catches unexpected behavior
- `integrity_preservation`: Maintains data consistency

### `rent_claim.measurable_by`
Suggested values:
- `golden_test`: Comparison against golden files
- `ledger_delta_rate`: Rate of ledger updates
- `backtest_pass_rate`: Percentage of backtests passing
- `routing_decision_log`: Logged routing decisions
- `artifact_completeness_check`: All sections present
- `hash_chain_verification`: Hash chain validates

### `rent_claim.thresholds`
Key-value pairs where keys are metric names and values are numeric thresholds.
Examples:
- `backtest_pass_rate_min: 0.70`: At least 70% of backtests must pass
- `ledger_delta_rate_min: 0.05`: At least 5% of ledger entries should be new
- `routing_accuracy_min: 0.95`: At least 95% routing accuracy
- `artifact_sections_min: 5`: At least 5 sections in artifact

---

## Validation Rules

### Structural Validation
1. All required fields must be present
2. `kind` must be one of: `"metric"`, `"operator"`, `"artifact"`
3. `domain` must be a valid domain value
4. `version` must follow semantic versioning (e.g., "0.1", "1.0.0")
5. `created_at` must be valid ISO 8601 date

### Cost Model Validation
1. `time_ms_expected` must be non-negative integer
2. `memory_kb_expected` must be non-negative integer
3. `io_expected` must be one of: `"none"`, `"read"`, `"write"`, `"read_write"`

### Proof Validation
1. All `tests` must be discoverable by pytest (format: `path/to/test.py::test_function`)
2. All `golden_files` must either:
   - Exist at specified path, OR
   - Be created by one of the declared tests
3. All `ledgers_touched` should follow path conventions (but paths don't need to exist yet)

### Operator-Specific Validation
1. `ter_edges_claimed` edges must be valid:
   - Each edge has `from` and `to` fields
   - If TER spec exists, edges must be subset of TER graph

### Artifact-Specific Validation
1. `output_paths` must be non-empty list
2. `uniqueness_claim` must be non-empty list

---

## Storage Conventions

### Directory Structure
```
data/rent_manifests/
├── metrics/
│   ├── tau_latency.yaml
│   ├── tau_memory.yaml
│   └── ...
├── operators/
│   ├── smem_gatekeeper.yaml
│   ├── srr_router.yaml
│   └── ...
└── artifacts/
    ├── integrity_brief.yaml
    ├── ledger_hash_chain.yaml
    └── ...
```

### File Naming
- File name should match the `id` field
- Use snake_case
- Extension must be `.yaml`
- Example: `tau_latency.yaml` for metric with `id: "tau_latency"`

---

## Evolution

### v0.1 (Current)
- Basic schema with required fields
- Manual creation of manifests
- Validation of structure and references

### v0.2 (Future)
- Auto-generation from docstrings
- Observed vs expected cost tracking
- Deprecation warnings for manifests without recent test runs

### v0.3 (Future)
- Backtest linkage required for predictive claims
- Threshold enforcement against actual backtest results
- Rent amortization over time

---

## Related Documents

- [Rent Enforcement v0.1 Patch Plan](../plan/rent_enforcement_v0_1_patch_plan.md)
- [Rent Enforcement v0.1 Specification](./rent_enforcement_v0_1.md)

---

**End of Schema Specification**
