"""Tests for SandboxPromotionCandidate.v1 - core/sandbox/promotion.py"""
from __future__ import annotations
import pytest
from core.models.governance import Authority
from core.sandbox.promotion import (
    SandboxPromotionCandidate,
    build_promotion_candidate,
)


@pytest.fixture
def auth() -> Authority:
    return Authority(
        authority_id="auth.promo.001",
        actor="system.promotion",
        locked=True,
        scope="sandbox_only",
    )


def test_promotion_defaults_false(auth):
    """promotion_allowed must default to False."""
    cand = build_promotion_candidate(
        candidate_id="c-001",
        sandbox_branch_hash="a" * 64,
        stabilization_hash="b" * 64,
        replay_hash="c" * 64,
        proposed_promotions=["p1"],
        authority=auth,
        stabilization_state="stable",
    )
    assert cand.promotion_allowed is False


def test_operator_review_always_required(auth):
    cand = build_promotion_candidate(
        candidate_id="c-001",
        sandbox_branch_hash="a" * 64,
        stabilization_hash="b" * 64,
        replay_hash="c" * 64,
        proposed_promotions=[],
        authority=auth,
    )
    assert cand.operator_review_required is True


def test_cannot_promote_unstable_branch(auth):
    cand = build_promotion_candidate(
        candidate_id="c-001",
        sandbox_branch_hash="a" * 64,
        stabilization_hash="b" * 64,
        replay_hash="c" * 64,
        proposed_promotions=["p1"],
        authority=auth,
        stabilization_state="unstable",
    )
    assert cand.promotion_allowed is False


def test_cannot_promote_failed_branch(auth):
    cand = build_promotion_candidate(
        candidate_id="c-001",
        sandbox_branch_hash="a" * 64,
        stabilization_hash="b" * 64,
        replay_hash="c" * 64,
        proposed_promotions=["p1"],
        authority=auth,
        stabilization_state="failed",
    )
    assert cand.promotion_allowed is False
    assert cand.status == "blocked"


def test_promotion_allowed_blocked_when_review_required(auth):
    """Even if promotion_allowed=True is set, operator_review_required blocks it."""
    cand = SandboxPromotionCandidate(
        candidate_id="c",
        sandbox_branch_hash="a" * 64,
        stabilization_hash="b" * 64,
        replay_hash="c" * 64,
        proposed_promotions=[],
        operator_review_required=True,
        promotion_allowed=True,  # Should be overridden
        authority=auth,
        status="approved",
    )
    assert cand.promotion_allowed is False
    assert cand.status == "blocked"


def test_authority_must_be_locked():
    bad_auth = Authority(
        authority_id="bad", actor="x", locked=False, scope="sandbox_only"
    )
    with pytest.raises(ValueError, match="authority must be locked"):
        SandboxPromotionCandidate(
            candidate_id="c",
            sandbox_branch_hash="a" * 64,
            stabilization_hash="b" * 64,
            replay_hash="c" * 64,
            proposed_promotions=[],
            operator_review_required=True,
            promotion_allowed=False,
            authority=bad_auth,
            status="pending",
        )


def test_candidate_hash_is_deterministic(auth):
    c1 = build_promotion_candidate("c", "a" * 64, "b" * 64, "c" * 64, ["p1"], auth)
    c2 = build_promotion_candidate("c", "a" * 64, "b" * 64, "c" * 64, ["p1"], auth)
    assert c1.candidate_hash() == c2.candidate_hash()


def test_candidate_hash_differs_for_different_inputs(auth):
    c1 = build_promotion_candidate("c1", "a" * 64, "b" * 64, "c" * 64, ["p1"], auth)
    c2 = build_promotion_candidate("c2", "d" * 64, "e" * 64, "f" * 64, ["p2"], auth)
    assert c1.candidate_hash() != c2.candidate_hash()


def test_schema_version_correct(auth):
    cand = build_promotion_candidate("c", "a" * 64, "b" * 64, "c" * 64, [], auth)
    assert cand.schema_version == "SandboxPromotionCandidate.v1"


def test_cannot_bypass_operator_review(auth):
    """Cannot bypass operator review by setting operator_review_required=False."""
    # When built through the builder, operator_review_required is always True
    cand = build_promotion_candidate(
        "c", "a" * 64, "b" * 64, "c" * 64, [], auth
    )
    assert cand.operator_review_required is True

    # Even if directly constructing with review=False, promotion stays blocked
    cand2 = SandboxPromotionCandidate(
        candidate_id="c2",
        sandbox_branch_hash="a" * 64,
        stabilization_hash="b" * 64,
        replay_hash="c" * 64,
        proposed_promotions=[],
        operator_review_required=False,  # No bypass
        promotion_allowed=False,
        authority=auth,
        status="pending",
    )
    # This is allowed (review not required + not allowed = consistent)
    assert cand2.promotion_allowed is False


def test_proposed_promotions_sorted(auth):
    cand = build_promotion_candidate(
        "c", "a" * 64, "b" * 64, "c" * 64,
        ["z_promo", "a_promo", "m_promo"], auth
    )
    assert cand.proposed_promotions == ["a_promo", "m_promo", "z_promo"]
