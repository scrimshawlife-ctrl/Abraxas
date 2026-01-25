# Cap Golden State

## Golden State Meaning
The Golden State is the current, capped baseline for Abraxas. Manual edits to Canon are forbidden by process. Any change that lands in Canon must pass through Upgrade Spine v1 and its governance gates.

## Golden Rule (Cap)
- **No manual mutations** to Canon paths.
- **Only Upgrade Spine promotions** may land changes.

## Upgrade Spine Commands (Deterministic Flow)
```bash
python tools/run_upgrade_spine.py --collect
python tools/run_upgrade_spine.py --apply <candidate_id>
python tools/run_upgrade_spine.py --promote <candidate_id>
```

## One-Liner Genesis Proof
```bash
python tools/genesis_proof_upgrade_spine.py
```

## Integrity Verification
- Verify artifact bundle hashes in `.aal/artifacts/upgrade_spine/<date>/<candidate_id>/provenance.json`.
- Validate that `patch.diff` hash matches the provenance bundle.
- Confirm ledger append-only writes in `out/upgrade_spine/ledger.jsonl`.
