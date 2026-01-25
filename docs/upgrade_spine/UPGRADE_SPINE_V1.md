# Upgrade Spine v1

## Architecture (Shadow → Candidate → Sandbox → Gates → Promote/Archive)

1. **Shadow + Loop Outputs (Observation Only)**
   - EvoGate reports, evolution candidates, shadow summaries, rent check reports, and drift summaries are harvested as *inputs only*.
   - Shadow lane artifacts never write to Canon; they only provide evidence.

2. **Candidate Normalization**
   - Each loop output is mapped into a single `UpgradeCandidate` schema.
   - Every candidate is content-hashed (`candidate_id`) and recorded in an append-only ledger.

3. **Sandbox Application**
   - Patch plans apply in an isolated sandbox (git worktree or temp copy).
   - No modifications occur on the main working tree during apply/gate runs.

4. **Gated Validation**
   - Schema validation (UpgradeCandidate).
   - Dozen-run invariance via the acceptance suite.
   - Rent enforcement via `abx rent-check`.
   - Missing-input enforcement (NOT_COMPUTABLE blocks promotion).

5. **Promote or Archive**
   - Promotion writes provenance + artifact bundle and applies the patch diff.
   - Archive writes ledger entries with explicit reasons.

## Safety Rules

- **Incremental Patch Only**: Upgrades apply via patch plans; no rewrites.
- **Dual-Lane Discipline**: Shadow evidence never mutates Canon directly.
- **Determinism**: All IDs and inputs are content-hashed.
- **Append-Only**: Candidate, decision, and provenance entries are immutable.
- **Rent First**: Any candidate failing rent or invariance gates is archived.

## CLI Usage

```bash
# Collect candidates
python tools/run_upgrade_spine.py --collect

# Evaluate a candidate (preflight)
python tools/run_upgrade_spine.py --evaluate <candidate_id>

# Apply + gate in sandbox (no auto-commit)
python tools/run_upgrade_spine.py --apply <candidate_id>

# Promote a candidate if gates pass
python tools/run_upgrade_spine.py --promote <candidate_id>
```

## Extending with New Loop Sources

1. Add a thin adapter in `server/abraxas/upgrade_spine/adapters/`.
2. Map outputs into the `UpgradeCandidate` schema.
3. Register adapter output in `collect_candidates()` for deterministic ordering.
4. Ensure missing inputs emit NOT_COMPUTABLE with provenance.
