# OSL v2 DROP Audit Evidence

## Schemas
- `schemas/input_envelope.v2.json`
- `schemas/oracle_output.v2.json`

## Tests added
- `tests/test_osl_v2_schema.py`: validates InputEnvelope.v2 and OracleOutput.v2 schemas; rejects extra metadata fields.
- `tests/test_osl_v2_hashing.py`: deterministic stable hashing and input envelope hashing excludes timestamps.
- `tests/test_osl_v2_operators.py`: boundedness/determinism for extract/compress/propose, missing extract error handling, enterprise-tier suppression, advisory-only actions.
- `tests/test_osl_v2_stability.py`: per-cycle policy_hash presence and drift_class behavior (nondeterminism/policy_change).
- `tests/test_osl_v2_suppression.py`: explicit suppression and not_computable markers for missing inputs or drift.

## Operator contract enforcement locations
- `webpanel/structure_extract.py`: MAX_NODES/MAX_METRICS/MAX_REFS/MAX_UNKNOWNS caps in `walk_payload` and `detect_unknowns`.
- `webpanel/compress_signal.py`: plan pressure clamping; next_questions bounded to 6.
- `webpanel/propose_actions.py`: bounded action list and enterprise-tier suppression.
- `webpanel/stability.py` and `webpanel/osl_v2.py`: stable hashing utilities and input envelope hashing for drift/stability.
