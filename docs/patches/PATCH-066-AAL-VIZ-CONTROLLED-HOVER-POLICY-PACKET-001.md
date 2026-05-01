# PATCH-066 — AAL-VIZ-CONTROLLED-HOVER-POLICY-PACKET-001

## purpose
Generate a deterministic review-only controlled hover policy packet from policy, ledger, provisioning, CI proof, and component manifest artifacts.

## authority boundary
Packet-generation only. No runtime hover enablement, no event binding, no component mutation, no animation/runtime loop activation.

## gate dependency
Status is blocked unless PATCH-064D CI proof reports `frontend_execution=verified` and policy ledger is `review_ready`.

## status logic
- `not_computable` on malformed/missing required input hashes
- `blocked` when CI proof unverified, ledger not ready, hover disallowed, or authority lock invalid
- `review_ready` only when all readiness checks pass

## hover contract
Defines conceptual pointer hover candidate only; runtime and binding remain disabled.

## forbidden runtime APIs
`requestAnimationFrame`, `setInterval`, `setTimeout`, `Math.random`, `Date.now`.

## drift hooks
`hover_runtime_api_scan`, `event_listener_binding_scan`, `component_source_mutation_scan`, `authority_regression_scan`, `frontend_execution_regression_scan`.

## guarantee
No runtime / no event binding / no component mutation.

## next patch
PATCH-067 — AAL-VIZ-CONTROLLED-HOVER-RUNTIME-SCAFFOLD-001, only after PATCH-066 is `review_ready` and frontend execution is verified.
