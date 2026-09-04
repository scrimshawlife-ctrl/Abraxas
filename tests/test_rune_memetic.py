"""Goldens A/B for RUNE.MEMETIC Shadow typed stub."""

from __future__ import annotations

from abraxas.runes.operators.memetic import (
    DISTINCT_FROM,
    RUNE_ID,
    MemeticResult,
    aliases_memetic_capability,
    apply_memetic,
    detect,
)
from abraxas.runes.registry import describe_rune
from abx.lifecycle_policy import enforce_lane_policy
from abx.rune_contracts import get_abx_rune_contract

_SLANG = [
    {"id": "se-1", "token": "yeet"},
    {"id": "se-2", "token": "rizz"},
]
_ECO = [
    {"id": "ee-1", "form": "eggcorn-a"},
    {"id": "ee-2", "form": "eggcorn-b"},
]
_WINDOW = {"id": "win-1", "lookback_span": "7d"}

_MEMETIC_CAPABILITY_IDS = (
    "ϟ_MEMETIC_SOURCES_LOAD",
    "ϟ_MEMETIC_EXTRACT_CLAIMS",
    "ϟ_MEMETIC_CLUSTER_CLAIMS",
    "ϟ_MEMETIC_DMX_CONTEXT",
    "ϟ_MEMETIC_TERM_INDEX_BUILD",
)


def _detect(slang=_SLANG, eco=_ECO, window=_WINDOW, **kwargs):
    return detect(slang, eco, window, **kwargs)


def test_golden_a_determinism_identical_payloads() -> None:
    first = _detect(seed=7, run_id="MEMETIC-A")
    second = _detect(seed=7, run_id="MEMETIC-A")
    assert first.rune_id == "RUNE.MEMETIC"
    assert first.rune_id == RUNE_ID
    assert first.model_dump() == second.model_dump()
    assert first.provenance.input_hash == second.provenance.input_hash
    assert first.provenance.output_hash == second.provenance.output_hash
    assert first.lane == "SHADOW"
    assert first.influence_policy == "NONE"
    assert first.vernacular_rows is None
    assert first.memetic_cluster is not None
    assert first.memetic_artifact is not None
    assert first.narrative_tracks is not None
    assert first.memetic_cluster.cluster_id is None
    assert first.memetic_cluster.members is None
    assert first.memetic_cluster.vernacular_rows is None
    assert first.memetic_cluster.score is None
    assert first.memetic_artifact.artifact_id is None
    assert first.memetic_artifact.payload is None
    assert first.memetic_artifact.vernacular_rows is None
    assert len(first.narrative_tracks) == 1
    assert first.narrative_tracks[0].track_id is None
    assert first.narrative_tracks[0].score is None
    assert first.narrative_tracks[0].status == "NOT_COMPUTABLE"
    assert first.memetic_cluster.status == "NOT_COMPUTABLE"
    assert first.memetic_artifact.status == "NOT_COMPUTABLE"
    assert "NOT_COMPUTABLE" in first.not_computable_flags
    assert "contamination_not_computable" in first.not_computable_flags
    assert "cluster_formation_fail" in first.not_computable_flags
    assert first.provenance.confidence is None


def test_golden_a_event_order_is_part_of_identity() -> None:
    left = _detect(_SLANG, _ECO, _WINDOW)
    right = _detect(list(reversed(_SLANG)), _ECO, _WINDOW)
    assert left.provenance.input_hash != right.provenance.input_hash
    assert left.vernacular_rows is None
    assert right.vernacular_rows is None
    assert left.memetic_cluster is not None
    assert left.memetic_cluster.score is None
    assert right.memetic_cluster is not None
    assert right.memetic_cluster.score is None


def test_golden_a_seed_does_not_invent_vernacular_or_clusters() -> None:
    left = _detect(seed=1)
    right = _detect(seed=99)
    assert left.memetic_cluster.model_dump() == right.memetic_cluster.model_dump()
    assert left.memetic_artifact.model_dump() == right.memetic_artifact.model_dump()
    assert [track.model_dump() for track in left.narrative_tracks] == [
        track.model_dump() for track in right.narrative_tracks
    ]
    assert left.vernacular_rows is None
    assert right.vernacular_rows is None
    assert left.provenance.input_hash != right.provenance.input_hash


def test_golden_b_null_discipline_missing_inputs() -> None:
    missing_slang = detect(None, _ECO, _WINDOW)
    missing_eco = detect(_SLANG, None, _WINDOW)
    missing_window = detect(_SLANG, _ECO, None)
    for result in (missing_slang, missing_eco, missing_window):
        assert result.memetic_cluster is None
        assert result.memetic_artifact is None
        assert result.narrative_tracks is None
        assert result.vernacular_rows is None
        assert "NOT_COMPUTABLE" in result.not_computable_flags
        assert "contamination_not_computable" in result.not_computable_flags
        assert result.provenance.confidence is None
    assert "missing_slang_or_eco_lineage" in missing_slang.not_computable_flags
    assert "missing_slang_or_eco_lineage" in missing_eco.not_computable_flags


def test_golden_b_null_discipline_weak_placeholder() -> None:
    result = detect(
        [{"status": "NOT_COMPUTABLE"}, {"placeholder": True}],
        [{"status": "NOT_COMPUTABLE"}],
        {"status": "NOT_COMPUTABLE"},
    )
    assert result.memetic_cluster is None
    assert result.memetic_artifact is None
    assert result.narrative_tracks is None
    assert result.vernacular_rows is None
    flags = result.not_computable_flags
    assert "NOT_COMPUTABLE" in flags
    assert "contamination_not_computable" in flags
    assert "placeholder_or_weak_input" in flags
    assert "missing_slang_or_eco_lineage" in flags


def test_golden_b_empty_and_unparseable() -> None:
    empty = detect([], [], {})
    junk = detect("not-slang", "not-eco", "not-window")
    for result in (empty, junk):
        assert result.memetic_cluster is None
        assert result.memetic_artifact is None
        assert result.narrative_tracks is None
        assert result.vernacular_rows is None
        assert "NOT_COMPUTABLE" in result.not_computable_flags
        assert "contamination_not_computable" in result.not_computable_flags


def test_no_wall_clock_without_caller_timestamp() -> None:
    result = _detect(timestamp=None)
    assert result.provenance.timestamp is None


def test_never_aliases_memetic_capability_operators() -> None:
    assert RUNE_ID == "RUNE.MEMETIC"
    assert RUNE_ID != DISTINCT_FROM
    assert not aliases_memetic_capability(RUNE_ID)
    for capability_id in _MEMETIC_CAPABILITY_IDS:
        assert RUNE_ID != capability_id
        assert aliases_memetic_capability(capability_id)


def test_contract_object_is_shadow_detect_none() -> None:
    contract = get_abx_rune_contract("RUNE.MEMETIC")
    assert contract.rune_id == "RUNE.MEMETIC"
    assert contract.rune_id != DISTINCT_FROM
    assert "[" not in contract.rune_id
    assert "http://" not in contract.rune_id
    assert not contract.rune_id.startswith("ϟ_MEMETIC_")
    assert contract.acronym == "MEM"
    assert contract.version == "v0.1.0"
    assert contract.lane == "SHADOW"
    assert contract.category == "DETECT"
    assert contract.influence_policy == "NONE"
    assert [item.name for item in contract.inputs] == [
        "slangEvents",
        "eggcornEvents",
        "windowSpec",
    ]
    assert [item.name for item in contract.outputs] == [
        "memeticCluster",
        "memeticArtifact",
        "narrativeTracks",
    ]
    assert "contamination_not_computable" in contract.failure_modes
    assert "missing_slang_or_eco_lineage" in contract.failure_modes
    assert "cluster_formation_fail" in contract.failure_modes
    assert "RUNE.SLANG" not in contract.dependencies
    assert "RUNE.ECO" not in contract.dependencies
    assert "RUNE.DRIFT" not in contract.dependencies
    assert "RUNE.ERS" not in contract.dependencies
    policy = enforce_lane_policy(
        lane=contract.lane,
        influence_policy=contract.influence_policy,
        influences_active_path=False,
    )
    assert policy.status == "VALID"


def test_registry_binding_cites_plain_rune_id() -> None:
    binding = describe_rune("RUNE.MEMETIC")
    assert binding.rune_id == "RUNE.MEMETIC"
    assert not binding.rune_id.startswith("ϟ_MEMETIC_")
    assert binding.short_name == "MEM"
    assert binding.operator_path == "abraxas.runes.operators.memetic:apply_memetic"
    assert binding.version == "v0.1.0"


def test_apply_adapter_matches_detect() -> None:
    typed = _detect(seed=3, run_id="MEMETIC-ADAPTER")
    dumped = apply_memetic(
        slangEvents=_SLANG,
        eggcornEvents=_ECO,
        windowSpec=_WINDOW,
        seed=3,
        run_id="MEMETIC-ADAPTER",
    )
    assert dumped == typed.model_dump()
    assert dumped["lane"] == "SHADOW"
    assert dumped["influence_policy"] == "NONE"
    assert dumped["vernacular_rows"] is None
    assert dumped["memetic_cluster"]["score"] is None
    assert dumped["memetic_cluster"]["vernacular_rows"] is None
    assert isinstance(typed, MemeticResult)
