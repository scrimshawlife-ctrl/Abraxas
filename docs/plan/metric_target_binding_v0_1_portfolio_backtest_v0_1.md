# Metric-Target Binding v0.1 + Portfolio Backtesting v0.1 — Patch Plan

**Status**: Active Development  
**Version**: 0.1  
**Created**: 2025-12-26  
**Purpose**: Bind metric candidates to explicit portfolio targets and score deltas deterministically across case portfolios.

---

## Objectives

1. **Explicit targets** for every MetricCandidate (portfolios, horizons, metrics, thresholds).
2. **Portfolio-level sandbox evaluation** (case sets, not single cases).
3. **Deterministic aggregate scores** with a single normalized shape.
4. **Ledger + report outputs** for promotion gates and rent.

---

## Scope

### Additions

- `data/backtests/portfolios/portfolios_v0_1.yaml`  
  - Portfolio definitions for short-term core, long-horizon integrity, slang term emergence.
- `abraxas/backtest/portfolio.py`  
  - Load portfolios, select cases deterministically.
- `abraxas/scoreboard/aggregate.py`  
  - Normalize backtest results into a standard score shape.
- `docs/specs/portfolio_backtesting_v0_1.md`

### Changes

- `abraxas/evolution/schema.py`
  - Add `CandidateTarget` + bind into `MetricCandidate`.
  - Extend `SandboxResult` with portfolio results + pass_gate.
- `abraxas/evolution/candidate_generator.py`
  - Bind targets for AALMANAC/MW/INTEGRITY candidate rules.
- `abraxas/evolution/sandbox.py`
  - Add `run_sandbox_portfolios` + portfolio report artifacts.
- `abraxas/evolution/promotion_gate.py`
  - Gate promotion on portfolio pass results + rent manifest presence.
- `abraxas/evolution/store.py`
  - Append portfolio score delta hash to sandbox ledger.

---

## Determinism Constraints

- **No network calls** during sandbox.
- **Stable ordering** by case_id for portfolio selection.
- **Stable score delta hashing** via canonical JSON.
- **Append-only, chained ledgers** preserved.

---

## Tests

- `tests/test_portfolio_case_selection.py`
- `tests/test_score_aggregate_shape.py`
- `tests/test_sandbox_portfolio_thresholds.py`
- `tests/test_no_regress_guardrail.py`
- `tests/golden/portfolios/portfolio_sandbox_report.json`

---

## Outputs

- `out/runs/<run_id>/evolution/portfolio_sandbox_report.json`
- `out/runs/<run_id>/evolution/portfolio_sandbox_report.md`
- `out/reports/portfolio_sandbox_<sandbox_id>.json`
- `out/reports/portfolio_sandbox_<sandbox_id>.md`

