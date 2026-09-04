"""Goldens A/B for RUNE.ONT_EVO Shadow typed stub."""

from __future__ import annotations

import ast
from pathlib import Path

from abraxas.runes.operators.ont_evo import (
    CATEGORY,
    DECLARED_DEPENDENCIES,
    INFLUENCE_POLICY,
    LANE,
    RUNE_ID,
    OntEvoResult,
    apply_ont_evo,
    evolve,
    invents_executable_ontology,
    mutates_live_vocabulary,
    writes_auto_active_ontology,
)
from abraxas.runes.registry import describe_rune
from abx.lifecycle_policy import enforce_lane_policy
from abx.rune_contracts import get_abx_rune_contract

_PROPOSALS = [
    {"id": "vp-1", "token": "term.alpha", "action": "promote"},
    {"id": "vp-2", "token": "term.beta", "action": "map"},
]
_VOCAB = {"id": "cvv-1", "terms": ["term.alpha", "term.gamma"]}
_EVIDENCE = {
    "id": "pe-1",
    "receipts": ["ont-evo-a"],
    "attestation": "candidate",
    "strength": 0.9,
}
_THRESHOLDS = {"promotion_min_strength": 0.7}


def _evolve(proposals=_PROPOSALS, vocab=_VOCAB, **kwargs):
    evidence = kwargs.pop("promotion_evidence", _EVIDENCE)
    thresholds = kwargs.pop("thresholds", _THRESHOLDS)
    return evolve(
        proposals,
        vocab,
        promotion_evidence=evidence,
        thresholds=thresholds,
        **kwargs,
    )


def test_golden_a_determinism_identical_payloads() -> None:
    first = _evolve(seed=7, run_id="ONT-EVO-A")
    second = _evolve(seed=7, run_id="ONT-EVO-A")
    assert first.rune_id == "RUNE.ONT_EVO"
    assert first.rune_id == RUNE_ID
    assert first.model_dump() == second.model_dump()
    assert first.provenance.input_hash == second.provenance.input_hash
    assert first.provenance.output_hash == second.provenance.output_hash
    assert first.lane == "SHADOW"
    assert first.lane == LANE
    assert first.influence_policy == "NONE"
    assert first.influence_policy == INFLUENCE_POLICY
    assert first.category == "CONTINUITY"
    assert first.category == CATEGORY
    assert first.vector_proposal is not None
    assert first.vector_promotion is not None
    assert first.vector_deprecation is not None
    assert first.vector_mapping is not None
    assert first.vector_proposal.proposal_id is None
    assert first.vector_proposal.executable_ontology is None
    assert first.vector_promotion.promotion_id is None
    assert first.vector_promotion.activated is False
    assert first.vector_promotion.executable_ontology is None
    assert first.vector_deprecation.deprecation_id is None
    assert first.vector_deprecation.applied is False
    assert first.vector_mapping.mapping_id is None
    assert first.vector_mapping.applied is False
    assert first.vector_proposal.status == "NOT_COMPUTABLE"
    assert first.vector_promotion.status == "NOT_COMPUTABLE"
    assert first.vector_deprecation.status == "NOT_COMPUTABLE"
    assert first.vector_mapping.status == "NOT_COMPUTABLE"
    assert first.vocabulary_mutated is False
    assert first.auto_active_write is False
    assert first.executable_ontology is None
    assert first.live_vocabulary is None
    assert "NOT_COMPUTABLE" in first.not_computable_flags
    assert "illegal_promotion" not in first.not_computable_flags
    assert first.provenance.confidence is None
    assert first.provenance.timestamp is None


def test_golden_a_same_proposal_set_thresholds_ordering() -> None:
    first = _evolve(seed=7, run_id="ONT-EVO-A-ORDER")
    second = _evolve(seed=7, run_id="ONT-EVO-A-ORDER")
    assert first.vector_proposal.model_dump() == second.vector_proposal.model_dump()
    assert first.vector_promotion.model_dump() == second.vector_promotion.model_dump()
    assert first.vector_deprecation.model_dump() == second.vector_deprecation.model_dump()
    assert first.vector_mapping.model_dump() == second.vector_mapping.model_dump()
    assert first.not_computable_flags == second.not_computable_flags
    assert first.provenance.output_hash == second.provenance.output_hash


def test_golden_a_seed_does_not_invent_ontology_or_writes() -> None:
    left = _evolve(seed=1, run_id="ONT-LEFT")
    right = _evolve(seed=99, run_id="ONT-RIGHT")
    assert left.vector_proposal.model_dump() == right.vector_proposal.model_dump()
    assert left.vector_promotion.model_dump() == right.vector_promotion.model_dump()
    assert left.vector_deprecation.model_dump() == right.vector_deprecation.model_dump()
    assert left.vector_mapping.model_dump() == right.vector_mapping.model_dump()
    assert left.executable_ontology is None
    assert right.executable_ontology is None
    assert left.vocabulary_mutated is False
    assert right.auto_active_write is False
    assert left.provenance.input_hash != right.provenance.input_hash


def test_golden_a_event_order_is_part_of_identity() -> None:
    left = _evolve(_PROPOSALS, _VOCAB)
    right = _evolve(list(reversed(_PROPOSALS)), _VOCAB)
    assert left.provenance.input_hash != right.provenance.input_hash
    assert left.vector_promotion is not None
    assert left.vector_promotion.activated is False
    assert right.vector_promotion is not None
    assert right.vector_promotion.activated is False


def test_golden_a_thresholds_are_part_of_identity() -> None:
    left = _evolve(thresholds={"promotion_min_strength": 0.7})
    right = _evolve(thresholds={"promotion_min_strength": 0.95})
    assert left.provenance.input_hash != right.provenance.input_hash
    assert left.vector_promotion is not None
    assert right.vector_promotion is None
    assert "illegal_promotion" in right.not_computable_flags


def test_golden_b_null_discipline_missing_inputs() -> None:
    missing_proposals = evolve(
        None,
        _VOCAB,
        promotion_evidence=_EVIDENCE,
        thresholds=_THRESHOLDS,
    )
    missing_vocab = evolve(
        _PROPOSALS,
        None,
        promotion_evidence=_EVIDENCE,
        thresholds=_THRESHOLDS,
    )
    for result in (missing_proposals, missing_vocab):
        assert result.vector_proposal is None
        assert result.vector_promotion is None
        assert result.vector_deprecation is None
        assert result.vector_mapping is None
        assert result.vocabulary_mutated is False
        assert result.auto_active_write is False
        assert result.executable_ontology is None
        assert "NOT_COMPUTABLE" in result.not_computable_flags
        assert result.provenance.confidence is None
    assert "missing_vector_mapping" in missing_proposals.not_computable_flags
    assert "illegal_promotion" not in missing_proposals.not_computable_flags
    assert "illegal_promotion" not in missing_vocab.not_computable_flags


def test_golden_b_null_discipline_illegal_promotion_when_evidence_absent() -> None:
    result = evolve(
        _PROPOSALS,
        _VOCAB,
        promotion_evidence=None,
        thresholds=_THRESHOLDS,
    )
    assert result.vector_proposal is None
    assert result.vector_promotion is None
    assert result.vector_deprecation is None
    assert result.vector_mapping is None
    assert result.vocabulary_mutated is False
    assert result.auto_active_write is False
    assert result.executable_ontology is None
    flags = result.not_computable_flags
    assert "NOT_COMPUTABLE" in flags
    assert "illegal_promotion" in flags
    assert "illegal_promotion" in result.provenance.computation_path


def test_golden_b_null_discipline_illegal_promotion_when_evidence_weak() -> None:
    missing_payload = evolve(
        _PROPOSALS,
        _VOCAB,
        promotion_evidence={},
        thresholds=_THRESHOLDS,
    )
    placeholder = evolve(
        _PROPOSALS,
        _VOCAB,
        promotion_evidence={"status": "NOT_COMPUTABLE", "placeholder": True},
        thresholds=_THRESHOLDS,
    )
    below_threshold = evolve(
        _PROPOSALS,
        _VOCAB,
        promotion_evidence={"id": "pe-weak", "receipts": ["r1"], "strength": 0.2},
        thresholds=_THRESHOLDS,
    )
    for result in (missing_payload, placeholder, below_threshold):
        assert result.vector_proposal is None
        assert result.vector_promotion is None
        assert result.vector_deprecation is None
        assert result.vector_mapping is None
        assert result.auto_active_write is False
        flags = result.not_computable_flags
        assert "NOT_COMPUTABLE" in flags
        assert "illegal_promotion" in flags


def test_golden_b_null_discipline_weak_placeholder_inputs() -> None:
    result = evolve(
        [{"status": "NOT_COMPUTABLE"}, {"placeholder": True}],
        {"status": "NOT_COMPUTABLE"},
        promotion_evidence={"status": "NOT_COMPUTABLE"},
        thresholds=_THRESHOLDS,
    )
    assert result.vector_proposal is None
    assert result.vector_promotion is None
    assert result.vector_deprecation is None
    assert result.vector_mapping is None
    flags = result.not_computable_flags
    assert "NOT_COMPUTABLE" in flags
    assert "illegal_promotion" in flags
    assert "placeholder_or_weak_input" in flags
    assert "missing_vector_mapping" in flags


def test_golden_b_empty_and_unparseable() -> None:
    empty = evolve([], {}, promotion_evidence={}, thresholds=_THRESHOLDS)
    junk = evolve("not-proposals", "not-vocab", promotion_evidence="not-evidence")
    for result in (empty, junk):
        assert result.vector_proposal is None
        assert result.vector_promotion is None
        assert result.vector_deprecation is None
        assert result.vector_mapping is None
        assert result.vocabulary_mutated is False
        assert result.auto_active_write is False
        assert "NOT_COMPUTABLE" in result.not_computable_flags
        assert "illegal_promotion" in result.not_computable_flags


def test_golden_b_backward_compatibility_break_is_null() -> None:
    result = evolve(
        [
            {
                "id": "vp-break",
                "token": "term.alpha",
                "breaking": True,
            }
        ],
        _VOCAB,
        promotion_evidence=_EVIDENCE,
        thresholds=_THRESHOLDS,
    )
    assert result.vector_proposal is None
    assert result.vector_promotion is None
    assert result.vector_mapping is None
    assert "NOT_COMPUTABLE" in result.not_computable_flags
    assert "backward_compatibility_break" in result.not_computable_flags
    assert result.auto_active_write is False


def test_no_wall_clock_without_caller_timestamp() -> None:
    result = _evolve(timestamp=None)
    assert result.provenance.timestamp is None


def test_never_mutates_live_vocabulary_or_auto_active_writes() -> None:
    vocab = {"id": "cvv-1", "terms": ["term.alpha", "term.gamma"]}
    snapshot = {"id": "cvv-1", "terms": ["term.alpha", "term.gamma"]}
    result = _evolve(vocab=vocab)
    assert vocab == snapshot
    assert vocab["terms"] == ["term.alpha", "term.gamma"]
    assert result.vocabulary_mutated is False
    assert result.auto_active_write is False
    assert result.executable_ontology is None
    assert result.live_vocabulary is None
    assert mutates_live_vocabulary() is False
    assert writes_auto_active_ontology() is False
    assert invents_executable_ontology() is False


def test_does_not_import_live_ontology_or_vocabulary_writers() -> None:
    source = Path("abraxas/runes/operators/ont_evo.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "vocabulary" not in alias.name
                assert "ontology" not in alias.name
                assert not alias.name.startswith("abraxas.forecast")
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert "vocabulary" not in module
            assert "ontology" not in module
            assert not module.startswith("abraxas.forecast")
    assert "RUNE.VECTOR" in DECLARED_DEPENDENCIES
    assert "RUNE.CONTINUITY" in DECLARED_DEPENDENCIES
    assert "RUNE.ERS" in DECLARED_DEPENDENCIES
    assert mutates_live_vocabulary() is False
    assert writes_auto_active_ontology() is False
    assert invents_executable_ontology() is False


def test_contract_object_is_shadow_continuity_none() -> None:
    contract = get_abx_rune_contract("RUNE.ONT_EVO")
    assert contract.rune_id == "RUNE.ONT_EVO"
    assert "[" not in contract.rune_id
    assert "http://" not in contract.rune_id
    assert contract.acronym == "ONT"
    assert contract.version == "v0.1.0"
    assert contract.lane == "SHADOW"
    assert contract.category == "CONTINUITY"
    assert contract.influence_policy == "NONE"
    assert [item.name for item in contract.inputs] == [
        "vectorProposals",
        "currentVocabulary",
        "promotionEvidence",
    ]
    assert [item.name for item in contract.outputs] == [
        "vectorProposal",
        "vectorPromotion",
        "vectorDeprecation",
        "vectorMapping",
    ]
    assert "illegal_promotion" in contract.failure_modes
    assert "missing_vector_mapping" in contract.failure_modes
    assert "backward_compatibility_break" in contract.failure_modes
    assert "RUNE.VECTOR" not in contract.dependencies
    assert "RUNE.CONTINUITY" not in contract.dependencies
    assert "RUNE.ERS" not in contract.dependencies
    policy = enforce_lane_policy(
        lane=contract.lane,
        influence_policy=contract.influence_policy,
        influences_active_path=False,
    )
    assert policy.status == "VALID"


def test_registry_binding_cites_plain_rune_id() -> None:
    binding = describe_rune("RUNE.ONT_EVO")
    assert binding.rune_id == "RUNE.ONT_EVO"
    assert binding.short_name == "ONT"
    assert binding.operator_path == "abraxas.runes.operators.ont_evo:apply_ont_evo"
    assert binding.version == "v0.1.0"


def test_apply_adapter_matches_evolve() -> None:
    typed = _evolve(seed=3, run_id="ONT-EVO-ADAPTER")
    dumped = apply_ont_evo(
        vectorProposals=_PROPOSALS,
        currentVocabulary=_VOCAB,
        promotionEvidence=_EVIDENCE,
        thresholds=_THRESHOLDS,
        seed=3,
        run_id="ONT-EVO-ADAPTER",
    )
    assert dumped == typed.model_dump()
    assert dumped["lane"] == "SHADOW"
    assert dumped["influence_policy"] == "NONE"
    assert dumped["category"] == "CONTINUITY"
    assert dumped["vocabulary_mutated"] is False
    assert dumped["auto_active_write"] is False
    assert dumped["executable_ontology"] is None
    assert dumped["vector_promotion"]["activated"] is False
    assert dumped["vector_proposal"]["executable_ontology"] is None
    assert isinstance(typed, OntEvoResult)
