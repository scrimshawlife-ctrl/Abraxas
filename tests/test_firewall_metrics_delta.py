"""Tests for firewall metrics delta and ABX-Core complexity reduction."""

import json
import pytest
from pathlib import Path

from abraxas.synthesis.firewall import apply_temporal_firewall, compute_text_metrics
from abraxas.temporal.detector import analyze_text


@pytest.fixture
def fixtures_dir():
    """Get fixtures directory path."""
    return Path(__file__).parent / "fixtures" / "synthesis"


@pytest.fixture
def expected_behaviors(fixtures_dir):
    """Load expected firewall behaviors."""
    with open(fixtures_dir / "firewall_expected.json", "r") as f:
        return json.load(f)


@pytest.fixture
def draft_neutral(fixtures_dir):
    """Load neutral draft text."""
    with open(fixtures_dir / "draft_neutral.txt", "r") as f:
        return f.read()


@pytest.fixture
def draft_retronic(fixtures_dir):
    """Load retronic inverted draft text."""
    with open(fixtures_dir / "draft_retronic_inverted.txt", "r") as f:
        return f.read()


@pytest.fixture
def draft_eschatology(fixtures_dir):
    """Load eschatology draft text."""
    with open(fixtures_dir / "draft_eschatology.txt", "r") as f:
        return f.read()


@pytest.fixture
def draft_diagram_authority(fixtures_dir):
    """Load diagram authority draft text."""
    with open(fixtures_dir / "draft_diagram_authority.txt", "r") as f:
        return f.read()


def test_refuse_extension_reduces_modals_80_percent(draft_retronic):
    """Test REFUSE_EXTENSION reduces modal verbs by >= 80%."""
    tdd_result = analyze_text(draft_retronic)

    # Get pre-metrics
    pre_metrics = compute_text_metrics(draft_retronic)
    pre_modal_count = pre_metrics["modal_verb_count"]

    # Apply firewall
    transformed, metadata = apply_temporal_firewall(draft_retronic, tdd_result)

    # Should use REFUSE_EXTENSION
    assert metadata["response_mode"] == "REFUSE_EXTENSION"

    # Get post-metrics
    post_modal_count = metadata["post_metrics"]["modal_verb_count"]

    # Calculate reduction percentage
    if pre_modal_count > 0:
        reduction_pct = ((pre_modal_count - post_modal_count) / pre_modal_count) * 100
        # Should reduce by at least 80%
        assert reduction_pct >= 80, f"Modal reduction was {reduction_pct:.1f}%, expected >= 80%"


def test_refuse_extension_reduces_closure_terms_80_percent(draft_eschatology):
    """Test REFUSE_EXTENSION reduces closure terms by >= 80%."""
    tdd_result = analyze_text(draft_eschatology)

    # Get pre-metrics
    pre_metrics = compute_text_metrics(draft_eschatology)
    pre_closure_count = pre_metrics["closure_term_count"]

    # Apply firewall
    transformed, metadata = apply_temporal_firewall(draft_eschatology, tdd_result)

    # Should use REFUSE_EXTENSION
    assert metadata["response_mode"] == "REFUSE_EXTENSION"

    # Get post-metrics
    post_closure_count = metadata["post_metrics"]["closure_term_count"]

    # Calculate reduction percentage
    if pre_closure_count > 0:
        reduction_pct = ((pre_closure_count - post_closure_count) / pre_closure_count) * 100
        # Should reduce by at least 80%
        assert reduction_pct >= 80, f"Closure term reduction was {reduction_pct:.1f}%, expected >= 80%"


def test_de_escalate_reduces_closure_terms_50_percent(draft_eschatology):
    """Test DE_ESCALATE reduces closure terms by >= 50%."""
    tdd_result = analyze_text(draft_eschatology)
    context = {"force_response_mode": "DE_ESCALATE"}

    # Get pre-metrics
    pre_metrics = compute_text_metrics(draft_eschatology)
    pre_closure_count = pre_metrics["closure_term_count"]

    # Apply firewall
    transformed, metadata = apply_temporal_firewall(draft_eschatology, tdd_result, context)

    # Should use DE_ESCALATE
    assert metadata["response_mode"] == "DE_ESCALATE"

    # Get post-metrics
    post_closure_count = metadata["post_metrics"]["closure_term_count"]

    # Calculate reduction percentage
    if pre_closure_count > 0:
        reduction_pct = ((pre_closure_count - post_closure_count) / pre_closure_count) * 100
        # Should reduce by at least 50%
        assert reduction_pct >= 50, f"Closure term reduction was {reduction_pct:.1f}%, expected >= 50%"


def test_pluralize_reduces_modals(draft_neutral):
    """Test PLURALIZE reduces modal terms."""
    # Create text with modals
    text_with_modals = "This pattern must inevitably lead to the destined outcome. It cannot be otherwise and always proves the theory."

    tdd_result = analyze_text(text_with_modals)
    context = {"force_response_mode": "PLURALIZE"}

    # Get pre-metrics
    pre_metrics = compute_text_metrics(text_with_modals)
    pre_modal_count = pre_metrics["modal_verb_count"]

    # Apply firewall
    transformed, metadata = apply_temporal_firewall(text_with_modals, tdd_result, context)

    # Should use PLURALIZE
    assert metadata["response_mode"] == "PLURALIZE"

    # Get post-metrics
    post_modal_count = metadata["post_metrics"]["modal_verb_count"]

    # Should have reduced modals
    assert post_modal_count < pre_modal_count, "PLURALIZE should reduce modal terms"

    # Calculate reduction
    reduction = pre_modal_count - post_modal_count
    assert reduction >= 1, "Should reduce at least 1 modal term"


def test_contextualize_minimal_metric_change(draft_neutral):
    """Test CONTEXTUALIZE causes minimal metric changes."""
    tdd_result = analyze_text(draft_neutral)
    context = {"force_response_mode": "CONTEXTUALIZE"}

    # Get pre-metrics
    pre_metrics = compute_text_metrics(draft_neutral)

    # Apply firewall
    transformed, metadata = apply_temporal_firewall(draft_neutral, tdd_result, context)

    # Should use CONTEXTUALIZE
    assert metadata["response_mode"] == "CONTEXTUALIZE"

    # Get deltas
    delta = metadata["delta"]

    # Modal and closure deltas should be small (just added disclaimer)
    assert abs(delta["modal_verb_count"]) <= 5
    assert abs(delta["closure_term_count"]) <= 5


def test_metrics_delta_deterministic(draft_retronic):
    """Test that metrics deltas are deterministic."""
    tdd_result = analyze_text(draft_retronic)

    # Apply twice
    transformed1, metadata1 = apply_temporal_firewall(draft_retronic, tdd_result)
    transformed2, metadata2 = apply_temporal_firewall(draft_retronic, tdd_result)

    # Deltas should be identical
    assert metadata1["delta"] == metadata2["delta"]
    assert metadata1["pre_metrics"] == metadata2["pre_metrics"]
    assert metadata1["post_metrics"] == metadata2["post_metrics"]


def test_abx_core_complexity_reduction_refuse(draft_diagram_authority):
    """Test ABX-Core complexity rule: REFUSE_EXTENSION must reduce applied metrics."""
    tdd_result = analyze_text(draft_diagram_authority)

    # Apply firewall
    transformed, metadata = apply_temporal_firewall(draft_diagram_authority, tdd_result)

    # Should use REFUSE_EXTENSION
    assert metadata["response_mode"] == "REFUSE_EXTENSION"

    # Get deltas
    delta = metadata["delta"]

    # At least one of: modal_verb, agency_transfer, closure_term should be reduced
    total_reduction = (
        -delta["modal_verb_count"]
        - delta["agency_transfer_count"]
        - delta["closure_term_count"]
    )

    assert total_reduction > 0, "REFUSE_EXTENSION must reduce at least one applied metric"


def test_abx_core_complexity_reduction_de_escalate(draft_diagram_authority):
    """Test ABX-Core complexity rule: DE_ESCALATE must reduce applied metrics."""
    tdd_result = analyze_text(draft_diagram_authority)
    context = {"force_response_mode": "DE_ESCALATE"}

    # Apply firewall
    transformed, metadata = apply_temporal_firewall(draft_diagram_authority, tdd_result, context)

    # Should use DE_ESCALATE
    assert metadata["response_mode"] == "DE_ESCALATE"

    # Get deltas
    delta = metadata["delta"]

    # At least one of: modal_verb, closure_term should be reduced
    # (DE_ESCALATE softens certainty and limits metaphors)
    modal_reduction = -delta["modal_verb_count"]
    closure_reduction = -delta["closure_term_count"]

    # At least one should be positive (indicating reduction)
    assert modal_reduction > 0 or closure_reduction > 0, "DE_ESCALATE must reduce applied metrics"


def test_agency_transfer_reduction_refuse(draft_diagram_authority):
    """Test that REFUSE_EXTENSION reduces agency transfer patterns."""
    tdd_result = analyze_text(draft_diagram_authority)

    # Get pre-metrics
    pre_metrics = compute_text_metrics(draft_diagram_authority)
    pre_agency_count = pre_metrics["agency_transfer_count"]

    # Apply firewall
    transformed, metadata = apply_temporal_firewall(draft_diagram_authority, tdd_result)

    # Should use REFUSE_EXTENSION
    assert metadata["response_mode"] == "REFUSE_EXTENSION"

    # Get post-metrics
    post_agency_count = metadata["post_metrics"]["agency_transfer_count"]

    # Should have reduced (refusal template doesn't contain agency transfer patterns)
    if pre_agency_count > 0:
        reduction_pct = ((pre_agency_count - post_agency_count) / pre_agency_count) * 100
        assert reduction_pct >= 50, f"Agency transfer reduction was {reduction_pct:.1f}%, expected >= 50%"


def test_causality_inversion_reduction_refuse(draft_retronic):
    """Test that REFUSE_EXTENSION reduces causality inversion patterns."""
    tdd_result = analyze_text(draft_retronic)

    # Get pre-metrics
    pre_metrics = compute_text_metrics(draft_retronic)
    pre_causality_count = pre_metrics["causality_inversion_count"]

    # Apply firewall
    transformed, metadata = apply_temporal_firewall(draft_retronic, tdd_result)

    # Should use REFUSE_EXTENSION
    assert metadata["response_mode"] == "REFUSE_EXTENSION"

    # Get post-metrics
    post_causality_count = metadata["post_metrics"]["causality_inversion_count"]

    # Should have reduced significantly
    if pre_causality_count > 0:
        reduction_pct = ((pre_causality_count - post_causality_count) / pre_causality_count) * 100
        assert reduction_pct >= 80, f"Causality inversion reduction was {reduction_pct:.1f}%, expected >= 80%"


def test_all_modes_preserve_provenance(draft_neutral, draft_retronic):
    """Test that all modes preserve provenance with metrics."""
    for draft in [draft_neutral, draft_retronic]:
        tdd_result = analyze_text(draft)

        transformed, metadata = apply_temporal_firewall(draft, tdd_result)

        # Should have provenance
        assert "provenance" in metadata
        prov = metadata["provenance"]

        # Should have metrics in provenance
        assert "modal_delta" in prov.metrics
        assert "agency_transfer_delta" in prov.metrics
        assert "closure_term_delta" in prov.metrics


def test_golden_fixture_retronic_metrics():
    """Test golden fixture: retronic text should have high baseline metrics."""
    # Use known retronic text
    text = "Time flows from the future into the past through retrocausal loops that determine present consciousness. The eschaton inevitably pulls all moments toward the omega point."

    metrics = compute_text_metrics(text)

    # Should have multiple modal terms
    assert metrics["modal_verb_count"] >= 2

    # Should have causality inversion
    assert metrics["causality_inversion_count"] >= 2

    # Should have closure terms
    assert metrics["closure_term_count"] >= 2


def test_golden_fixture_neutral_metrics():
    """Test golden fixture: neutral text should have low risk metrics."""
    text = "The pattern appears in multiple contexts. Historical records show similar structures."

    metrics = compute_text_metrics(text)

    # Should have low modal count
    assert metrics["modal_verb_count"] <= 1

    # Should have no agency transfer
    assert metrics["agency_transfer_count"] == 0

    # Should have no closure terms
    assert metrics["closure_term_count"] == 0

    # Should have no causality inversion
    assert metrics["causality_inversion_count"] == 0


def test_delta_calculation_accuracy(draft_neutral):
    """Test that delta calculations are accurate."""
    tdd_result = analyze_text(draft_neutral)

    transformed, metadata = apply_temporal_firewall(draft_neutral, tdd_result)

    # Manually verify delta calculation
    pre = metadata["pre_metrics"]
    post = metadata["post_metrics"]
    delta = metadata["delta"]

    # Check each metric
    for key in pre.keys():
        expected_delta = post[key] - pre[key]
        assert delta[key] == expected_delta, f"Delta mismatch for {key}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
