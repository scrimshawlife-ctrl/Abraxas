# Oracle Signal Layer v2 Receipts

## Emitted artifacts
- Runtime artifact: `out/oracle_signal_layer_v2/oracle_signal_layer_output_<run_id>.json`
- Invariance artifact: `out/oracle_signal_layer_v2/oracle_invariance_<run_id>.json`
- Validator summary: `out/oracle_signal_layer_v2/oracle_validator_summary_<run_id>.json`
- Ledger row append: `out/ledger/oracle_signal_layer_v2_runs.jsonl`

## Hashes
Validator summary includes digest triplet:
- `input_hash`
- `authority_hash`
- `full_hash`

## Commands
```bash
PYTHONPATH=. python scripts/run_oracle_signal_layer_v2.py --input docs/artifacts/oracle_signal_input_envelope_sample.v2.json
PYTHONPATH=. python scripts/run_oracle_signal_layer_v2_invariance.py --input docs/artifacts/oracle_signal_input_envelope_sample.v2.json --repeats 12
```

- Runtime artifact provenance includes `computable/status/not_computable_reasons` for validator-visible non-computable paths.
