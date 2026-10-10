# Decisions

Dated decision log. Newest first. Each entry records what was decided and what stays open.

## D-2026-10-10: forecasting direction follow-ups

Decided by Danny, 2026-10-10 10:47 AM PT.

1. **Canonical repo.** Zero-State-LLC/Abraxas is canonical for code, runtime and the forecast record. Zero-State-LLC/Abraxas-v2.0 is doctrine only.
2. **Memetic operations allowed later, with taint flags.** Any forecast a campaign could have influenced is flagged in the ledger, scored separately, and never counts as independent confirmation. Operations stay off until the ledger taint fields exist.
3. **Roadmap milestones.** The CI-streak and public-beta milestones in ROADMAP.md are replaced by the S1 (forecast record and evals) and S2 (scored engine) gates.
4. **aether deferred.** `aether` is dropped from the active architecture until image memes are approved. The manifest entry and refusing provider are unchanged.
5. **Resumption rule.** After the new-engine freeze ends on 2026-11-09, new work follows the four-part rule in [DIRECTION.md](DIRECTION.md).
6. **Drift fixes.** README engine count corrected from "5 live, 5 planned" to 9 live and 1 planned. The `VERSION` file (2.2.0) is aligned with the canon version 2.1.0 used by `.abraxas/gates.json`, `pyproject.toml` and the README badge.

Still open:
- Noema live-agent population target (Noema lab gate 1).
- Model go/no-go bar (minimum settled examples and Brier margin), to be fixed before S2 ends.
