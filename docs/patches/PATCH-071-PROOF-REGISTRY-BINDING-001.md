# PATCH-071 — PROOF-REGISTRY-BINDING-001

## Purpose
Bind PATCH-069 repo proof artifacts and PATCH-070 runtime proof artifact into a deterministic registry.

## Inputs
- out/proof/repo/repo_proof_manifest.latest.json
- out/proof/repo/patch_coverage_map.latest.json
- out/proof/repo/repo_canon_alignment_report.latest.json
- out/proof/repo/repo_proof_receipt.latest.json
- out/proofs/proof_artifact_001.latest.json

## Output
- out/proof/proof_registry.latest.json

## Determinism Rules
- canonical JSON
- sorted keys
- compact separators
- byte-identical reruns

## Authority Boundary
Proof-only. No promotion, runtime mutation, scheduler write, or forecast influence.

## CLI Command
`python scripts/run_proof_registry.py`

## Test Command
`pytest -q tests/test_proof_registry.py`
