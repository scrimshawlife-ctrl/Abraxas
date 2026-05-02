# PATCH-069 — REPO-HASH-PROOF-MANIFEST-001

## Purpose
Create deterministic, proof-only repository hash manifests and canon drift artifacts.

## Authority Boundary
- runtime_mutation: false
- promotion_granted: false
- scheduler_write: false
- source_weight_mutation: false
- activation_allowed: false
- authority_boundary: proof_only

## Generated Artifact Paths
- out/proof/repo/repo_proof_manifest.latest.json
- out/proof/repo/patch_coverage_map.latest.json
- out/proof/repo/repo_canon_alignment_report.latest.json
- out/proof/repo/repo_proof_receipt.latest.json

## CLI Command
`python scripts/run_repo_proof_manifest.py --repo-root . --notion-patch-floor PATCH-067+ --out-dir out/proof/repo`

## Test Command
`PYTHONPATH=. pytest -q tests/test_repo_proof_manifest.py`

## Drift Classes
- aligned
- repo_ahead
- notion_ahead
- diverged
- not_computable

## Proof-Only Seal
Proof infrastructure only. No runtime mutation, promotion, scheduler write, source-weight mutation, or activation.
