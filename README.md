# Abraxas

Abraxas is a deterministic, proof-bearing runtime for run-linked execution artifacts, validator closure, and operator governance.

## Canonical path first

The canonical runtime spine is:

`ingest -> rune invoke -> artifact emit -> ledger linkage -> validator-visible proof -> operator projection -> attestation`

Run local closure with one command:

```bash
python -m abx.cli proof-run --run-id <RUN_ID>
```

Classify local-vs-promotion readiness with:

```bash
python -m abx.cli promotion-check --run-id <RUN_ID>
```

Evaluate promotion permission policy with:

```bash
python -m abx.cli promotion-policy --run-id <RUN_ID>
```

## Golden-path onboarding

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m abx.cli proof-run --run-id RUN-DEMO-001
python -m abx.cli promotion-check --run-id RUN-DEMO-001
python -m abx.cli promotion-policy --run-id RUN-DEMO-001
```

Make targets:

- `make proof RUN_ID=<RUN_ID>`
- `make promotion-check RUN_ID=<RUN_ID>`
- `make promotion-policy RUN_ID=<RUN_ID>`

Read next:

- `docs/CANONICAL_RUNTIME.md`
- `docs/VALIDATION_AND_ATTESTATION.md`
- `docs/SUBSYSTEM_INVENTORY.md`
- `docs/RELEASE_READINESS.md`

Canonical drift check:

```bash
python scripts/run_governance_lint.py
```


Release candidate checklist:

```bash
make ts-canonical-check
make release-readiness RUN_ID=<RUN_ID>
```

## Surface hierarchy

### Canonical (proof/governance default)

- `aal_core/` (rune execution contract + schema)
- `abx/` (CLI + validator/runtime orchestration)
- `abraxas/runes/` (rune/capability invocation)
- `webpanel/` (canonical operator proof/governance surface)

### Secondary (useful but non-canonical for proof closure)

- `server/`, `client/`, `shared/` TypeScript stack for dashboard/admin/product workflows
- long-tail diagnostic and audit scripts in `scripts/`

## Shared operator projection contract

Canonical projection schema: `OperatorProjectionSummary.v1`.

- Canonical derivation: `abx/operator_projection.py`
- Canonical renderer: `webpanel` (`/runs/{run_id}/projection.json`)
- Secondary aligned renderer/API: TS route `/api/operator/projection/:runId` with shared type `shared/operatorProjection.ts`

## Closure tiers

- **Tier 1 (local canonical closure):** `proof-run` proves deterministic local emit/ledger/validate/operator/attestation traversal.
- **Tier 2 (local promotion readiness):** `promotion-check` reports local promotion state (`LOCAL_ONLY_COMPLETE`, `LOCAL_PROMOTION_READY`, `NOT_COMPUTABLE`).
- **Tier 2.5 (federated readiness):** `promotion-check` also reports federated state (`FEDERATED_READY`, `FEDERATED_INCOMPLETE`, `NOT_COMPUTABLE`) based on explicit external evidence markers.
  - Federated readiness now includes `RemoteEvidenceManifest.v1` bounded aggregation (packet freshness/consistency/partial state) when a remote manifest is declared.
- **Tier 2.75 (promotion policy gate):** `promotion-policy` enforces whether promotion/seal actions are `ALLOWED`, `BLOCKED`, `WAIVED`, or `NOT_COMPUTABLE`.
- **Tier 3 (promotion-grade attestation execution):** `scripts/run_execution_attestation.py` / `make attest` runs acceptance + optional seal, and now fails closed unless Tier 2.75 policy is `ALLOWED` or `WAIVED`.

Tier boundaries: local readiness does not imply federated readiness; readiness does not imply permission; policy gate is the enforcement boundary; Tier 3 is blocked unless policy allows/waives; federated readiness does not imply Tier 3 execution.
Legacy `abx acceptance` remains shadow-diagnostic only by default and is not the canonical Tier 3 promotion path.
`make seal` / `scripts/seal_release.py` remain shadow seal diagnostics and are archive-candidates for promotion execution workflows.
`scripts/run_promotion_pack.py` is shadow/deprecated for canonical promotion execution and requires explicit override (`ABX_ALLOW_SHADOW_PROMOTION_PACK=1`).

## License

A root `LICENSE` file is not currently present. `package.json` declares `MIT` for the TypeScript package only; confirm top-level licensing before redistribution.


## Operator Surfaces

These surfaces are views over canonical truth (proof/readiness/policy/federated evidence), not parallel systems.

- Run console: `/runs/{run_id}/console` + `/api/operator/run/{run_id}`
- Run compare: `/runs/compare?run_a=<A>&run_b=<B>` + `/api/operator/compare/{run_a}/{run_b}`
- Release readiness: `/release/readiness?run_id=<RUN_ID>` + `/api/operator/release-readiness/{run_id}`
- Evidence explorer: `/runs/{run_id}/evidence` + `/api/operator/evidence/{run_id}`
