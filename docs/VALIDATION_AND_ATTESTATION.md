# Validation and Attestation Surfaces

This inventory compresses validation and attestation into canonical tiers.

## Tier 1 — Local canonical closure

Command:

```bash
python -m abx.cli proof-run --run-id <RUN_ID>
```

Outputs:

- runtime spine artifact
- run-linked ledger row
- validator artifact
- operator proof projection
- canonical local attestation

This proves deterministic local closure traversal only.

## Tier 2 — Local promotion readiness bridge

Command:

```bash
python -m abx.cli promotion-check --run-id <RUN_ID>
```

Local promotion state contract:

- `LOCAL_ONLY_COMPLETE`
- `LOCAL_PROMOTION_READY`
- `NOT_COMPUTABLE`

This tier confirms local promotion posture from local artifacts.

## Tier 2.5 — Federated readiness bridge

Evaluated by the same `promotion-check` output via:

- `FEDERATED_READY`
- `FEDERATED_INCOMPLETE`
- `NOT_COMPUTABLE`

Federated readiness requires explicit external evidence markers (e.g. external attestation refs, federated ledger IDs, remote validation/attestation confirmations). If absent, state must remain incomplete.
When `remote_evidence_manifest` is declared, the manifest is verified using `RemoteEvidenceManifest.v1` bounded semantics (schema/run_id normalization, packet status classification, freshness checks, and inconsistency detection).
Remote evidence status feeds Tier 2.5 and Tier 2.75 as:
- `NOT_DECLARED`
- `MISSING`
- `MALFORMED`
- `VALID`

Federated evidence aggregate summary is additionally classified as:
- `ABSENT`
- `VALID`
- `PARTIAL`
- `INCONSISTENT`
- `MALFORMED`
- `STALE`

## Tier 2.75 — Promotion policy gate

Command:

```bash
python -m abx.cli promotion-policy --run-id <RUN_ID>
```

Decision contract:

- `ALLOWED`
- `BLOCKED`
- `WAIVED`
- `NOT_COMPUTABLE`

This tier separates readiness from permission and enforces federated requirements (unless explicitly waived).

## Tier 3 — Promotion-grade attestation execution

Commands:

- `python scripts/run_execution_attestation.py <RUN_ID> [--with-seal]`
- `make attest RUN_ID=<RUN_ID> [WITH_SEAL=1]`

This tier runs acceptance and optional seal to support promotion-grade closure execution.
Tier 3 is hard-gated by Tier 2.75 policy decision:

- proceed only for `ALLOWED` or `WAIVED`,
- fail closed for `BLOCKED` and `NOT_COMPUTABLE`,
- include policy provenance in execution attestation artifacts.

## Tier boundaries (non-negotiable)

- Local readiness **does not imply** federated readiness.
- Readiness **does not imply** permission to promote/seal.
- Tier 2.75 policy gate is the permission boundary before execution.
- Tier 3 execution is blocked unless policy is `ALLOWED` or `WAIVED`.
- Federated readiness **does not imply** Tier 3 seal execution.
- Tier 3 can remain heavier/external and must not be simulated.

## Canonical/default vs optional script classes

### Canonical/default-worthy

- `python -m abx.cli proof-run --run-id <RUN_ID>`
- `python -m abx.cli promotion-check --run-id <RUN_ID>`
- `python -m abx.cli promotion-policy --run-id <RUN_ID>`
- `scripts/run_execution_validator.py`
- `scripts/run_execution_attestation.py`

### Diagnostic/shadow/optional

- Most `scripts/run_*_audit.py` scorecards and domain audits
- Scenario-specific proof-chain checks (`scripts/run_proof_chain_validation.py`)
- Specialized closure summaries (`scripts/run_closure_summary.py`)
- `abx.cli acceptance` / `scripts/abx_acceptance.sh` (shadow-only; explicit env override required; stabilized for controlled diagnostic use)
- `tools/acceptance/run_acceptance_suite.py` (shadow harness; stabilized for direct invocation from non-repo cwd)
- `scripts/seal_release.py` / `make seal` (seal artifact diagnostics, not canonical promotion execution; deprecate/archive candidate for promotion workflows)
- `scripts/run_promotion_pack.py` (shadow/deprecated; explicit override required via `ABX_ALLOW_SHADOW_PROMOTION_PACK=1`)

## Governance lint and anti-regrowth

Use consolidated lint to prevent canonical drift and unclassified heavy-path regrowth:

```bash
python scripts/run_governance_lint.py
```

Lint checks include:
- canonical command surfacing (`proof-run`, `promotion-check`, `promotion-policy`, canonical Tier 3 path),
- tier language coherence (Tier 1 / 2 / 2.5 / 2.75 / 3),
- shadow/deprecate labels in inventory/docs,
- classification coverage for discovered heavy/promotion/seal/acceptance/attestation scripts,
- touched-surface projection token parity between `shared/operatorProjection.ts` and `server/routes.ts`.

## Operator projection contract note

`OperatorProjectionSummary.v1` carries Tier 1, Tier 2, Tier 2.5, and Tier 2.75 policy state in one bounded object. Webpanel is canonical; TS remains secondary but semantically aligned.


## Pre-feature release checklist

Run:

```bash
python scripts/run_release_readiness.py --run-id <RUN_ID> --base-dir .
```

This emits `ReleaseReadinessReport.v1` and distinguishes blocking failures from expected fail-closed Tier 3 policy blocks for non-federated fixtures.
