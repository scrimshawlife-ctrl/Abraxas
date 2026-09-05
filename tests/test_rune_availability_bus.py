"""Goldens A/B plus fail-closed gates for RUNE.AVAILABILITY_BUS Shadow typed stub."""

from __future__ import annotations

from abraxas.runes.operators.availability_bus import (
    DISTINCT_FROM,
    RUNE_ID,
    AvailabilityBusResult,
    admit,
    apply_availability_bus,
)
from abraxas.runes.registry import describe_rune
from abx.lifecycle_policy import enforce_lane_policy
from abx.rune_contracts import get_abx_rune_contract

_ADMISSION = {"id": "RUNE.AVAILABILITY_BUS", "status": "canon-shadow"}
_HONESTY = {"id": "honesty-1", "verdict": "clear", "axes": {"hold": False}}
_PROMOTION = {"id": "promo-0", "lane": "SHADOW", "human_yes": False}


def _admit(admission=None, honesty=None, **kwargs):
    if admission is None:
        admission = dict(_ADMISSION)
    if honesty is None:
        honesty = dict(_HONESTY)
    if "promotion_event" not in kwargs:
        kwargs["promotion_event"] = dict(_PROMOTION)
    return admit(admission, honesty, **kwargs)


def test_golden_a_determinism_identical_payloads() -> None:
    first = _admit(seed=7, run_id="AVL-A")
    second = _admit(seed=7, run_id="AVL-A")
    assert first.rune_id == "RUNE.AVAILABILITY_BUS"
    assert first.rune_id == RUNE_ID
    assert first.model_dump() == second.model_dump()
    assert first.provenance.input_hash == second.provenance.input_hash
    assert first.provenance.output_hash == second.provenance.output_hash
    assert first.lane == "SHADOW"
    assert first.influence_policy == "NONE"
    assert first.availability_packet.availability is None
    assert first.availability_packet.access is None
    assert first.availability_packet.admitted_id == "RUNE.AVAILABILITY_BUS"
    assert first.access_report.claim is None
    assert first.access_report.reportable is None
    assert first.access_report.access_only is True
    assert first.seal_receipt.sealed is None
    assert first.seal_receipt.receipt_id is None
    assert first.availability_packet.status == "NOT_COMPUTABLE"
    assert first.access_report.status == "NOT_COMPUTABLE"
    assert first.seal_receipt.status == "NOT_COMPUTABLE"
    assert "NOT_COMPUTABLE" in first.availability_packet.not_computable_flags
    assert "availability_not_computable" in first.availability_packet.not_computable_flags
    assert first.provenance.confidence is None
    assert first.rune_id != DISTINCT_FROM


def test_golden_a_optional_field_order_is_part_of_identity() -> None:
    left = _admit(chrono_packet={"id": "chp-1", "marker": "a"})
    right = _admit(chrono_packet={"id": "chp-1", "marker": "b"})
    assert left.provenance.input_hash != right.provenance.input_hash
    assert left.availability_packet.availability is None
    assert right.availability_packet.availability is None


def test_golden_a_seed_does_not_invent_availability() -> None:
    left = _admit(seed=1)
    right = _admit(seed=99)
    assert left.availability_packet.model_dump() == right.availability_packet.model_dump()
    assert left.access_report.model_dump() == right.access_report.model_dump()
    assert left.seal_receipt.model_dump() == right.seal_receipt.model_dump()
    assert left.provenance.input_hash != right.provenance.input_hash


def test_golden_b_null_discipline_missing_inputs() -> None:
    missing_admission = admit(None, _HONESTY, promotion_event=_PROMOTION)
    missing_honesty = admit(_ADMISSION, None, promotion_event=_PROMOTION)
    for result in (missing_admission, missing_honesty):
        assert result.availability_packet.availability is None
        assert result.availability_packet.access is None
        assert result.availability_packet.admitted_id is None
        assert result.access_report.claim is None
        assert result.access_report.reportable is False
        assert result.seal_receipt.sealed is False
        assert result.availability_packet.status == "NOT_COMPUTABLE"
        assert "NOT_COMPUTABLE" in result.availability_packet.not_computable_flags
        assert "availability_not_computable" in result.availability_packet.not_computable_flags
        assert result.provenance.confidence is None


def test_golden_b_null_discipline_weak_placeholder() -> None:
    result = admit(
        {"status": "NOT_COMPUTABLE"},
        {"status": "NOT_COMPUTABLE", "verdict": "clear"},
        promotion_event=None,
    )
    assert result.availability_packet.availability is None
    assert result.access_report.claim is None
    assert result.seal_receipt.receipt_id is None
    flags = result.availability_packet.not_computable_flags
    assert "NOT_COMPUTABLE" in flags
    assert "availability_not_computable" in flags
    assert "placeholder_or_weak_input" in flags
    assert "registry_id_missing" in flags


def test_golden_b_empty_and_unparseable() -> None:
    empty = admit({}, {}, promotion_event={})
    junk = admit("not-admission", "not-honesty", promotion_event="not-promo")
    for result in (empty, junk):
        assert result.availability_packet.availability is None
        assert result.access_report.claim is None
        assert "NOT_COMPUTABLE" in result.availability_packet.not_computable_flags
        assert "availability_not_computable" in result.availability_packet.not_computable_flags


def test_fail_closed_phenomenology_claim() -> None:
    result = _admit(
        admission={"id": "RUNE.AVAILABILITY_BUS", "note": "phenomenology resolved"},
    )
    flags = result.availability_packet.not_computable_flags
    assert "phenomenology_claim" in flags
    assert result.availability_packet.admitted_id is None
    assert result.access_report.reportable is False
    assert result.seal_receipt.sealed is False
    assert result.availability_packet.availability is None
    assert result.lane == "SHADOW"
    assert result.influence_policy == "NONE"


def test_fail_closed_consciousness_module_naming() -> None:
    result = _admit(
        admission={"id": "consciousness_module", "name": "consciousness module"},
    )
    flags = result.availability_packet.not_computable_flags
    assert "consciousness_module_naming" in flags
    assert result.availability_packet.admitted_id is None
    assert result.access_report.reportable is False
    assert result.access_report.claim is None
    dumped = result.model_dump()
    assert "qualia" not in str(dumped).lower()
    assert "sentience" not in str(dumped).lower()


def test_fail_closed_honesty_hold() -> None:
    result = _admit(honesty={"id": "honesty-hold", "verdict": "hold"})
    flags = result.availability_packet.not_computable_flags
    assert "honesty_hold" in flags
    assert result.availability_packet.admitted_id is None
    assert result.access_report.reportable is False
    assert result.seal_receipt.sealed is False
    assert result.availability_packet.availability is None


def test_fail_closed_registry_id_missing() -> None:
    result = admit({"status": "canon-shadow"}, _HONESTY, promotion_event=_PROMOTION)
    flags = result.availability_packet.not_computable_flags
    assert "registry_id_missing" in flags
    assert result.availability_packet.admitted_id is None
    assert result.access_report.reportable is False
    assert result.seal_receipt.sealed is False


def test_fail_closed_active_without_human_yes() -> None:
    result = _admit(promotion_event={"lane": "ACTIVE", "human_yes": False})
    flags = result.availability_packet.not_computable_flags
    assert "active_without_human_yes" in flags
    assert result.lane == "SHADOW"
    assert result.influence_policy == "NONE"
    assert result.availability_packet.admitted_id is None


def test_no_wall_clock_without_caller_timestamp() -> None:
    result = _admit(timestamp=None)
    assert result.provenance.timestamp is None


def test_contract_object_is_shadow_route_none() -> None:
    contract = get_abx_rune_contract("RUNE.AVAILABILITY_BUS")
    assert contract.rune_id == "RUNE.AVAILABILITY_BUS"
    assert contract.rune_id != "RUNE.CHRONO_PACKET"
    assert contract.rune_id != DISTINCT_FROM
    assert "[" not in contract.rune_id
    assert "http://" not in contract.rune_id
    assert contract.acronym == "AVL"
    assert contract.acronym != "AVB"
    assert contract.version == "v0.1.0"
    assert contract.lane == "SHADOW"
    assert contract.category == "ROUTE"
    assert contract.category != "GOVERN"
    assert contract.influence_policy == "NONE"
    assert [item.name for item in contract.inputs] == [
        "registryAdmission",
        "promotionEvent",
        "shadowHonestyVerdict",
        "driftParity",
        "chronoPacket",
        "timechainSeal",
        "prismCardLifecycle",
    ]
    assert [item.name for item in contract.outputs] == [
        "availabilityPacket",
        "accessReport",
        "sealReceipt",
    ]
    assert "phenomenology_claim" in contract.failure_modes
    assert "consciousness_module_naming" in contract.failure_modes
    assert "honesty_hold" in contract.failure_modes
    assert "registry_id_missing" in contract.failure_modes
    assert "active_without_human_yes" in contract.failure_modes
    assert "RUNE.TRUST" not in contract.dependencies
    assert "RUNE.DRIFT" not in contract.dependencies
    assert "RUNE.ERS" not in contract.dependencies
    policy = enforce_lane_policy(
        lane=contract.lane,
        influence_policy=contract.influence_policy,
        influences_active_path=False,
    )
    assert policy.status == "VALID"


def test_registry_binding_cites_plain_rune_id() -> None:
    binding = describe_rune("RUNE.AVAILABILITY_BUS")
    assert binding.rune_id == "RUNE.AVAILABILITY_BUS"
    assert binding.rune_id != "RUNE.CHRONO_PACKET"
    assert binding.short_name == "AVL"
    assert binding.operator_path == (
        "abraxas.runes.operators.availability_bus:apply_availability_bus"
    )
    assert binding.version == "v0.1.0"


def test_apply_adapter_matches_admit() -> None:
    typed = _admit(seed=3, run_id="AVL-ADAPTER")
    dumped = apply_availability_bus(
        registryAdmission=_ADMISSION,
        shadowHonestyVerdict=_HONESTY,
        promotionEvent=_PROMOTION,
        seed=3,
        run_id="AVL-ADAPTER",
    )
    assert dumped["availabilityPacket"] == typed.availability_packet.model_dump()
    assert dumped["accessReport"] == typed.access_report.model_dump()
    assert dumped["sealReceipt"] == typed.seal_receipt.model_dump()
    assert "availability_packet" not in dumped
    assert "access_report" not in dumped
    assert "seal_receipt" not in dumped
    assert dumped["lane"] == "SHADOW"
    assert dumped["influence_policy"] == "NONE"
    assert dumped["availabilityPacket"]["availability"] is None
    assert dumped["accessReport"]["access_only"] is True
    assert [item.name for item in get_abx_rune_contract("RUNE.AVAILABILITY_BUS").outputs] == [
        "availabilityPacket",
        "accessReport",
        "sealReceipt",
    ]
    assert isinstance(typed, AvailabilityBusResult)
