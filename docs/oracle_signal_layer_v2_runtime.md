# Oracle Signal Layer v2 Runtime

## Chain
1. `OracleSignalInputEnvelope.v2` validation + normalization
2. Hashable core extraction (`signal_sources`, `payload`, bounded `context`, bounded `metadata`)
3. Display-only field split (`display_label`, `operator_note`)
4. Deterministic compression operators (`compress_signal_v0`, `dedupe_signal_items_v0`, `bound_evidence_v0`, `compute_decay_v0`)
5. Authority build (`authority_scope=interpretation_only`)
6. Advisory registry invocation (MIRCL, trend)
7. Final `OracleSignalLayerOutput.v2` assembly with explicit boundary marker

## Boundary law
- Authority terminates at interpretation.
- Advisory attachments are downstream-only and structurally separated under `advisory_attachments`.
- MIRCL/trend cannot mutate authority payload by API shape.

## Computability
- Missing observations -> visible `not_computable_reasons`.
- Missing trend inputs -> `trend` attachment: `status=NOT_COMPUTABLE`, `computable=false`.
- Missing MIRCL-required inputs -> MIRCL attachment remains present as `NOT_COMPUTABLE`.

- Registry and service enforce authority hash checks before/after advisory invocation to detect illegal mutation attempts.

- Output provenance now carries `computable`, `status`, and explicit `not_computable_reasons` for fail-closed visibility.

- Runtime service enforces schema guards against `schemas/oracle_signal_input_envelope.v2.json` and `schemas/oracle_signal_layer_output.v2.json` before/after processing.
