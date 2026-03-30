# Canonical Runtime and Proof Spine

This document defines the default Abraxas execution and the bridge from local closure to promotion-grade closure.

## Canonical Spine (default)

`ingest -> rune invoke -> artifact emit -> ledger link -> execution validator -> operator proof projection -> attestation`

Tier 1 command:

```bash
python -m abx.cli proof-run --run-id <RUN_ID>
```

Tier 2 bridge command:

```bash
python -m abx.cli promotion-check --run-id <RUN_ID>
```

Tier 2.75 policy gate command:

```bash
python -m abx.cli promotion-policy --run-id <RUN_ID>
```

## Closure tier guarantees

### Tier 1 — Local canonical closure (`proof-run`)

Guarantees:

- deterministic local rune artifact emission,
- run-linked ledger record,
- validator artifact generation,
- operator projection artifact,
- local canonical attestation artifact.

Does **not** guarantee promotion-grade acceptance/seal evidence.

### Tier 2 — Local promotion readiness bridge (`promotion-check`)

Guarantees deterministic classification of local promotion posture:

- `LOCAL_ONLY_COMPLETE`
- `LOCAL_PROMOTION_READY`
- `NOT_COMPUTABLE`

### Tier 2.5 — Federated readiness bridge (`promotion-check`)

Adds federated-awareness without simulating distributed systems:

- `FEDERATED_READY`
- `FEDERATED_INCOMPLETE`
- `NOT_COMPUTABLE`

Federated readiness requires explicit external evidence markers (external attestation refs, federated ledger IDs, and remote validation/attestation confirmation fields).
If a remote evidence manifest is declared, it is structurally verified via `RemoteEvidenceManifest.v1` (presence, schema id, origin, packet id/ref/status fields).

### Tier 2.75 — Promotion policy decision gate (`promotion-policy`)

Enforces permission semantics over Tier 1 / Tier 2 / Tier 2.5 evidence:

- `ALLOWED`
- `BLOCKED`
- `WAIVED`
- `NOT_COMPUTABLE`

Readiness is classification; policy is permission.

### Tier 3 — Promotion-grade closure execution (`run_execution_attestation.py` / `make attest`)

Runs acceptance suite and optional seal requirements to provide stronger promotion execution evidence.
Tier 3 is policy-gated: execution must fail closed unless Tier 2.75 returns `ALLOWED` or `WAIVED`.
Tier 3 artifacts must surface the governing policy decision, reason codes/blockers, waiver state, and federation requirement fields.

## Canonical run_id propagation requirements

`run_id` must be present and unchanged across:

- rune execution envelope (`run_id`),
- ledger event rows (`run_id`, provenance `run_id`),
- validator artifact (`runId`),
- local attestation (`run_id`),
- promotion readiness artifact (`run_id`),
- promotion attestation (`run_id`) when present.

## Surface hierarchy (canonical vs secondary)

### Canonical

- Python runtime contracts + wrappers: `aal_core/`, `abraxas/runes/`, `abx/`
- Canonical proof commands: `abx.cli proof-run`, `abx.cli promotion-check`, `abx.cli promotion-policy`
- Validator/attestation/readiness artifacts: `out/validators`, `out/attestation`, `out/promotion`
- Operator proof/governance surface: `webpanel/`

### Secondary (non-canonical for proof closure)

- TypeScript stack: `server/`, `client/`, `shared/` (dashboard/admin/product surfaces)
- Long-tail diagnostics in `scripts/` not required for default proof classification
- Legacy acceptance/seal helpers are shadow diagnostics unless routed through canonical Tier 3

## Golden path for contributors

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m abx.cli proof-run --run-id RUN-DEMO-001
python -m abx.cli promotion-check --run-id RUN-DEMO-001
python -m abx.cli promotion-policy --run-id RUN-DEMO-001
```

Optional promotion-grade upgrade:

```bash
python scripts/run_execution_attestation.py RUN-DEMO-001
```


## Shared operator projection contract

`OperatorProjectionSummary.v1` is the canonical proof/promotion meaning surface.

- Python derivation source of truth: `abx/operator_projection.py`
- Webpanel canonical projection endpoint: `/runs/{run_id}/projection.json`
- TS secondary aligned endpoint: `/api/operator/projection/:runId`
- TS shared type: `shared/operatorProjection.ts`

Both surfaces may differ visually, but must preserve this semantic contract.


## Tier boundary truth

- local readiness does not imply federated readiness
- readiness does not imply permission
- federated readiness does not imply Tier 3 execution
- policy gate is the enforcement boundary before Tier 3
- Tier 3 execution is blocked unless policy is `ALLOWED` or `WAIVED`
- Tier 3 remains heavy and may include external execution surfaces
- legacy acceptance command (`abx.cli acceptance`) is intentionally shadow-only by default
- legacy seal diagnostics (`make seal` / `scripts/seal_release.py`) are non-canonical and archive-candidates for promotion workflows


## Release-readiness baseline

Use `python scripts/run_release_readiness.py --run-id <RUN_ID> --base-dir .` (or `make release-readiness RUN_ID=<RUN_ID>`) to run canonical pre-feature checks, including governance lint, canonical TS sanity (`tsconfig.canonical.json`), proof/run readiness flow, policy gate, and focused tests.


## Operator Surfaces

Operator surfaces are read/compare/explain layers over canonical artifacts and policy outcomes.

- `/runs/{run_id}/console`: unified run summary (projection, readiness, policy, federated summary, execution state, blockers, artifact refs).
- `/runs/compare?run_a=<A>&run_b=<B>`: policy/readiness/federation/execution deltas across runs.
- `/release/readiness?run_id=<RUN_ID>`: rendered `ReleaseReadinessReport.v1` checklist and issues.
- `/runs/{run_id}/evidence`: federated evidence state + packet inspection view.

Secondary API mirrors:
- `/api/operator/run/{run_id}`
- `/api/operator/compare/{run_a}/{run_b}`
- `/api/operator/release-readiness/{run_id}`
- `/api/operator/evidence/{run_id}`
