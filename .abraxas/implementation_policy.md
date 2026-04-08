# Abraxas Repo-Local Implementation Policy

This shell governs repo-local execution and governance workflows. It does not replace runtime or validator authority.

## Core Principles
- Additive-only patching.
- Deterministic behavior.
- Proof-addressable execution.
- Explicit partial/blocked states when receipts are missing.
- SHADOW / FORECAST separation.
- Fail-closed semantics for readiness, promotion, and closure claims.

## Attestation Discipline
- No attestation by prose.
- No readiness by declaration alone.
- No closure without validator-visible or ledger-visible evidence.
- Memory growth and execution closure are distinct.

## Governance Integrity Rules
- Promotion is reversible.
- Silence is not promotion.
- No derivative surface confers authority.
- Seeded ledger memory does not confer closure.
- Reconciliation is append-only and must never rewrite history.

## Placeholder Rule
Implementation-pending surfaces must be labeled explicitly and remain non-authoritative.
