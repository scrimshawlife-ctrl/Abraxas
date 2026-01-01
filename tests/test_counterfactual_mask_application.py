"""
Tests for counterfactual mask application.
"""

from abraxas.replay.masks import apply_mask_to_influence_events
from abraxas.replay.types import ReplayInfluence, ReplayMask, ReplayMaskKind


def test_counterfactual_mask_application():
    influences = [
        ReplayInfluence(
            influence_id="inf_1",
            source_label="rss_a",
            quarantined=False,
            weight=0.4,
            source_class="signal",
            domain="AALMANAC",
        ),
        ReplayInfluence(
            influence_id="inf_2",
            source_label="rss_b",
            quarantined=True,
            weight=0.9,
            source_class="evidence_pack",
            domain="FORECAST",
        ),
    ]

    mask = ReplayMask(
        mask_id="exclude_sources",
        kind=ReplayMaskKind.EXCLUDE_SOURCE_LABELS,
        params={"source_labels": ["rss_a"]},
        description="exclude",
    )
    filtered = apply_mask_to_influence_events(influences, mask)
    assert [inf.influence_id for inf in filtered] == ["inf_2"]

    mask = ReplayMask(
        mask_id="exclude_quarantined",
        kind=ReplayMaskKind.EXCLUDE_QUARANTINED,
        params={},
        description="exclude quarantined",
    )
    filtered = apply_mask_to_influence_events(influences, mask)
    assert [inf.influence_id for inf in filtered] == ["inf_1"]

    mask = ReplayMask(
        mask_id="clamp_siw_max",
        kind=ReplayMaskKind.CLAMP_SIW_MAX,
        params={"max_w": 0.5},
        description="clamp",
    )
    filtered = apply_mask_to_influence_events(influences, mask)
    assert filtered[1].weight == 0.5

    mask = ReplayMask(
        mask_id="only_evidence_pack",
        kind=ReplayMaskKind.ONLY_EVIDENCE_PACK,
        params={},
        description="only evidence",
    )
    filtered = apply_mask_to_influence_events(influences, mask)
    assert [inf.influence_id for inf in filtered] == ["inf_2"]

    mask = ReplayMask(
        mask_id="exclude_domain",
        kind=ReplayMaskKind.EXCLUDE_DOMAIN,
        params={"domain": "AALMANAC"},
        description="exclude domain",
    )
    filtered = apply_mask_to_influence_events(influences, mask)
    assert [inf.influence_id for inf in filtered] == ["inf_2"]
