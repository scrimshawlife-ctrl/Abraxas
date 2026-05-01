# PATCH-065 — AAL-VIZ-INTERACTION-POLICY-LEDGER-001

## purpose
Persist interaction policy governance state into a deterministic ledger run with promotion gate evaluation and passive drift hooks.

## authority boundary
Governance-layer only: no interaction execution, no event binding, no runtime activation, no animation, no physics, no browser mutation.

## ledger function
- computes deterministic entry IDs and entry hashes
- dedupes by entry ID
- preserves prior entries
- computes deterministic run hash

## promotion gate
Evaluates runtime-disabled policy, overlap constraints, and frontend lockfile presence to emit `review_ready` or `blocked` state.

## drift hooks
Defines passive scans only: runtime API scan, overlap scan, authority regression scan, lockfile presence scan, and component source hash drift scan.

## next patch
PATCH-066.
