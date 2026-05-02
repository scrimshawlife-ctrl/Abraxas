# PATCH-073 — OPERATOR-PROOF-STATUS-CARD-001

## Purpose
Convert proof projection truth into an Operator Console-ready status card.

## Input
- out/viz/proof_state.latest.json

## Output
- out/operator/proof_status_card.latest.json

## Logic
- GREEN only when combined_status is LOCAL_CHAIN_PROVEN and pointer_closure is PASS
- otherwise YELLOW or RED based on closure and status conditions

## Guarantees
- projection-derived only
- no promotion authority
- no runtime mutation authority
- no forecast influence authority

## Determinism
- canonical JSON
- sorted keys
- byte-identical reruns

## Commands
- `pytest -q tests/test_operator_proof_status_card.py`
- `python scripts/run_operator_proof_status_card.py`

## Seal
Render truth for operator. Do not grant authority.
