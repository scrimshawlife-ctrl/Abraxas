from __future__ import annotations

import pytest

from abx.core.formulas import normalize_vector, stable_sort_score_desc_id_asc
from abx.core.types import EvidenceRef
from abx.explain_ir import ExplainIR, ExplainProvenance
from abx.trace_types import ExecutionTrace, ExecutionTraceEvent


def test_stable_sort_score_desc_id_asc() -> None:
    items = [
        {"id": "b", "score": 0.4},
        {"id": "a", "score": 0.4},
        {"id": "c", "score": 0.9},
    ]
    out = stable_sort_score_desc_id_asc(items)
    assert [row["id"] for row in out] == ["c", "a", "b"]


def test_normalize_vector_deterministic() -> None:
    vector = {"z": 20.0, "a": 10.0, "m": 15.0}
    normalized = normalize_vector(vector)
    assert list(normalized.keys()) == ["a", "m", "z"]
    assert normalized["a"] == 0.0
    assert normalized["z"] == 1.0


def test_explain_ir_conforms() -> None:
    explain = ExplainIR(
        explain_rune_id="ϟ_EXPLAIN",
        event_type="forecast.selection",
        summary="Selected candidate by deterministic score ordering.",
        evidence=[EvidenceRef(id="e1", source="ledger", pointer="out/ledger/run.jsonl")],
        provenance=ExplainProvenance(observed=["score"], inferred=["rank"], speculative=[]),
        confidence=0.9,
    )
    payload = explain.model_dump()
    assert payload["explain_rune_id"] == "ϟ_EXPLAIN"
    assert payload["provenance"]["observed"] == ["score"]


def test_explain_ir_rejects_invalid_confidence() -> None:
    with pytest.raises(ValueError):
        ExplainIR(
            explain_rune_id="ϟ_EXPLAIN",
            event_type="forecast.selection",
            summary="bad",
            evidence=[],
            provenance=ExplainProvenance(),
            confidence=1.2,
        )


def test_execution_trace_deterministic_view() -> None:
    trace = ExecutionTrace(
        run_id="RUN-TRACE",
        events=[
            ExecutionTraceEvent(rune_id="ϟ₂", capability="rune:tam", status="ok", input_hash="a", order=2),
            ExecutionTraceEvent(rune_id="ϟ₁", capability="rune:rfa", status="ok", input_hash="b", order=1),
        ],
    )
    view = trace.deterministic_view()
    assert [event.rune_id for event in view] == ["ϟ₁", "ϟ₂"]
