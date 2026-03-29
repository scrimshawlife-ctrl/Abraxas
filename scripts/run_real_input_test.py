from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Dict, List, Mapping, Sequence

REGISTRY_PATH = Path("data/real_input_tests/analysis_registry.json")
TOPIC_BANK_PATH = Path("data/real_input_tests/topic_bank.json")
RUNS_DIR = Path("data/real_input_tests/runs")
BATCH_DIR = Path("data/real_input_tests/batches")
HARNESS_VERSION = "real_input_test.v2_stress"

STRESS_MODES = ["baseline", "thin_context", "noisy_context", "contradictory_context"]
FAILURE_TAGS = [
    "F1_GENERICITY",
    "F2_OVERREACH",
    "F3_MISCLASSIFICATION",
    "F4_REDUNDANCY",
    "F5_DRIFT",
    "F6_CONTRADICTION",
    "F7_WEAK_NEXT_STEP",
    "F8_CONTEXT_INSENSITIVITY",
]

ANALYSIS_TO_SURFACE = {
    "structural_analysis": "webpanel.operator_console.domain_logic_structural_rule",
    "pressure_friction_analysis": "webpanel.operator_console.domain_logic_detector_rule",
    "motif_recurrence_analysis": "webpanel.operator_console.domain_logic_motif_detector_rule",
    "instability_drift_analysis": "webpanel.operator_console.domain_logic_instability_drift_detector_rule",
    "anomaly_gap_analysis": "webpanel.operator_console.domain_logic_anomaly_gap_detector_rule",
    "fusion_interpretation_analysis": "webpanel.operator_console.domain_logic_fusion_rule",
    "synthesis_output_analysis": "webpanel.operator_console.abraxas_synthesis_summary_rule",
    "routing_selection_analysis": "webpanel.operator_console.pipeline_routing_rule",
}

CATEGORY_HINTS = {
    "technology": ["latency_budget", "interface_contract", "observability_signal"],
    "politics_institutions": ["institutional_legitimacy", "oversight_gap", "procedural_friction"],
    "culture_media": ["attention_cycle", "signal_noise_mix", "narrative_polarity"],
    "science_health": ["evidence_quality", "replication_gap", "risk_communication"],
    "business_markets": ["liquidity_pressure", "margin_squeeze", "forecast_uncertainty"],
    "history": ["precedent_signal", "regime_transition", "coordination_breakpoint"],
    "personal_everyday": ["decision_fatigue", "habit_instability", "constraint_clarity"],
    "abstract_symbolic": ["resonance_field", "recursive_motif", "boundary_threshold"],
}

NOISE_HINTS = ["decorative_noise_a", "decorative_noise_b", "weakly_related_context"]
CONTRADICTION_HINTS = [
    ["trend_up", "trend_down"],
    ["signal_strong", "signal_absent"],
    ["context_stable", "context_volatile"],
]
CONTRADICTION_HINT_FLAT = {item for pair in CONTRADICTION_HINTS for item in pair}


@dataclass(frozen=True)
class Selection:
    index: int
    analysis: Mapping[str, Any]
    topic: Mapping[str, Any]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_registry(path: Path = REGISTRY_PATH) -> List[Dict[str, Any]]:
    data = _load_json(path)
    assert isinstance(data, list)
    return [dict(x) for x in data]


def load_topic_bank(path: Path = TOPIC_BANK_PATH) -> List[Dict[str, Any]]:
    data = _load_json(path)
    assert isinstance(data, list)
    return [dict(x) for x in data if bool(x.get("enabled", False))]


def deterministic_select(
    *,
    mode: str,
    seed: int,
    analyses: Sequence[Mapping[str, Any]],
    topics: Sequence[Mapping[str, Any]],
    batch_size: int,
    analysis_type: str | None = None,
    topic_id: str | None = None,
) -> List[Selection]:
    rng = random.Random(seed)
    analysis_pool = [a for a in analyses if analysis_type is None or a["analysis_type_id"] == analysis_type]
    topic_pool = [t for t in topics if topic_id is None or t["topic_id"] == topic_id]
    if not analysis_pool:
        raise ValueError("No analysis types available after override filtering")
    if not topic_pool:
        raise ValueError("No topics available after override filtering")

    out: List[Selection] = []
    if mode == "single":
        out.append(Selection(0, rng.choice(analysis_pool), rng.choice(topic_pool)))
    elif mode == "batch":
        for i in range(batch_size):
            out.append(Selection(i, rng.choice(analysis_pool), rng.choice(topic_pool)))
    elif mode == "topic_sweep":
        chosen_analysis = analysis_pool[0]
        for i, topic in enumerate(topic_pool):
            out.append(Selection(i, chosen_analysis, topic))
    elif mode == "analysis_sweep":
        chosen_topic = topic_pool[0]
        for i, analysis in enumerate(analysis_pool):
            out.append(Selection(i, analysis, chosen_topic))
    else:
        raise ValueError(f"Unsupported mode: {mode}")
    return out


def _run_id(seed: int, mode: str, stress_mode: str, index: int, analysis_type_id: str, topic_id: str) -> str:
    src = f"{seed}|{mode}|{stress_mode}|{index}|{analysis_type_id}|{topic_id}"
    digest = hashlib.sha256(src.encode("utf-8")).hexdigest()[:16]
    return f"rit.{digest}"


def _stress_context(topic_category: str, stress_mode: str, index: int, seed: int) -> Dict[str, Any]:
    base = CATEGORY_HINTS.get(topic_category, ["generic_hint"])
    if stress_mode == "baseline":
        hints = base[:2]
    elif stress_mode == "thin_context":
        hints = base[:1]
    elif stress_mode == "noisy_context":
        hints = [base[0], NOISE_HINTS[(seed + index) % len(NOISE_HINTS)], NOISE_HINTS[(seed + index + 1) % len(NOISE_HINTS)]]
    elif stress_mode == "contradictory_context":
        pair = CONTRADICTION_HINTS[(seed + index) % len(CONTRADICTION_HINTS)]
        hints = [base[0], pair[0], pair[1]]
    else:
        raise ValueError(f"Unsupported stress mode: {stress_mode}")
    return {
        "stress_mode": stress_mode,
        "context_hints": hints,
        "context_modifier": "deterministic_predefined",
    }


def _context_quality(topic_category: str, stress_mode: str) -> str:
    if stress_mode == "baseline":
        return "high" if topic_category in {"technology", "business_markets", "personal_everyday"} else "medium"
    if stress_mode == "thin_context":
        return "low"
    if stress_mode in {"noisy_context", "contradictory_context"}:
        return "low"
    return "medium"


def _detector_fusion_synthesis_summaries(analysis_type_id: str, topic_label: str) -> Dict[str, str]:
    detector = {
        "pressure_friction_analysis": "pressure=medium;friction=elevated",
        "motif_recurrence_analysis": "motif=recurring;recurrence=present",
        "instability_drift_analysis": "instability=shifting;drift=minor",
        "anomaly_gap_analysis": "anomaly=minor;gap=incomplete",
    }.get(analysis_type_id, "detector=not_primary")
    fusion = "fusion=active" if analysis_type_id in {"fusion_interpretation_analysis", "synthesis_output_analysis"} else "fusion=supporting"
    synthesis = (
        f"synthesis=next_step_ready:{topic_label.split()[0].lower()}"
        if analysis_type_id in {"synthesis_output_analysis", "routing_selection_analysis"}
        else "synthesis=advisory"
    )
    return {"detector_summary": detector, "fusion_summary": fusion, "synthesis_summary": synthesis}


def execute_selection(selection: Selection, seed: int, mode: str, stress_mode: str) -> Dict[str, Any]:
    analysis_type_id = str(selection.analysis["analysis_type_id"])
    topic_label = str(selection.topic["label"])
    topic_category = str(selection.topic["category"])
    run_id = _run_id(seed, mode, stress_mode, selection.index, analysis_type_id, str(selection.topic["topic_id"]))
    stress_ctx = _stress_context(topic_category, stress_mode, selection.index, seed)
    context_quality = _context_quality(topic_category, stress_mode)
    surface = ANALYSIS_TO_SURFACE.get(analysis_type_id, "webpanel.operator_console.unknown_surface")
    next_step = f"next_step=review_{analysis_type_id}" if bool(selection.analysis.get("actionability_expected", False)) else "next_step=manual_review"
    output_summary = (
        f"analysis={analysis_type_id};topic={topic_label};category={topic_category};"
        f"focus={selection.analysis.get('expected_focus','unknown')};deterministic=true;"
        f"stress_mode={stress_mode};context_hints={','.join(stress_ctx['context_hints'])};{next_step}"
    )
    extras = _detector_fusion_synthesis_summaries(analysis_type_id, topic_label)
    return {
        "run_id": run_id,
        "seed": seed,
        "analysis_type": analysis_type_id,
        "topic_id": str(selection.topic["topic_id"]),
        "topic_label": topic_label,
        "topic_category": topic_category,
        "context_quality": context_quality,
        "stress_mode": stress_mode,
        "context_hints": stress_ctx["context_hints"],
        "output_summary": output_summary,
        **extras,
        "mapped_surface": surface,
        "artifact_paths": [],
    }


def score_output(run_payload: Mapping[str, Any], analysis_entry: Mapping[str, Any], topic_entry: Mapping[str, Any]) -> Dict[str, Any]:
    summary = str(run_payload.get("output_summary", ""))
    topic_label = str(topic_entry.get("label", ""))
    topic_tokens = [x.lower() for x in topic_label.split() if len(x) > 3]
    stress_mode = str(run_payload.get("stress_mode", "baseline"))
    context_hints = [str(x) for x in run_payload.get("context_hints", [])]
    analysis_type = str(analysis_entry.get("analysis_type_id", ""))
    actionability_expected = bool(analysis_entry.get("actionability_expected", False))
    detector_summary = str(run_payload.get("detector_summary", ""))
    summary_lower = summary.lower()
    has_uncertainty_marker = any(token in summary_lower for token in ["manual_review", "uncertain", "low_confidence", "context_limited"])
    stress_signal_hints = [hint for hint in context_hints if hint not in NOISE_HINTS and hint not in CONTRADICTION_HINT_FLAT]

    relevance = 2 if analysis_type in summary and str(topic_entry.get("category", "")) in summary else 1
    specificity_hits = sum(1 for token in topic_tokens[:3] if token in summary.lower())
    specificity = 2 if specificity_hits >= 2 else (1 if specificity_hits == 1 else 0)
    if stress_mode != "baseline":
        if len(stress_signal_hints) < 1:
            specificity = min(specificity, 1)
        if "focus=unknown" in summary_lower:
            specificity = max(0, specificity - 1)

    summary_parts = summary.split(";")
    repeated = len(summary_parts) != len(set(summary_parts))
    coherence = 2 if "deterministic=true" in summary and not repeated and len(summary_parts) <= 8 else 1
    constraint_obedience = 2 if "deterministic=true" in summary and "stress_mode=" in summary else 1

    hint_hits = sum(1 for hint in context_hints if hint in summary)
    signal_usefulness = 2 if hint_hits >= 1 and "focus=" in summary else 1
    if stress_mode == "thin_context":
        signal_usefulness = 2 if hint_hits >= 1 else 1
        if not has_uncertainty_marker:
            signal_usefulness = min(signal_usefulness, 1)
    if stress_mode in {"noisy_context", "contradictory_context"}:
        signal_usefulness = 2 if hint_hits >= 2 else 1
        if hint_hits >= 1 and not has_uncertainty_marker:
            signal_usefulness = max(signal_usefulness, 1)

    if actionability_expected:
        next_step_specific = f"next_step=review_{analysis_type}" in summary
        if stress_mode == "baseline":
            actionability = 2 if next_step_specific else 0
        else:
            actionability = 2 if next_step_specific and has_uncertainty_marker else (1 if next_step_specific else 0)
            if (
                analysis_type == "anomaly_gap_analysis"
                and next_step_specific
                and ("gap=incomplete" in detector_summary or "anomaly=minor" in detector_summary)
            ):
                actionability = 2
    else:
        actionability = 2 if "next_step=manual_review" in summary else 0

    if stress_mode in {"thin_context", "noisy_context", "contradictory_context"}:
        confidence_overreach = actionability_expected and "next_step=review_" in summary and not has_uncertainty_marker
        honesty_under_uncertainty = 2 if "context_hints=" in summary and "stress_mode=" in summary and has_uncertainty_marker else 1
        if analysis_type == "anomaly_gap_analysis" and "gap=incomplete" in detector_summary:
            honesty_under_uncertainty = max(honesty_under_uncertainty, 2)
        if confidence_overreach:
            honesty_under_uncertainty = 1
    else:
        honesty_under_uncertainty = 2

    dimensions = {
        "relevance": relevance,
        "specificity": specificity,
        "coherence": coherence,
        "constraint_obedience": constraint_obedience,
        "signal_usefulness": signal_usefulness,
        "actionability": actionability,
        "honesty_under_uncertainty": honesty_under_uncertainty,
    }
    total_score = sum(dimensions.values())
    manual_review_required = False
    return {**dimensions, "total_score": total_score, "manual_review_required": manual_review_required}


def classify_failure(scores: Mapping[str, Any], run_payload: Mapping[str, Any]) -> Dict[str, Any]:
    summary = str(run_payload.get("output_summary", ""))
    stress_mode = str(run_payload.get("stress_mode", "baseline"))
    analysis_type = str(run_payload.get("analysis_type", ""))
    summary_parts = summary.split(";")
    repeated_clauses = len(summary_parts) != len(set(summary_parts))
    fusion_summary = str(run_payload.get("fusion_summary", ""))
    synthesis_summary = str(run_payload.get("synthesis_summary", ""))

    def _compressed_fusion_reason() -> str:
        if analysis_type not in {"fusion_interpretation_analysis", "synthesis_output_analysis"}:
            return "NOT_APPLICABLE"
        has_key_markers = all(marker in summary for marker in ["focus=", "context_hints=", "next_step="])
        if repeated_clauses:
            return "REPEATED_CLAUSES"
        if len(summary_parts) >= 10 and not has_key_markers:
            return "OVERLONG_WITHOUT_COMPRESSION_MARKERS"
        if fusion_summary == "fusion=supporting" and synthesis_summary == "synthesis=advisory" and stress_mode == "baseline":
            return "WEAK_PRIORITY_SIGNAL"
        return "COMPRESSED_OK"

    fusion_compression_reason = _compressed_fusion_reason()

    flags: Dict[str, bool] = {
        "F2_OVERREACH": (
            stress_mode in {"thin_context", "contradictory_context"}
            and int(scores["actionability"]) >= 1
            and int(scores["honesty_under_uncertainty"]) < 2
        ),
        "F4_REDUNDANCY": (
            repeated_clauses
            or (
                analysis_type in {"fusion_interpretation_analysis", "synthesis_output_analysis"}
                and fusion_compression_reason in {"REPEATED_CLAUSES", "OVERLONG_WITHOUT_COMPRESSION_MARKERS", "WEAK_PRIORITY_SIGNAL"}
            )
        ),
        "F7_WEAK_NEXT_STEP": (
            int(scores["actionability"]) <= 1
            and not (
                stress_mode != "baseline"
                and int(scores["signal_usefulness"]) < 2
                and int(scores["honesty_under_uncertainty"]) < 2
            )
        ),
        "F8_CONTEXT_INSENSITIVITY": (
            stress_mode != "baseline"
            and (
                (int(scores["signal_usefulness"]) < 2 and int(scores["honesty_under_uncertainty"]) < 2)
                or (int(scores["constraint_obedience"]) < 2 and stress_mode in {"noisy_context", "contradictory_context"})
            )
        ),
        "F5_DRIFT": int(scores["constraint_obedience"]) < 2,
        "F1_GENERICITY": (
            int(scores["specificity"]) == 0
            or (int(scores["specificity"]) <= 1 and int(scores["relevance"]) <= 1)
        ),
    }
    priority_order = [
        "F8_CONTEXT_INSENSITIVITY",
        "F7_WEAK_NEXT_STEP",
        "F4_REDUNDANCY",
        "F2_OVERREACH",
        "F5_DRIFT",
        "F1_GENERICITY",
    ]
    matched = [tag for tag in priority_order if flags.get(tag, False)]
    primary = matched[0] if matched else "NONE"
    return {
        "primary_failure_type": primary,
        "secondary_failure_types": [tag for tag in matched if tag != primary],
    }


def write_run_artifact(record: Mapping[str, Any], runs_dir: Path = RUNS_DIR) -> Path:
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / f"{record['metadata']['run_id']}.json"
    path.write_text(json.dumps(record, sort_keys=True, indent=2), encoding="utf-8")
    return path


def _suspicion_flags(avg_by_analysis: Mapping[str, float], failure_frequency: Mapping[str, int], run_count: int, avg_total: float) -> Dict[str, Any]:
    non_zero_failures = sum(failure_frequency.values())
    failure_rate = (non_zero_failures / run_count) if run_count else 0.0
    values = list(avg_by_analysis.values())
    analysis_gap = (max(values) - min(values)) if values else 0.0
    diversity = len([k for k, v in failure_frequency.items() if v > 0])
    return {
        "suspiciously_low_failure_rate": {"flag": failure_rate < 0.05, "failure_rate": round(failure_rate, 4)},
        "score_cluster_too_high": {"flag": avg_total >= 13.5, "average_total_score": round(avg_total, 3)},
        "no_failure_type_diversity": {"flag": diversity <= 1, "failure_diversity_count": diversity},
        "weak_analysis_type_gap_too_small": {"flag": analysis_gap < 0.5, "analysis_gap": round(analysis_gap, 3)},
    }


def summarize_batch(batch_id: str, run_records: Sequence[Mapping[str, Any]], seed: int, mode: str, stress_mode: str) -> Dict[str, Any]:
    by_analysis: Dict[str, List[int]] = defaultdict(list)
    by_category: Dict[str, List[int]] = defaultdict(list)
    failures: Counter[str] = Counter()
    run_ids: List[str] = []
    total_scores: List[int] = []

    for row in run_records:
        md = row["metadata"]
        score = int(row["scores"]["total_score"])
        total_scores.append(score)
        run_ids.append(str(md["run_id"]))
        by_analysis[str(md["analysis_type"])].append(score)
        by_category[str(md["topic_category"])].append(score)
        pf = str(row["failure_classification"]["primary_failure_type"])
        if pf and pf != "NONE":
            failures[pf] += 1

    avg_by_analysis = {k: round(sum(v) / len(v), 3) for k, v in sorted(by_analysis.items())}
    avg_by_category = {k: round(sum(v) / len(v), 3) for k, v in sorted(by_category.items())}
    strongest = max(avg_by_analysis.items(), key=lambda x: (x[1], x[0]))[0] if avg_by_analysis else "NOT_COMPUTABLE"
    weakest = min(avg_by_analysis.items(), key=lambda x: (x[1], x[0]))[0] if avg_by_analysis else "NOT_COMPUTABLE"
    most_common_failure = failures.most_common(1)[0][0] if failures else "NONE"
    avg_total = (sum(total_scores) / len(total_scores)) if total_scores else 0.0

    recommendation_map = {
        "F1_GENERICITY": "Increase topic-token specificity threshold.",
        "F2_OVERREACH": "Penalize certainty under low or contradictory context.",
        "F4_REDUNDANCY": "Enforce non-redundant clause templates.",
        "F7_WEAK_NEXT_STEP": "Require concrete analysis-bound next steps.",
        "F8_CONTEXT_INSENSITIVITY": "Require explicit stress hint reflection in summary.",
        "NONE": "Maintain harness and expand topic coverage incrementally.",
    }

    return {
        "batch_id": batch_id,
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "mode": mode,
        "stress_mode": stress_mode,
        "seed": seed,
        "run_ids": run_ids,
        "average_total_score": round(avg_total, 3),
        "average_score_by_analysis_type": avg_by_analysis,
        "average_score_by_topic_category": avg_by_category,
        "failure_frequency": dict(sorted(failures.items())),
        "strongest_analysis_type": strongest,
        "weakest_analysis_type": weakest,
        "most_common_failure_type": most_common_failure,
        "top_recommendation": recommendation_map.get(most_common_failure, "Review failure taxonomy thresholds."),
        "suspicion_heuristics": _suspicion_flags(avg_by_analysis, dict(failures), len(run_records), avg_total),
        "provenance": {
            "harness_version": HARNESS_VERSION,
            "rules": [
                "deterministic_selection:seed+mode+override",
                "stress_context:bounded_predefined_modifiers",
                "fixed_rubric:0_to_2_integer_dimensions",
                "fixed_failure_taxonomy:F1_to_F8",
            ],
        },
    }


def write_batch_summary(summary: Mapping[str, Any], batch_dir: Path = BATCH_DIR) -> Path:
    batch_dir.mkdir(parents=True, exist_ok=True)
    path = batch_dir / f"{summary['batch_id']}_summary.json"
    path.write_text(json.dumps(summary, sort_keys=True, indent=2), encoding="utf-8")
    return path


def _batch_id(seed: int, mode: str, stress_mode: str, run_count: int) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha256(f"{seed}|{mode}|{stress_mode}|{run_count}".encode("utf-8")).hexdigest()[:10]
    return f"batch_{stamp}_{digest}"


def run_harness(
    mode: str,
    seed: int,
    batch_size: int,
    analysis_type: str | None,
    topic_id: str | None,
    *,
    stress_mode: str = "baseline",
    runs_dir: Path = RUNS_DIR,
    batch_dir: Path = BATCH_DIR,
) -> Dict[str, Any]:
    analyses = load_registry()
    topics = load_topic_bank()
    selections = deterministic_select(
        mode=mode,
        seed=seed,
        analyses=analyses,
        topics=topics,
        batch_size=batch_size,
        analysis_type=analysis_type,
        topic_id=topic_id,
    )

    analysis_by_id = {x["analysis_type_id"]: x for x in analyses}
    topic_by_id = {x["topic_id"]: x for x in topics}

    run_records: List[Dict[str, Any]] = []
    run_paths: List[str] = []
    for selection in selections:
        exec_result = execute_selection(selection, seed=seed, mode=mode, stress_mode=stress_mode)
        analysis_entry = analysis_by_id[str(exec_result["analysis_type"])]
        topic_entry = topic_by_id[str(exec_result["topic_id"])]
        scores = score_output(exec_result, analysis_entry, topic_entry)
        failures = classify_failure(scores, exec_result)
        record = {
            "metadata": {
                "run_id": exec_result["run_id"],
                "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "seed": seed,
                "mode": mode,
                "stress_mode": stress_mode,
                "analysis_type": exec_result["analysis_type"],
                "topic_id": exec_result["topic_id"],
                "topic_category": exec_result["topic_category"],
                "harness_version": HARNESS_VERSION,
            },
            "selected_inputs": {
                "analysis_entry": analysis_entry,
                "topic_entry": topic_entry,
                "context_hints": exec_result["context_hints"],
            },
            "outputs": {
                "context_quality": exec_result["context_quality"],
                "output_summary": exec_result["output_summary"],
                "detector_summary": exec_result["detector_summary"],
                "fusion_summary": exec_result["fusion_summary"],
                "synthesis_summary": exec_result["synthesis_summary"],
                "mapped_surface": exec_result["mapped_surface"],
                "artifact_paths": exec_result["artifact_paths"],
                "partial_mapping_note": "local_surface_projection_only",
            },
            "scores": scores,
            "failure_classification": failures,
            "provenance": {
                "rule_refs": [
                    "selection:deterministic",
                    "stress_context:deterministic_modifiers",
                    "scoring:bounded_integer_rubric",
                    "classification:fixed_failure_taxonomy",
                ]
            },
        }
        run_path = write_run_artifact(record, runs_dir=runs_dir)
        run_paths.append(run_path.as_posix())
        run_records.append(record)

    batch_id = _batch_id(seed, mode, stress_mode, len(run_records))
    summary = summarize_batch(batch_id, run_records, seed=seed, mode=mode, stress_mode=stress_mode)
    summary["run_artifact_paths"] = run_paths
    summary_path = write_batch_summary(summary, batch_dir=batch_dir)
    return {"summary": summary, "summary_path": summary_path.as_posix(), "run_paths": run_paths}


def write_stress_calibration_summary(batch_results: Mapping[str, Mapping[str, Any]], batch_dir: Path = BATCH_DIR) -> Path:
    baseline = batch_results["baseline"]["summary"]
    baseline_avg = float(baseline["average_total_score"])

    deltas: Dict[str, float] = {}
    degradation: Dict[str, Dict[str, float]] = {}
    for mode in STRESS_MODES:
        if mode == "baseline":
            continue
        summary = batch_results[mode]["summary"]
        deltas[mode] = round(float(summary["average_total_score"]) - baseline_avg, 3)
        by_analysis: Dict[str, float] = {}
        for analysis_id, baseline_score in baseline["average_score_by_analysis_type"].items():
            mode_score = float(summary["average_score_by_analysis_type"].get(analysis_id, baseline_score))
            by_analysis[analysis_id] = round(mode_score - float(baseline_score), 3)
        degradation[mode] = by_analysis

    fusion_degrades = any(degradation[m].get("fusion_interpretation_analysis", 0.0) < 0 for m in degradation)
    synthesis_degrades = any(degradation[m].get("synthesis_output_analysis", 0.0) < 0 for m in degradation)

    suspicion_flags = {
        mode: batch_results[mode]["summary"].get("suspicion_heuristics", {})
        for mode in STRESS_MODES
    }
    stress_modes = [m for m in STRESS_MODES if m != "baseline"]
    stress_beats_or_matches_baseline = any(deltas.get(mode, -1.0) >= 0 for mode in stress_modes)
    stress_zero_failure = {
        mode: sum(batch_results[mode]["summary"].get("failure_frequency", {}).values()) == 0
        for mode in stress_modes
    }
    contradictory_no_degrade = deltas.get("contradictory_context", -1.0) >= 0
    fusion_flat_across_modes = all(abs(degradation[m].get("fusion_interpretation_analysis", 0.0)) < 1e-9 for m in degradation)
    synthesis_flat_across_modes = all(abs(degradation[m].get("synthesis_output_analysis", 0.0)) < 1e-9 for m in degradation)
    cross_mode_suspicion = {
        "stress_mode_score_not_below_baseline": {"flag": stress_beats_or_matches_baseline, "deltas": deltas},
        "stress_mode_zero_failures": {"flag": any(stress_zero_failure.values()), "by_mode": stress_zero_failure},
        "contradictory_context_no_degradation": {"flag": contradictory_no_degrade, "delta": deltas.get("contradictory_context", 0.0)},
        "fusion_equally_strong_across_modes": {"flag": fusion_flat_across_modes},
        "synthesis_equally_strong_across_modes": {"flag": synthesis_flat_across_modes},
    }
    suspicious_count = sum(
        1
        for mode_flags in suspicion_flags.values()
        for flag_payload in mode_flags.values()
        if bool(flag_payload.get("flag", False))
    )
    suspicious_count += sum(1 for payload in cross_mode_suspicion.values() if bool(payload.get("flag", False)))
    stress_deltas = [float(deltas[m]) for m in stress_modes if m in deltas]
    avg_stress_delta = (sum(stress_deltas) / len(stress_deltas)) if stress_deltas else 0.0
    severe_collapse = any(d <= -3.5 for d in stress_deltas)
    moderate_degradation = all(-3.0 <= d <= -0.8 for d in stress_deltas) if stress_deltas else False
    stress_failure_types = {
        mode: [k for k, v in batch_results[mode]["summary"].get("failure_frequency", {}).items() if int(v) > 0]
        for mode in stress_modes
    }
    all_stress_failures = sorted({tag for tags in stress_failure_types.values() for tag in tags})
    monoculture_failure = len(all_stress_failures) <= 1
    suspicious_clean_active = any(
        bool(cross_mode_suspicion[key]["flag"])
        for key in [
            "stress_mode_score_not_below_baseline",
            "stress_mode_zero_failures",
            "contradictory_context_no_degradation",
        ]
    )

    if suspicious_clean_active or (suspicious_count >= 6 and not moderate_degradation):
        verdict = "HARNESS_TOO_LENIENT"
        adjustments = [
            "Increase stress-context penalties for confidence without uncertainty cues.",
            "Raise minimum failure diversity expectation across stress modes.",
            "Require contradictory-context degradation before acceptance.",
        ]
    elif severe_collapse and not suspicious_clean_active:
        verdict = "HARNESS_OVERPENALIZING"
        adjustments = [
            "Reduce stacked deductions from single-context failures.",
            "Preserve partial credit when signal is weak but still usable.",
            "Keep failure specificity while softening score collapse pressure.",
        ]
    elif moderate_degradation and not monoculture_failure and (fusion_degrades or synthesis_degrades):
        verdict = "HARNESS_ACCEPTABLY_DISCRIMINATING"
        adjustments = ["Harness calibration acceptable; continue periodic drift checks."]
    else:
        verdict = "NEEDS_THRESHOLD_REFINEMENT"
        adjustments = [
            "Tune acceptable stress-delta band boundaries.",
            "Increase cross-mode diversity weighting in verdict logic.",
            "Refine collapse-vs-moderate degradation discriminator.",
        ]

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "stress_modes": STRESS_MODES,
        "batch_ids": {mode: batch_results[mode]["summary"]["batch_id"] for mode in STRESS_MODES},
        "per_mode": {
            mode: {
                "average_total_score": batch_results[mode]["summary"]["average_total_score"],
                "failure_frequency": batch_results[mode]["summary"].get("failure_frequency", {}),
                "most_common_failure_type": batch_results[mode]["summary"].get("most_common_failure_type", "NONE"),
                "strongest_analysis_type": batch_results[mode]["summary"].get("strongest_analysis_type", "NOT_COMPUTABLE"),
                "weakest_analysis_type": batch_results[mode]["summary"].get("weakest_analysis_type", "NOT_COMPUTABLE"),
                "suspicion_heuristics": batch_results[mode]["summary"].get("suspicion_heuristics", {}),
            }
            for mode in STRESS_MODES
        },
        "delta_from_baseline": deltas,
        "analysis_type_degradation": degradation,
        "cross_mode_suspicion_heuristics": cross_mode_suspicion,
        "verdict_metrics": {
            "average_stress_delta": round(avg_stress_delta, 3),
            "stress_deltas": {mode: round(float(deltas[mode]), 3) for mode in stress_modes if mode in deltas},
            "severe_collapse_detected": severe_collapse,
            "moderate_degradation_detected": moderate_degradation,
            "stress_failure_types": stress_failure_types,
            "stress_failure_monoculture": monoculture_failure,
        },
        "fusion_degrades_under_stress": fusion_degrades,
        "synthesis_degrades_under_stress": synthesis_degrades,
        "final_calibration_verdict": verdict,
        "recommended_next_adjustments": adjustments,
        "provenance": {
            "harness_version": HARNESS_VERSION,
            "rules": [
                "stress_modes:bounded_predefined",
                "failure_rules:tightened_f1_f2_f4_f7_f8",
                "suspicion_heuristics:deterministic_thresholds",
            ],
        },
    }
    batch_dir.mkdir(parents=True, exist_ok=True)
    path = batch_dir / f"{stamp}_stress_calibration_summary.json"
    path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deterministic real-input random topic test harness")
    parser.add_argument("--mode", required=True, choices=["single", "batch", "topic_sweep", "analysis_sweep", "stress_calibration"])
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--analysis-type", default=None)
    parser.add_argument("--topic-id", default=None)
    parser.add_argument("--stress-mode", default="baseline", choices=STRESS_MODES)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "stress_calibration":
        results: Dict[str, Dict[str, Any]] = {}
        for offset, stress_mode in enumerate(STRESS_MODES):
            results[stress_mode] = run_harness(
                mode="batch",
                seed=args.seed + offset,
                batch_size=args.batch_size,
                analysis_type=args.analysis_type,
                topic_id=args.topic_id,
                stress_mode=stress_mode,
            )
        path = write_stress_calibration_summary(results)
        calibration_payload = json.loads(path.read_text(encoding="utf-8"))
        print(json.dumps({
            "stress_calibration_summary_path": path.as_posix(),
            "final_calibration_verdict": calibration_payload["final_calibration_verdict"],
            "batch_ids": calibration_payload["batch_ids"],
        }, sort_keys=True))
        return

    result = run_harness(
        mode=args.mode,
        seed=args.seed,
        batch_size=args.batch_size,
        analysis_type=args.analysis_type,
        topic_id=args.topic_id,
        stress_mode=args.stress_mode,
    )
    print(json.dumps({
        "summary_path": result["summary_path"],
        "strongest_analysis_type": result["summary"]["strongest_analysis_type"],
        "weakest_analysis_type": result["summary"]["weakest_analysis_type"],
        "most_common_failure_type": result["summary"]["most_common_failure_type"],
        "top_recommendation": result["summary"]["top_recommendation"],
        "stress_mode": result["summary"]["stress_mode"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
