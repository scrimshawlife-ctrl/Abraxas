# Subsystem Maturity Inventory

High-impact subsystem maturity snapshot for canonical convergence.

| Path / package | Role | Primary entrypoint | Proof relevance | Coverage signal | Maturity class | Rationale |
|---|---|---|---|---|---|---|
| `aal_core/` | Rune envelope/schema/catalog contracts | `aal_core/runes/executor.py` | Direct: canonical execution artifact contract | schema + focused tests in repo | Canon-Active | Deterministic envelope is explicit and reused by runtime surfaces. |
| `abx/` | Canonical CLI/runtime orchestration | `abx/cli.py` | Direct: proof command, validator, attestation orchestration | broad `tests/` footprint including validator/operator tests | Canon-Active | Most stable execution and governance entrypoints live here. |
| `abraxas/runes/` | Rune invocation and capability binding | `abraxas/runes/invoke.py` | Direct: run-linked rune invocation and ledger recording | targeted tests + schema validation hooks | Canon-Active | Core invocation contract with explicit failure/stub handling. |
| `webpanel/` | Canonical operator/governance/proof interface | `webpanel/app.py` | Direct: operator proof inspection and governance actions | dedicated webpanel tests + operator console tests | Canon-Active | Best aligned operator proof surface; should remain primary for closure workflows. |
| `scripts/run_execution_validator.py` + `scripts/run_execution_attestation.py` | Validator and attestation gates | script CLIs | Direct: validator-visible evidence closure | dedicated tests (`test_execution_validator`, `test_execution_attestation_runner`) | Governed Partial | Strong core behavior, but broader script ecosystem creates discovery noise. |
| `server/` | TS API and product/dashboard backend | `server/index.ts` | Indirect: exposes artifacts/governance data but not canonical closure path | TS checks/tests available | Governed Partial | Valuable product/admin APIs; not the canonical proof spine. |
| `client/` | TS React dashboard UI | `client/src/App.tsx` | Indirect | TS checks/tests available | Shadow | Useful surface but overlaps with operator narratives; keep secondary to webpanel for proof ops. |
| `shared/` | Shared TS contracts/types | package imports in server/client | Indirect but now includes projection contract alignment | typed schemas + TS compile checks | Governed Partial | Supports TS stack consistency; includes `shared/operatorProjection.ts` for proof/promotion semantics. |
| `tools/acceptance/` | Determinism/acceptance harness | `tools/acceptance/run_acceptance_suite.py` | Promotion-grade proof support | dedicated acceptance tests | Governed Partial | Critical for higher assurance, but heavier than default contributor flow. |
| `scripts/` long-tail audit suite | Domain audits/scorecards/diagnostics | many script entrypoints | Mixed | mixed test linkage | Shadow / Scaffold (mixed) | Contains many useful gates, but default vs optional boundaries were unclear before this pass. |

## Canon compression notes

- Canonical proof-bearing spine should route through `abx.cli proof-run` and `webpanel`.
- TS stack remains important but secondary for validator closure operations.
- Long-tail scripts should be invoked intentionally, not treated as default onboarding requirements.

## Tier 3 path audit + containment (2026-03-30)

| Path | Classification | Triage decision | Containment status | Guidance |
|---|---|---|---|---|
| `scripts/run_execution_attestation.py` | `CANONICAL_GATED` | `REDIRECT_TO_CANONICAL` | Tier 2.75 policy precondition enforced (`ALLOWED/WAIVED` only) | Use this for promotion-grade heavy execution. |
| `make attest` | `CANONICAL_WRAPPER` | `REDIRECT_TO_CANONICAL` | Wrapper over `scripts/run_execution_attestation.py` | Preferred shell entrypoint for make users. |
| `abx.cli acceptance` + `scripts/abx_acceptance.sh` | `SHADOW_DIAGNOSTIC` | `STABILIZE_SHADOW` | Refuses by default; explicit env override required (`ABX_ALLOW_SHADOW_ACCEPTANCE=1`) | Not valid as a production Tier 3 promotion path. |
| `scripts/seal_release.py` / `make seal` | `SHADOW_DIAGNOSTIC` | `DEPRECATE_OR_RETIRE` | Kept for artifact-seal diagnostics; not policy-gated promotion execution | Use only for seal diagnostics, not promotion decisions. |
| `tools/acceptance/run_acceptance_suite.py` | `SHADOW_DIAGNOSTIC` | `STABILIZE_SHADOW` | Harness only; consumed by canonical Tier 3 runner; stabilized for direct shadow invocation | Invoke directly only for targeted acceptance diagnostics. |
| `scripts/run_execution_validator.py` | `SHADOW_DIAGNOSTIC` | `STABILIZE_SHADOW` | Validator helper; not a full promotion execution path | Use standalone for validator-only checks. |
| `scripts/run_promotion_pack.py` | `SHADOW_DIAGNOSTIC` | `DEPRECATE_OR_RETIRE` | Legacy promotion evidence pack helper; not policy-gated execution; explicit override required | Prefer canonical proof/readiness/policy + attestation flow. |
| `scripts/run_promotion_audit.py` | `SHADOW_DIAGNOSTIC` | `STABILIZE_SHADOW` | Audit-only reporting path | Use for governance diagnostics only. |
| `scripts/run_receiver_acceptance_audit.py` | `SHADOW_DIAGNOSTIC` | `STABILIZE_SHADOW` | Audit-only acceptance reporting path | Use for acceptance diagnostics only. |
| `scripts/run_baseline_seal.py` | `SHADOW_DIAGNOSTIC` | `DEPRECATE_OR_RETIRE` | Baseline seal snapshot helper; not canonical execution | Archive candidate for promotion workflows. |
| `scripts/run_closure_generalized_attestation.py` | `SHADOW_DIAGNOSTIC` | `STABILIZE_SHADOW` | Closure milestone attestation helper, separate from canonical Tier 3 run execution | Use for closure milestone diagnostics only. |

Any future Tier-3-like execution entrypoint should be either a thin wrapper over the canonical gated path or explicitly marked shadow/diagnostic.


## Release prep surfaces

- `scripts/run_release_readiness.py` + `docs/RELEASE_READINESS.md` are release-grade canonical check surfaces.
- `tsconfig.canonical.json` + `make ts-canonical-check` are governed TS sanity surfaces for canonical projection semantics (not a repo-wide TS cleanup promise).
