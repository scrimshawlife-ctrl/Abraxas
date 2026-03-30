# Release Readiness (Pre-Feature Baseline)

This surface defines the **bounded release checklist** for the canonical spine.

## Canonical release validation command

```bash
python scripts/run_release_readiness.py --run-id RUN-PREFEATURE-001 --base-dir .
```

The command emits `out/release/release-readiness-<run_id>.json` (`ReleaseReadinessReport.v1`) and classifies status as `READY` or `NOT_READY`.

## What must pass

- docs/help canonical surfaces exist:
  - `README.md`
  - `docs/CANONICAL_RUNTIME.md`
  - `docs/VALIDATION_AND_ATTESTATION.md`
  - `docs/SUBSYSTEM_INVENTORY.md`
  - `docs/RELEASE_READINESS.md`
- governance drift guard: `python scripts/run_governance_lint.py`
- canonical TS sanity: `npx tsc -p tsconfig.canonical.json --pretty false`
- canonical runtime sequence:
  - `python -m abx.cli proof-run --run-id <RUN_ID> --base-dir .`
  - `python -m abx.cli promotion-check --run-id <RUN_ID> --base-dir .`
  - `python -m abx.cli promotion-policy --run-id <RUN_ID> --base-dir .`
  - `python scripts/run_execution_attestation.py <RUN_ID> --base-dir .`
- focused policy/federation/projection tests

## Release taxonomy

- **Release-grade canonical**: proof-run, promotion-check, promotion-policy, policy-gated Tier 3 attestation, governance lint, canonical TS sanity.
- **Governed partial**: federated evidence v1 aggregation is bounded and deterministic, but not a full distributed trust network.
- **Shadow / diagnostic**: `abx.cli acceptance`, `scripts/run_promotion_pack.py`, and `scripts/seal_release.py`.

## Known non-blocking limits

- Tier 3 may intentionally fail closed when policy blocks federation requirements for a given run fixture.
- Repo-wide TS debt outside `tsconfig.canonical.json` is tracked separately and intentionally out of scope for this pass.
- Federation support is v1 manifest aggregation/consistency/freshness classification, not live remote handshakes or cryptographic federation trust.
