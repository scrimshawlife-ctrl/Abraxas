# Abraxas Artifact Schema Index (Canonical)

**Version:** 1.0.0  
**Last Updated:** 2026-01-04  
**Status:** Canonical Contract

This document defines the canonical on-disk artifacts emitted by Abraxas runtime.
All artifacts MUST be deterministic under identical inputs and bindings, unless explicitly noted.

---

## Table of Contents

1. [Determinism Rules (Global)](#determinism-rules-global)
2. [RunIndex.v0](#1-runindexv0)
3. [RunHeader.v0](#2-runheaderv0-write-once)
4. [TrendPack.v0](#3-trendpackv0)
5. [ResultsPack.v0](#4-resultspackv0)
6. [ViewPack.v0](#5-viewpackv0)
7. [PolicySnapshot.v0](#6-policysnapshotv0)
8. [PolicyRef.v0](#7-policyrefv0)
9. [RunStability.v0](#8-runstabilityv0)
10. [StabilityRef.v0](#9-stabilityrefv0)
11. [ShadowResult (Detector Contract)](#shadowresult-detector-output-contract)
12. [RetentionPolicy.v0](#retentionpolicyv0-optional)
13. [InvarianceSummary.v0](#invariancesummaryv0-embedded)
14. [StabilitySummary.v0](#stabilitysummaryv0-embedded)

---

## Determinism Rules (Global)

All Abraxas artifacts follow these determinism rules:

### JSON Serialization
- JSON MUST be serialized with **stable key ordering** (writer enforces `sort_keys=True`).
- Separators MUST be `(",", ":")` (compact, no extra whitespace).
- Encoding MUST be UTF-8.

### List Ordering
- Lists MUST be deterministic in ordering:
  - Tasks sorted by name where applicable.
  - Records sorted by `(tick, kind, schema, path)` where applicable.
  - Events in timeline order (execution order).

### Path Determinism
- Artifact paths MUST be deterministic:
  - Tick artifacts: use zero-padded tick numbers (e.g., `000000`).
  - Run artifacts: one per `run_id` (write-once where specified).
- Paths embedded in artifacts MUST use relative patterns where possible.

### Timestamps
- No artifact may embed timestamps unless explicitly routed through deterministic time sources.
- Generally disallowed to ensure reproducibility.

### Hashing
- All provenance hashes MUST be SHA-256 hex-encoded (64 characters).
- Hashes are computed on the canonical JSON serialization.

---

## 1) RunIndex.v0

**Purpose:** Minimal per-tick entrypoint pointing to other artifacts.

**Path Pattern:** `run_index/<run_id>/<tick:06d>.runindex.json`

**Example Path:** `run_index/my_run/000000.runindex.json`

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | `"RunIndex.v0"` | Schema identifier |
| `run_id` | `string` | Run identifier |
| `tick` | `integer` | Tick number |
| `refs` | `object` | References to other artifacts |
| `refs.trendpack` | `string` | Path to TrendPack |
| `refs.results_pack` | `string` | Path to ResultsPack |
| `refs.run_header` | `string` | Path to RunHeader |
| `hashes` | `object` | SHA-256 hashes |
| `hashes.trendpack_sha256` | `string` | TrendPack content hash |
| `hashes.results_pack_sha256` | `string` | ResultsPack content hash |
| `tags` | `array` | Optional tags (empty array if none) |
| `provenance` | `object` | Provenance metadata |

### Provenance Fields

| Field | Type | Description |
|-------|------|-------------|
| `provenance.engine` | `string` | Always `"abraxas"` |
| `provenance.mode` | `string` | Execution mode |
| `provenance.policy_ref` | `PolicyRef.v0` | Policy reference |
| `provenance.run_header_sha256` | `string` | RunHeader content hash |

### Notes
- MUST contain `refs.run_header`.
- SHOULD contain hashes for every ref it lists.

---

## 2) RunHeader.v0 (Write-Once)

**Purpose:** Run-level provenance written once per `run_id`.

**Path Pattern:** `runs/<run_id>.runheader.json`

**Example Path:** `runs/my_run.runheader.json`

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | `"RunHeader.v0"` | Schema identifier |
| `run_id` | `string` | Run identifier |
| `mode` | `string` | Execution mode |
| `code` | `object` | Code provenance |
| `code.git_sha` | `string \| null` | Git SHA (best-effort, null if unavailable) |
| `pipeline_bindings` | `object` | Pipeline bindings provenance |
| `policy_refs` | `object` | Map of policy name to PolicyRef |
| `stability_ref_pattern` | `string` | Convention path for StabilityRef |
| `env` | `object` | Environment fingerprint |

### Environment Fingerprint

```json
{
  "python": {
    "version": "3.12.3",
    "implementation": "CPython"
  },
  "platform": {
    "system": "Linux",
    "release": "6.1.147",
    "machine": "x86_64"
  }
}
```

### Write-Once Rule
- If file exists, it MUST NOT be rewritten.
- Use `ensure_run_header()` which respects this rule.

---

## 3) TrendPack.v0

**Purpose:** Timeline of ERS trace events for a tick; lightweight visualization format.

**Path Pattern:** `viz/<run_id>/<tick:06d>.trendpack.json`

**Example Path:** `viz/my_run/000000.trendpack.json`

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | `"TrendPack.v0"` | Schema identifier (in provenance) |
| `version` | `string` | Format version (e.g., `"0.1"`) |
| `run_id` | `string` | Run identifier |
| `tick` | `integer` | Tick number |
| `timeline` | `array` | List of Event objects |
| `budget` | `object` | Budget analysis by lane |
| `errors` | `array` | Error events extracted |
| `skipped` | `array` | Skipped events extracted |
| `stats` | `object` | Summary statistics |
| `provenance` | `object` | Provenance metadata |

### Event Fields (in timeline)

| Field | Type | Description |
|-------|------|-------------|
| `task` | `string` | Task name (e.g., `"oracle:signal"`) |
| `lane` | `"forecast" \| "shadow"` | Execution lane |
| `status` | `string` | `"ok"`, `"skipped_budget"`, `"error"` |
| `cost_ops` | `integer` | Operations cost |
| `cost_entropy` | `number` | Entropy cost |
| `meta` | `object` | Event metadata |
| `meta.result_ref` | `ResultRef.v0` | Reference to full result |

### ResultRef Injection Rule
- `event.meta.result_ref` MUST exist where ResultsPack is emitted.
- Contains `{ schema, results_pack, task }`.

---

## 4) ResultsPack.v0

**Purpose:** All TaskResult outputs for a tick (full results, deterministic ordering).

**Path Pattern:** `results/<run_id>/<tick:06d>.resultspack.json`

**Example Path:** `results/my_run/000000.resultspack.json`

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | `"ResultsPack.v0"` | Schema identifier |
| `run_id` | `string` | Run identifier |
| `tick` | `integer` | Tick number |
| `items` | `array` | List of task results |
| `provenance` | `object` | Provenance metadata |

### Item Fields

| Field | Type | Description |
|-------|------|-------------|
| `task` | `string` | Task name |
| `result` | `object` | Full TaskResult object |

### Ordering Rule
- `items` MUST be sorted by `task` (alphabetically).

---

## 5) ViewPack.v0

**Purpose:** One-file UI overview; self-contained with optional capped resolved results.

**Path Pattern:** `view/<run_id>/<tick:06d>.viewpack.json`

**Example Path:** `view/my_run/000000.viewpack.json`

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | `"ViewPack.v0"` | Schema identifier |
| `run_id` | `string` | Run identifier |
| `tick` | `integer` | Tick number |
| `mode` | `string` | Execution mode |
| `trendpack_ref` | `object` | Reference pattern to TrendPack |
| `aggregates` | `object` | Aggregated statistics and summaries |
| `events` | `array` | Events (same as TrendPack timeline) |
| `resolved` | `array` | Resolved event+result pairs (capped) |
| `resolved_filter` | `object` | Filter metadata |
| `provenance` | `object` | Provenance metadata |

### Aggregates Fields

| Field | Type | Description |
|-------|------|-------------|
| `aggregates.stats` | `object` | Event counts |
| `aggregates.budget` | `object` | Budget by lane |
| `aggregates.error_count` | `integer` | Number of errors |
| `aggregates.skipped_count` | `integer` | Number of skipped |
| `aggregates.invariance` | `InvarianceSummary.v0` | Tick-level invariance |
| `aggregates.stability_summary` | `StabilitySummary.v0 \| null` | Run-level stability (if exists) |

### Notes
- Events have `result_ref` stripped (ViewPack is self-contained).
- `resolved` paths are stripped for determinism.

---

## 6) PolicySnapshot.v0

**Purpose:** Immutable snapshot of a policy file, hashed and referenced by PolicyRef.

**Path Pattern:** `policy_snapshots/<run_id>/<policy>.<sha256>.policysnapshot.json`

**Example Path:** `policy_snapshots/my_run/retention.abc123...def.policysnapshot.json`

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | `"PolicySnapshot.v0"` | Schema identifier |
| `policy` | `string` | Policy name (e.g., `"retention"`) |
| `present` | `boolean` | Whether source file existed |
| `source_path_pattern` | `string` | Relative path pattern to source |
| `policy_obj` | `object \| null` | Policy content (null if missing) |

### Notes
- Snapshots are immutable (content-addressed by SHA-256).
- Reused if identical content already exists.

---

## 7) PolicyRef.v0

**Purpose:** Lightweight reference to a PolicySnapshot (not the mutable policy file).

**Location:** Embedded in provenance objects, not standalone.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | `"PolicyRef.v0"` | Schema identifier |
| `policy` | `string` | Policy name |
| `snapshot_path` | `string` | Relative path to snapshot |
| `snapshot_sha256` | `string` | SHA-256 of snapshot content |

---

## 8) RunStability.v0

**Purpose:** Persisted record of the latest Dozen-Run Gate outcome.

**Path Pattern:** `runs/<run_id>.runstability.json`

**Example Path:** `runs/my_run.runstability.json`

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | `"RunStability.v0"` | Schema identifier |
| `run_id` | `string` | Run identifier |
| `ok` | `boolean` | Gate passed |
| `expected_trendpack_sha256` | `string` | First run's TrendPack hash |
| `trendpack_sha256s` | `array[string]` | All TrendPack hashes |
| `expected_runheader_sha256` | `string \| null` | First run's RunHeader hash |
| `runheader_sha256s` | `array[string] \| null` | All RunHeader hashes |
| `first_mismatch_run` | `integer \| null` | Index of first mismatch |
| `divergence` | `object \| null` | Divergence details |
| `note` | `string \| null` | Optional note |

### Divergence Fields (when present)

| Field | Type | Description |
|-------|------|-------------|
| `divergence.kind` | `string` | `"trendpack_content_mismatch"` or `"runheader_sha256_mismatch"` |
| `divergence.diffs` | `array` | Bounded list of field diffs (max 25) |

### Bounded Diffs Rule
- Divergence diffs MUST be bounded (e.g., first 25 entries).

---

## 9) StabilityRef.v0

**Purpose:** Pointer to RunStability without rewriting RunHeader.

**Path Pattern:** `runs/<run_id>.stability_ref.json`

**Example Path:** `runs/my_run.stability_ref.json`

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | `"StabilityRef.v0"` | Schema identifier |
| `run_id` | `string` | Run identifier |
| `runstability_path` | `string` | Path to RunStability file |
| `runstability_sha256` | `string` | SHA-256 of RunStability content |

---

## ShadowResult (Detector Output Contract)

Shadow detector outputs MUST be normalized to this shape:

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | `string` | `"ok"`, `"not_computable"`, or `"error"` |
| `value` | `any \| null` | Computed value (null if not computable) |
| `missing` | `array[string]` | List of missing required inputs |
| `error` | `string \| null` | Error message (null if no error) |
| `provenance` | `object` | Provenance metadata |

### Helper Functions

Located at:
- `abraxas/detectors/shadow/util.py`: `ok()`, `not_computable()`, `err()`
- `abraxas/detectors/shadow/normalize.py`: `wrap_shadow_task()` wraps all shadow tasks

---

## RetentionPolicy.v0 (Optional)

**Purpose:** Controls artifact retention and pruning.

**Path Pattern:** `policy/retention.json`

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | `"RetentionPolicy.v0"` | Schema identifier |
| `enabled` | `boolean` | Whether retention is active |
| `keep_last_ticks` | `integer` | Number of recent ticks to keep |
| `max_bytes_per_run` | `integer \| null` | Optional size limit |
| `protected_roots` | `array[string]` | Directories to never prune |
| `compact_manifest` | `boolean` | Whether to compact manifest |

---

## InvarianceSummary.v0 (Embedded)

**Purpose:** Tick-level invariance badge data embedded in ViewPack.

**Location:** `ViewPack.aggregates.invariance`

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | `"InvarianceSummary.v0"` | Schema identifier |
| `trendpack_sha256` | `string` | TrendPack content hash |
| `runheader_sha256` | `string` | RunHeader content hash |
| `passed` | `boolean` | Both hashes present and valid |

---

## StabilitySummary.v0 (Embedded)

**Purpose:** Run-level stability badge data embedded in ViewPack.

**Location:** `ViewPack.aggregates.stability_summary`

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | `"StabilitySummary.v0"` | Schema identifier |
| `ok` | `boolean` | Gate passed |
| `first_mismatch_run` | `integer \| null` | Index of first mismatch |
| `divergence_kind` | `string \| null` | Type of divergence |

---

## Artifact Directory Structure

```
<artifacts_dir>/
├── policy/
│   └── retention.json                    # RetentionPolicy.v0
├── policy_snapshots/
│   └── <run_id>/
│       └── <policy>.<sha>.policysnapshot.json  # PolicySnapshot.v0
├── runs/
│   ├── <run_id>.runheader.json           # RunHeader.v0
│   ├── <run_id>.runstability.json        # RunStability.v0
│   └── <run_id>.stability_ref.json       # StabilityRef.v0
├── run_index/
│   └── <run_id>/
│       └── <tick:06d>.runindex.json      # RunIndex.v0
├── results/
│   └── <run_id>/
│       └── <tick:06d>.resultspack.json   # ResultsPack.v0
├── view/
│   └── <run_id>/
│       └── <tick:06d>.viewpack.json      # ViewPack.v0
└── viz/
    └── <run_id>/
        └── <tick:06d>.trendpack.json     # TrendPack.v0
```

---

## Validation

Artifacts can be validated using:
- `abraxas.runtime.artifacts.ArtifactWriter` — ensures deterministic serialization
- Schema-specific loaders in `abraxas.runtime.*` — validate required fields

Example validation:
```python
from abraxas.runtime import load_run_header, verify_run_header

# Load and validate schema
header = load_run_header("runs/my_run.runheader.json")
assert header["schema"] == "RunHeader.v0"

# Verify hash integrity
result = verify_run_header("runs/my_run.runheader.json", expected_sha256)
assert result["valid"]
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-04 | Initial canonical release |

---

**End of Schema Index**
