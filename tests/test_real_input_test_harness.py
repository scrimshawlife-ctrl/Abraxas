from __future__ import annotations

from pathlib import Path

from scripts.run_real_input_test import (
    REGISTRY_PATH,
    TOPIC_BANK_PATH,
    deterministic_select,
    load_registry,
    load_topic_bank,
    run_harness,
)


def test_registry_and_topic_bank_loading() -> None:
    registry = load_registry(REGISTRY_PATH)
    topics = load_topic_bank(TOPIC_BANK_PATH)
    assert len(registry) == 8
    assert len(topics) >= 64
    assert len({x["analysis_type_id"] for x in registry}) == len(registry)


def test_deterministic_selection_reproducible() -> None:
    registry = load_registry()
    topics = load_topic_bank()
    a = deterministic_select(mode="batch", seed=1234, analyses=registry, topics=topics, batch_size=5)
    b = deterministic_select(mode="batch", seed=1234, analyses=registry, topics=topics, batch_size=5)
    assert [(x.analysis["analysis_type_id"], x.topic["topic_id"]) for x in a] == [
        (x.analysis["analysis_type_id"], x.topic["topic_id"]) for x in b
    ]


def test_scoring_and_failure_stability_via_harness_single(tmp_path: Path) -> None:
    result = run_harness(
        mode="single",
        seed=222,
        batch_size=1,
        analysis_type="synthesis_output_analysis",
        topic_id="technology_01",
        runs_dir=tmp_path / "runs",
        batch_dir=tmp_path / "batches",
    )
    summary = result["summary"]
    assert summary["most_common_failure_type"] in {
        "NONE",
        "F1_GENERICITY",
        "F2_OVERREACH",
        "F3_MISCLASSIFICATION",
        "F4_REDUNDANCY",
        "F5_DRIFT",
        "F6_CONTRADICTION",
        "F7_WEAK_NEXT_STEP",
        "F8_CONTEXT_INSENSITIVITY",
    }


def test_artifact_writing_and_batch_summary(tmp_path: Path) -> None:
    result = run_harness(
        mode="batch",
        seed=999,
        batch_size=3,
        analysis_type=None,
        topic_id=None,
        runs_dir=tmp_path / "runs",
        batch_dir=tmp_path / "batches",
    )
    summary_path = Path(result["summary_path"])
    assert summary_path.exists()
    assert len(result["run_paths"]) == 3
    assert summary_path.name.endswith("_summary.json")
    assert result["summary"]["strongest_analysis_type"]
    assert result["summary"]["weakest_analysis_type"]
