"""
Failure Analyzer for Active Learning Loops.

Deterministic analysis of backtest failures (MISS/ABSTAIN).
No ML, no guessing - just gap analysis between expectations and observations.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from abraxas.backtest.event_query import SignalEvent, load_domain_ledgers
from abraxas.backtest.schema import (
    BacktestCase,
    BacktestResult,
    BacktestStatus,
    Confidence,
    TriggerKind,
)
from abraxas.learning.schema import (
    FailureAnalysis,
    IntegrityConditions,
    SignalGaps,
    TemporalGaps,
    UnmetTrigger,
)
from abraxas.core.provenance import hash_canonical_json


class FailureAnalyzer:
    """
    Deterministic failure analyzer.

    Analyzes backtest failures to identify gaps between expectations and reality.
    """

    def __init__(
        self,
        output_dir: str | Path = "out/reports",
        ledger_path: str | Path = "out/learning_ledgers/failure_analyses.jsonl",
    ):
        """
        Initialize failure analyzer.

        Args:
            output_dir: Directory for failure analysis artifacts
            ledger_path: Path to failure analysis ledger
        """
        self.output_dir = Path(output_dir)
        self.ledger_path = Path(ledger_path)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def analyze(
        self,
        case: BacktestCase,
        result: BacktestResult,
        events: List[SignalEvent],
        ledgers: Dict[str, List[Dict[str, Any]]],
    ) -> FailureAnalysis:
        """
        Deterministic failure analysis.

        No ML, no guessing. Just:
        - What was expected (triggers)
        - What was observed (events/ledgers)
        - What was missing (gap analysis)

        Args:
            case: Backtest case specification
            result: Backtest result (MISS or ABSTAIN)
            events: Signal events in evaluation window
            ledgers: Loaded ledgers

        Returns:
            FailureAnalysis artifact
        """
        failure_id = f"failure_{case.case_id}_{result.run_id}"

        # Analyze unmet triggers
        unmet_triggers = self._analyze_unmet_triggers(case, result, events, ledgers)

        # Analyze hit falsifiers (if any)
        hit_falsifiers = self._analyze_hit_falsifiers(case, result, events, ledgers)

        # Analyze signal availability gaps
        signal_gaps = self._analyze_signal_gaps(case, events, ledgers)

        # Analyze integrity conditions
        integrity_conditions = self._analyze_integrity_conditions(events, ledgers)

        # Analyze temporal gaps
        temporal_gaps = self._analyze_temporal_gaps(ledgers)

        # Generate deterministic hypothesis
        hypothesis = self._generate_hypothesis(
            case, result, unmet_triggers, signal_gaps, integrity_conditions
        )

        # Suggest adjustments
        suggested_adjustments = self._suggest_adjustments(
            case, result, unmet_triggers, signal_gaps, integrity_conditions
        )

        return FailureAnalysis(
            failure_id=failure_id,
            case_id=case.case_id,
            run_id=result.run_id,
            backtest_result={
                "status": result.status.value,
                "score": result.score,
                "confidence": result.confidence.value,
            },
            unmet_triggers=unmet_triggers,
            hit_falsifiers=hit_falsifiers,
            signal_gaps=signal_gaps,
            integrity_conditions=integrity_conditions,
            temporal_gaps=temporal_gaps,
            hypothesis=hypothesis,
            suggested_adjustments=suggested_adjustments,
        )

    def _analyze_unmet_triggers(
        self,
        case: BacktestCase,
        result: BacktestResult,
        events: List[SignalEvent],
        ledgers: Dict[str, List[Dict[str, Any]]],
    ) -> List[UnmetTrigger]:
        """Identify which triggers were not satisfied."""
        unmet = []

        # Check any_of triggers
        for trigger in case.triggers.any_of:
            if trigger.kind == TriggerKind.TERM_SEEN:
                term = trigger.params.get("term", "").lower()
                min_count = trigger.params.get("min_count", 1)

                actual_count = sum(
                    1 for event in events if term in event.text.lower()
                )

                if actual_count < min_count:
                    unmet.append(
                        UnmetTrigger(
                            kind="term_seen",
                            expected={"term": term, "min_count": min_count},
                            actual={"count": actual_count},
                        )
                    )

            elif trigger.kind == TriggerKind.MW_SHIFT:
                min_shifts = trigger.params.get("min_shifts", 1)
                threshold = trigger.params.get("threshold", 0.5)

                # Count MW shifts in ledger
                mw_ledger = ledgers.get("mw_ledger", [])
                shift_count = sum(
                    1
                    for entry in mw_ledger
                    if entry.get("shift_magnitude", 0) >= threshold
                )

                if shift_count < min_shifts:
                    unmet.append(
                        UnmetTrigger(
                            kind="mw_shift",
                            expected={"min_shifts": min_shifts, "threshold": threshold},
                            actual={"shift_count": shift_count},
                        )
                    )

            elif trigger.kind == TriggerKind.INDEX_THRESHOLD:
                index = trigger.params.get("index")
                gte = trigger.params.get("gte")

                # Find max index value in integrity ledger
                integrity_ledger = ledgers.get("integrity_ledger", [])
                max_index = max(
                    (
                        entry.get("indices", {}).get(index, 0)
                        for entry in integrity_ledger
                    ),
                    default=0,
                )

                if max_index < gte:
                    unmet.append(
                        UnmetTrigger(
                            kind="index_threshold",
                            expected={"index": index, "gte": gte},
                            actual={"max_value": max_index},
                        )
                    )

        return unmet

    def _analyze_hit_falsifiers(
        self,
        case: BacktestCase,
        result: BacktestResult,
        events: List[SignalEvent],
        ledgers: Dict[str, List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """Identify falsifiers that were triggered."""
        hit = []

        for falsifier in case.falsifiers.any_of:
            # Similar logic to triggers, but these should NOT have fired
            # For now, return empty (falsifier logic would mirror trigger logic)
            pass

        return hit

    def _analyze_signal_gaps(
        self,
        case: BacktestCase,
        events: List[SignalEvent],
        ledgers: Dict[str, List[Dict[str, Any]]],
    ) -> SignalGaps:
        """Analyze signal availability gaps."""
        min_signal_count = case.guardrails.min_signal_count
        missing_events = max(0, min_signal_count - len(events))

        # Count denied signals (estimate from integrity filtering)
        integrity_ledger = ledgers.get("integrity_ledger", [])
        denied_signals = sum(
            1
            for entry in integrity_ledger
            if entry.get("filtered", False) or entry.get("ssi", 0) > 0.7
        )

        # Identify missing ledgers
        required_ledgers = case.provenance.required_ledgers
        missing_ledgers = [
            ledger_path
            for ledger_path in required_ledgers
            if Path(ledger_path).name.replace(".jsonl", "")
            not in ledgers  # ledgers dict uses base names
        ]

        return SignalGaps(
            missing_events=missing_events,
            denied_signals=denied_signals,
            missing_ledgers=missing_ledgers,
        )

    def _analyze_integrity_conditions(
        self,
        events: List[SignalEvent],
        ledgers: Dict[str, List[Dict[str, Any]]],
    ) -> IntegrityConditions:
        """Analyze integrity metrics at evaluation time."""
        integrity_ledger = ledgers.get("integrity_ledger", [])

        max_ssi = max(
            (entry.get("ssi", 0) for entry in integrity_ledger), default=0.0
        )

        # Estimate synthetic saturation (proportion of high-SSI events)
        synthetic_count = sum(1 for entry in integrity_ledger if entry.get("ssi", 0) > 0.5)
        synthetic_saturation = (
            synthetic_count / len(integrity_ledger) if integrity_ledger else 0.0
        )

        return IntegrityConditions(
            max_ssi=max_ssi, synthetic_saturation=synthetic_saturation
        )

    def _analyze_temporal_gaps(
        self, ledgers: Dict[str, List[Dict[str, Any]]]
    ) -> TemporalGaps:
        """Analyze temporal dynamics."""
        oracle_delta = ledgers.get("oracle_delta", [])

        if oracle_delta:
            tau_latencies = [
                entry.get("tau_latency_ms", 0)
                for entry in oracle_delta
                if "tau_latency_ms" in entry
            ]
            tau_phases = [
                entry.get("tau_phase", 0)
                for entry in oracle_delta
                if "tau_phase" in entry
            ]

            tau_latency_mean = (
                sum(tau_latencies) / len(tau_latencies) if tau_latencies else None
            )

            # Simple variance calculation
            if tau_phases and len(tau_phases) > 1:
                mean_phase = sum(tau_phases) / len(tau_phases)
                variance = sum((p - mean_phase) ** 2 for p in tau_phases) / len(
                    tau_phases
                )
                tau_phase_variance = variance
            else:
                tau_phase_variance = None
        else:
            tau_latency_mean = None
            tau_phase_variance = None

        return TemporalGaps(
            tau_latency_mean=tau_latency_mean, tau_phase_variance=tau_phase_variance
        )

    def _generate_hypothesis(
        self,
        case: BacktestCase,
        result: BacktestResult,
        unmet_triggers: List[UnmetTrigger],
        signal_gaps: SignalGaps,
        integrity_conditions: IntegrityConditions,
    ) -> str:
        """Generate deterministic hypothesis about failure cause."""
        if result.status == BacktestStatus.ABSTAIN:
            if signal_gaps.missing_events > 0:
                return "insufficient_signal_count"
            elif signal_gaps.missing_ledgers:
                return "missing_required_ledgers"
            elif integrity_conditions.max_ssi > case.guardrails.max_integrity_risk:
                return "integrity_risk_exceeded"
            else:
                return "guardrail_triggered_unknown"

        elif result.status == BacktestStatus.MISS:
            if len(unmet_triggers) > 0:
                # Classify based on trigger type
                term_seen_unmet = any(t.kind == "term_seen" for t in unmet_triggers)
                mw_shift_unmet = any(t.kind == "mw_shift" for t in unmet_triggers)
                index_threshold_unmet = any(
                    t.kind == "index_threshold" for t in unmet_triggers
                )

                if term_seen_unmet:
                    return "term_prediction_too_aggressive"
                elif mw_shift_unmet:
                    return "mw_dynamics_underestimated"
                elif index_threshold_unmet:
                    return "index_threshold_not_reached"
                else:
                    return "trigger_conditions_unmet"
            else:
                return "falsifier_triggered"

        return "unknown_failure_mode"

    def _suggest_adjustments(
        self,
        case: BacktestCase,
        result: BacktestResult,
        unmet_triggers: List[UnmetTrigger],
        signal_gaps: SignalGaps,
        integrity_conditions: IntegrityConditions,
    ) -> List[str]:
        """Suggest potential adjustments based on analysis."""
        suggestions = []

        # Signal gap suggestions
        if signal_gaps.missing_events > 0:
            suggestions.append("extend_evaluation_window")
            suggestions.append("relax_min_signal_count_threshold")

        if signal_gaps.denied_signals > 5:
            suggestions.append("adjust_integrity_filtering")

        if signal_gaps.missing_ledgers:
            suggestions.append("add_signal_source_diversity")

        # Unmet trigger suggestions
        for trigger in unmet_triggers:
            if trigger.kind == "term_seen":
                expected_count = trigger.expected.get("min_count", 1)
                actual_count = trigger.actual.get("count", 0)

                if actual_count == 0:
                    suggestions.append("term_prediction_too_specific")
                elif actual_count < expected_count:
                    suggestions.append("relax_min_count_threshold")

            elif trigger.kind == "mw_shift":
                suggestions.append("relax_mw_shift_threshold")

            elif trigger.kind == "index_threshold":
                suggestions.append("adjust_index_threshold")

        # Integrity condition suggestions
        if integrity_conditions.max_ssi > 0.7:
            suggestions.append("add_integrity_gate_enforcement")

        return list(set(suggestions))  # Deduplicate

    def write_failure(self, analysis: FailureAnalysis) -> tuple[Path, Path]:
        """
        Write failure analysis to disk (JSON + Markdown).

        Args:
            analysis: Failure analysis artifact

        Returns:
            Tuple of (json_path, markdown_path)
        """
        json_path = self.output_dir / f"{analysis.failure_id}.json"
        md_path = self.output_dir / f"{analysis.failure_id}.md"

        # Write JSON
        with open(json_path, "w") as f:
            json.dump(analysis.model_dump(), f, indent=2, default=str)

        # Write Markdown
        md_content = self._render_markdown(analysis)
        with open(md_path, "w") as f:
            f.write(md_content)

        return json_path, md_path

    def append_to_ledger(self, analysis: FailureAnalysis) -> str:
        """
        Append failure analysis to learning ledger.

        Args:
            analysis: Failure analysis artifact

        Returns:
            SHA256 hash of ledger entry
        """
        # Get last hash
        prev_hash = self._get_last_hash()

        # Create ledger entry
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "failure_analysis",
            "failure_id": analysis.failure_id,
            "case_id": analysis.case_id,
            "run_id": analysis.run_id,
            "status": analysis.backtest_result["status"],
            "hypothesis": analysis.hypothesis,
            "unmet_trigger_count": len(analysis.unmet_triggers),
            "suggested_adjustment_count": len(analysis.suggested_adjustments),
            "prev_hash": prev_hash,
        }

        # Hash entry
        step_hash = hash_canonical_json(entry)
        entry["step_hash"] = step_hash

        # Append to ledger
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")

        return step_hash

    def _get_last_hash(self) -> str:
        """Get hash of last ledger entry."""
        if not self.ledger_path.exists():
            return "genesis"

        with open(self.ledger_path, "r") as f:
            lines = f.readlines()
            if not lines:
                return "genesis"

            last_entry = json.loads(lines[-1])
            return last_entry.get("step_hash", "genesis")

    def _render_markdown(self, analysis: FailureAnalysis) -> str:
        """Render failure analysis as Markdown."""
        lines = [
            f"# Failure Analysis: {analysis.failure_id}",
            "",
            f"**Case ID**: {analysis.case_id}",
            f"**Run ID**: {analysis.run_id}",
            f"**Status**: {analysis.backtest_result['status']}",
            f"**Score**: {analysis.backtest_result['score']}",
            f"**Confidence**: {analysis.backtest_result['confidence']}",
            f"**Created**: {analysis.created_at.isoformat()}",
            "",
            "## Hypothesis",
            "",
            f"**{analysis.hypothesis}**",
            "",
            "## Unmet Triggers",
            "",
        ]

        if analysis.unmet_triggers:
            for trigger in analysis.unmet_triggers:
                lines.append(f"- **{trigger.kind}**")
                lines.append(f"  - Expected: {trigger.expected}")
                lines.append(f"  - Actual: {trigger.actual}")
        else:
            lines.append("*No unmet triggers (falsifiers may have been hit)*")

        lines.extend(
            [
                "",
                "## Signal Gaps",
                "",
                f"- **Missing Events**: {analysis.signal_gaps.missing_events}",
                f"- **Denied Signals**: {analysis.signal_gaps.denied_signals}",
                f"- **Missing Ledgers**: {', '.join(analysis.signal_gaps.missing_ledgers) if analysis.signal_gaps.missing_ledgers else 'None'}",
                "",
                "## Integrity Conditions",
                "",
                f"- **Max SSI**: {analysis.integrity_conditions.max_ssi:.2f}",
                f"- **Synthetic Saturation**: {analysis.integrity_conditions.synthetic_saturation:.2%}",
                "",
                "## Temporal Gaps",
                "",
                f"- **τ Latency Mean**: {analysis.temporal_gaps.tau_latency_mean:.1f} ms"
                if analysis.temporal_gaps.tau_latency_mean
                else "- **τ Latency Mean**: N/A",
                f"- **τ Phase Variance**: {analysis.temporal_gaps.tau_phase_variance:.3f}"
                if analysis.temporal_gaps.tau_phase_variance
                else "- **τ Phase Variance**: N/A",
                "",
                "## Suggested Adjustments",
                "",
            ]
        )

        if analysis.suggested_adjustments:
            for adjustment in analysis.suggested_adjustments:
                lines.append(f"- {adjustment}")
        else:
            lines.append("*No adjustments suggested*")

        lines.extend(["", "---", "", "*Generated by Abraxas Active Learning v0.1*"])

        return "\n".join(lines)


def analyze_backtest_failure(
    case: BacktestCase,
    result: BacktestResult,
    events: List[SignalEvent],
    ledgers: Dict[str, List[Dict[str, Any]]],
    output_dir: str | Path = "out/reports",
    ledger_path: str | Path = "out/learning_ledgers/failure_analyses.jsonl",
) -> FailureAnalysis:
    """
    Analyze backtest failure and write artifacts.

    Convenience function that creates analyzer, runs analysis,
    writes files, and appends to ledger.

    Args:
        case: Backtest case
        result: Backtest result (MISS or ABSTAIN)
        events: Signal events
        ledgers: Loaded ledgers
        output_dir: Output directory for artifacts
        ledger_path: Learning ledger path

    Returns:
        FailureAnalysis artifact
    """
    analyzer = FailureAnalyzer(output_dir=output_dir, ledger_path=ledger_path)
    analysis = analyzer.analyze(case, result, events, ledgers)
    analyzer.write_failure(analysis)
    analyzer.append_to_ledger(analysis)
    return analysis
