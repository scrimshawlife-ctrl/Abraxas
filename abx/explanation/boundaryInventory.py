from __future__ import annotations

from abx.explanation.types import ExplanationBoundaryRecord, ExplanationLayerRecord


def build_boundary_inventory() -> tuple[ExplanationBoundaryRecord, ...]:
    return (
        ExplanationBoundaryRecord("bnd.ops", "operator.writeup", "BOUNDARY_CLEAR", "layer_labels_present"),
        ExplanationBoundaryRecord("bnd.causal", "causal.summary", "BOUNDARY_EXCEEDED", "causal_claim_without_support"),
        ExplanationBoundaryRecord("bnd.forecast", "forecast.narrative", "BOUNDARY_AMBIGUOUS", "speculation_not_labeled"),
        ExplanationBoundaryRecord("bnd.legacy", "legacy.explanation", "NOT_COMPUTABLE", "source_text_missing"),
    )


def build_layer_inventory() -> tuple[ExplanationLayerRecord, ...]:
    return (
        ExplanationLayerRecord("lyr.obs", "operator.writeup", "OBSERVED_LAYER", "evidence/ops-metrics"),
        ExplanationLayerRecord("lyr.inf", "operator.writeup", "INFERRED_LAYER", "inference/rule-v2"),
        ExplanationLayerRecord("lyr.int", "causal.summary", "INTERPRETIVE_LAYER", "analysis/theme-map"),
        ExplanationLayerRecord("lyr.spec", "forecast.narrative", "SPECULATIVE_LAYER", "forecast/model-v4"),
        ExplanationLayerRecord("lyr.causal", "causal.summary", "CAUSAL_CLAIM_LAYER", "missing-causal-proof"),
    )
