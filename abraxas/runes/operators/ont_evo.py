"""ABX-Rune Operator: RUNE.ONT_EVO (ONT).

Shadow typed stub only. Placeholder types stay NOT_COMPUTABLE.
Does not mutate live CanonicalVectorVocabulary, Auto-Active write,
invent executable ontology, or influence Forecast.
"""

from __future__ import annotations

from typing import Literal, Mapping, Sequence

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex

RUNE_ID = "RUNE.ONT_EVO"
RUNE_VERSION = "v0.1.0"
LANE: Literal["SHADOW"] = "SHADOW"
INFLUENCE_POLICY: Literal["NONE"] = "NONE"
CATEGORY: Literal["CONTINUITY"] = "CONTINUITY"
DECLARED_DEPENDENCIES = (
    "RUNE.VECTOR",
    "RUNE.CONTINUITY",
    "RUNE.ERS",
)

_FLAG_NOT_COMPUTABLE = "NOT_COMPUTABLE"
_FLAG_ILLEGAL_PROMOTION = "illegal_promotion"
_FLAG_MISSING_MAPPING = "missing_vector_mapping"
_FLAG_COMPAT_BREAK = "backward_compatibility_break"
_FLAG_WEAK = "placeholder_or_weak_input"

_DEFAULT_PROMOTION_MIN_STRENGTH = 0.7

_IDENTIFYING_KEYS = (
    "id",
    "proposal_id",
    "proposalId",
    "vector_id",
    "vectorId",
    "vocab_id",
    "vocabId",
    "evidence_id",
    "evidenceId",
    "mapping_id",
    "mappingId",
)
_MAPPING_KEYS = (
    "id",
    "vector_id",
    "vectorId",
    "token",
    "term",
    "from",
    "to",
    "source",
    "target",
)
_VOCAB_COLLECTION_KEYS = ("terms", "vectors", "entries", "tokens", "items")
_EVIDENCE_PAYLOAD_KEYS = (
    "receipts",
    "receipt",
    "attestations",
    "attestation",
    "sources",
    "strength",
    "score",
    "weight",
)
_STRENGTH_KEYS = ("strength", "score", "weight")
_BREAKING_TRUE_KEYS = ("breaking", "compatibility_break", "compatibilityBreak")
_BREAKING_FALSE_KEYS = ("backward_compatible", "backwardCompatible")


class VectorProposalStub(BaseModel):
    """Placeholder VectorProposal. NOT_COMPUTABLE. Not an ontology write."""

    type_name: Literal["VectorProposal"] = "VectorProposal"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    proposal_id: str | None = None
    executable_ontology: None = None


class CanonicalVectorVocabularyStub(BaseModel):
    """Placeholder CanonicalVectorVocabulary. NOT_COMPUTABLE. Read-only echo."""

    type_name: Literal["CanonicalVectorVocabulary"] = "CanonicalVectorVocabulary"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    vocab_id: str | None = None
    mutated: Literal[False] = False


class PromotionEvidenceStub(BaseModel):
    """Placeholder PromotionEvidence. NOT_COMPUTABLE. Not a promotion grant."""

    type_name: Literal["PromotionEvidence"] = "PromotionEvidence"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    evidence_id: str | None = None


class VectorPromotionStub(BaseModel):
    """Placeholder VectorPromotion. NOT_COMPUTABLE. Not a live promotion."""

    type_name: Literal["VectorPromotion"] = "VectorPromotion"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    promotion_id: None = None
    activated: Literal[False] = False
    executable_ontology: None = None


class VectorDeprecationStub(BaseModel):
    """Placeholder VectorDeprecation. NOT_COMPUTABLE. Not a live deprecation."""

    type_name: Literal["VectorDeprecation"] = "VectorDeprecation"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    deprecation_id: None = None
    applied: Literal[False] = False


class VectorMappingStub(BaseModel):
    """Placeholder VectorMapping. NOT_COMPUTABLE. Not a live remapping."""

    type_name: Literal["VectorMapping"] = "VectorMapping"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    mapping_id: None = None
    applied: Literal[False] = False


class OntEvoProvenance(BaseModel):
    rune_id: str = RUNE_ID
    version: str = RUNE_VERSION
    run_id: str | None = None
    input_hash: str
    output_hash: str
    catalog_hash: str | None = None
    timestamp: str | None = None
    computation_path: list[str] = Field(default_factory=list)
    confidence: None = None


class OntEvoResult(BaseModel):
    rune_id: str = RUNE_ID
    lane: Literal["SHADOW"] = LANE
    influence_policy: Literal["NONE"] = INFLUENCE_POLICY
    category: Literal["CONTINUITY"] = CATEGORY
    vector_proposal: VectorProposalStub | None
    vector_promotion: VectorPromotionStub | None
    vector_deprecation: VectorDeprecationStub | None
    vector_mapping: VectorMappingStub | None
    vocabulary_mutated: Literal[False] = False
    auto_active_write: Literal[False] = False
    executable_ontology: None = None
    live_vocabulary: None = None
    not_computable_flags: list[str] = Field(default_factory=list)
    provenance: OntEvoProvenance


def evolve(
    vector_proposals: object,
    current_vocabulary: object,
    *,
    promotion_evidence: object = None,
    thresholds: object = None,
    seed: object = None,
    run_id: object = None,
    timestamp: object = None,
    catalog_hash: object = None,
    strict_execution: bool = False,
) -> OntEvoResult:
    """Accept proposals + vocabulary + optional evidence. Never promote live."""
    del strict_execution
    path = ["parse_inputs"]
    caller_ts = _optional_string(timestamp)
    vocab_copy = _shallow_mapping_copy(current_vocabulary)
    input_hash = _input_hash(
        vector_proposals,
        vocab_copy,
        promotion_evidence,
        thresholds,
        seed,
        run_id,
        caller_ts,
        catalog_hash,
    )

    proposals, proposals_ok, proposals_weak = _parse_proposal_list(vector_proposals)
    vocab, vocab_ok, vocab_weak = _parse_vocabulary(current_vocabulary)
    evidence, evidence_ok, evidence_weak, evidence_absent = _parse_evidence(
        promotion_evidence
    )
    parsed_thresholds, thresholds_ok = _parse_thresholds(thresholds)

    if not proposals_ok or not vocab_ok or not evidence_ok or not thresholds_ok:
        path.extend(["reject_schema", "not_computable"])
        return _null_result(
            flags=[
                _FLAG_NOT_COMPUTABLE,
                _FLAG_ILLEGAL_PROMOTION,
                _FLAG_WEAK,
            ],
            path=path,
            input_hash=input_hash,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
        )

    path.append("typed_stub")
    flags = [_FLAG_NOT_COMPUTABLE]

    if (
        evidence_absent
        or evidence_weak
        or evidence is None
        or not _evidence_meets_thresholds(promotion_evidence, parsed_thresholds)
    ):
        flags.append(_FLAG_ILLEGAL_PROMOTION)
        path.append("illegal_promotion")

    missing_mapping = _missing_vector_mapping(vector_proposals, current_vocabulary)
    if missing_mapping:
        flags.append(_FLAG_MISSING_MAPPING)
        path.append("missing_vector_mapping")

    compat_break = _backward_compatibility_break(vector_proposals)
    if compat_break:
        flags.append(_FLAG_COMPAT_BREAK)
        path.append("backward_compatibility_break")

    if (
        proposals_weak
        or vocab_weak
        or vocab is None
        or proposals is None
        or not proposals
    ):
        flags.append(_FLAG_WEAK)
        path.append("weak_or_placeholder")

    path.append("not_computable")

    emit_placeholders = (
        _FLAG_ILLEGAL_PROMOTION not in flags
        and not missing_mapping
        and not compat_break
        and vocab is not None
        and proposals
        and not proposals_weak
        and not vocab_weak
    )
    del proposals, vocab, evidence, vocab_copy
    if emit_placeholders:
        return _placeholder_result(
            flags=flags,
            path=path,
            input_hash=input_hash,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
        )
    return _null_result(
        flags=flags,
        path=path,
        input_hash=input_hash,
        run_id=run_id,
        catalog_hash=catalog_hash,
        timestamp=caller_ts,
    )


def apply_ont_evo(
    vectorProposals: object = None,
    currentVocabulary: object = None,
    promotionEvidence: object = None,
    thresholds: object = None,
    seed: object = None,
    run_id: object = None,
    timestamp: object = None,
    catalog_hash: object = None,
    *,
    vector_proposals: object = None,
    current_vocabulary: object = None,
    promotion_evidence: object = None,
    strict_execution: bool = False,
    **_extra: object,
) -> dict[str, object]:
    """Registry/invoke adapter. Returns a dict; evolve() is the typed API."""
    result = evolve(
        vectorProposals if vectorProposals is not None else vector_proposals,
        currentVocabulary if currentVocabulary is not None else current_vocabulary,
        promotion_evidence=(
            promotionEvidence if promotionEvidence is not None else promotion_evidence
        ),
        thresholds=thresholds,
        seed=seed,
        run_id=run_id,
        timestamp=timestamp,
        catalog_hash=catalog_hash,
        strict_execution=strict_execution,
    )
    return result.model_dump()


def mutates_live_vocabulary() -> bool:
    """Typed stub never mutates CanonicalVectorVocabulary."""
    return False


def writes_auto_active_ontology() -> bool:
    """Typed stub never Auto-Active ontology-writes."""
    return False


def invents_executable_ontology() -> bool:
    """Typed stub never invents executable ontology code."""
    return False


def _as_mapping(raw: object) -> Mapping[str, object] | None:
    if isinstance(raw, Mapping):
        return raw
    dumped = getattr(raw, "model_dump", None)
    if callable(dumped):
        payload = dumped()
        if isinstance(payload, Mapping):
            return payload
    return None


def _as_sequence(raw: object) -> list[object] | None:
    if raw is None or isinstance(raw, (str, bytes, bytearray)):
        return None
    if isinstance(raw, Sequence):
        return list(raw)
    return None


def _optional_string(raw: object) -> str | None:
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def _shallow_mapping_copy(raw: object) -> dict[str, object] | None:
    mapping = _as_mapping(raw)
    if mapping is None:
        return None
    return dict(mapping)


def _echo_id(mapping: Mapping[str, object]) -> str | None:
    for key in _IDENTIFYING_KEYS:
        value = mapping.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _is_placeholder_mapping(mapping: Mapping[str, object]) -> bool:
    status = mapping.get("status")
    if status in {_FLAG_NOT_COMPUTABLE, "not_computable"}:
        return True
    if mapping.get("placeholder") is True:
        return True
    if _echo_id(mapping) is None and not any(
        key not in {"type", "type_name", "status", "placeholder"} for key in mapping
    ):
        return True
    return False


def _parse_proposal_list(
    raw: object,
) -> tuple[list[VectorProposalStub] | None, bool, bool]:
    if raw is None:
        return None, True, True
    items = _as_sequence(raw)
    if items is None:
        return None, False, True
    parsed: list[VectorProposalStub] = []
    weak = not items
    for item in items:
        mapping = _as_mapping(item)
        if mapping is None:
            return None, False, True
        if _is_placeholder_mapping(mapping):
            weak = True
        parsed.append(VectorProposalStub(proposal_id=_echo_id(mapping)))
    return parsed, True, weak


def _parse_vocabulary(
    raw: object,
) -> tuple[CanonicalVectorVocabularyStub | None, bool, bool]:
    if raw is None:
        return None, True, True
    mapping = _as_mapping(raw)
    if mapping is None:
        return None, False, True
    return (
        CanonicalVectorVocabularyStub(vocab_id=_echo_id(mapping)),
        True,
        _is_placeholder_mapping(mapping),
    )


def _parse_evidence(
    raw: object,
) -> tuple[PromotionEvidenceStub | None, bool, bool, bool]:
    if raw is None:
        return None, True, True, True
    mapping = _as_mapping(raw)
    if mapping is None:
        return None, False, True, False
    weak = _is_placeholder_mapping(mapping) or not _has_evidence_payload(mapping)
    return PromotionEvidenceStub(evidence_id=_echo_id(mapping)), True, weak, False


def _has_evidence_payload(mapping: Mapping[str, object]) -> bool:
    if _echo_id(mapping) is None and not any(
        key in mapping for key in _EVIDENCE_PAYLOAD_KEYS
    ):
        return False
    for key in _EVIDENCE_PAYLOAD_KEYS:
        if key not in mapping:
            continue
        value = mapping[key]
        if value is None or value == "":
            continue
        items = _as_sequence(value)
        if items is not None:
            if items:
                return True
            continue
        return True
    return _echo_id(mapping) is not None and any(
        key in mapping for key in _EVIDENCE_PAYLOAD_KEYS
    )


def _parse_thresholds(raw: object) -> tuple[dict[str, float], bool]:
    defaults = {"promotion_min_strength": _DEFAULT_PROMOTION_MIN_STRENGTH}
    if raw is None:
        return defaults, True
    mapping = _as_mapping(raw)
    if mapping is None:
        return defaults, False
    strength, strength_ok = _parse_unit_interval(mapping.get("promotion_min_strength"))
    if not strength_ok:
        return defaults, False
    if strength is not None:
        defaults = {"promotion_min_strength": strength}
    return defaults, True


def _parse_unit_interval(raw: object) -> tuple[float | None, bool]:
    if raw is None:
        return None, True
    if isinstance(raw, bool):
        return None, False
    if isinstance(raw, (int, float)):
        value = float(raw)
        if value != value or value < 0.0 or value > 1.0:
            return None, False
        return value, True
    if isinstance(raw, str) and raw.strip():
        try:
            value = float(raw.strip())
        except ValueError:
            return None, False
        if value != value or value < 0.0 or value > 1.0:
            return None, False
        return value, True
    return None, False


def _evidence_strength(raw: object) -> float | None:
    mapping = _as_mapping(raw)
    if mapping is None:
        return None
    for key in _STRENGTH_KEYS:
        value, ok = _parse_unit_interval(mapping.get(key))
        if ok and value is not None:
            return value
    return None


def _evidence_meets_thresholds(
    raw_evidence: object, thresholds: Mapping[str, float]
) -> bool:
    minimum = thresholds.get("promotion_min_strength", _DEFAULT_PROMOTION_MIN_STRENGTH)
    strength = _evidence_strength(raw_evidence)
    if strength is not None:
        return strength >= minimum
    mapping = _as_mapping(raw_evidence)
    if mapping is None:
        return False
    return _has_evidence_payload(mapping) and minimum <= 0.0


def _item_has_mapping_key(mapping: Mapping[str, object]) -> bool:
    for key in _MAPPING_KEYS:
        value = mapping.get(key)
        if isinstance(value, str) and value.strip():
            return True
    return False


def _vocab_has_mapping_surface(mapping: Mapping[str, object]) -> bool:
    if _item_has_mapping_key(mapping):
        return True
    for key in _VOCAB_COLLECTION_KEYS:
        items = _as_sequence(mapping.get(key))
        if items:
            return True
    return False


def _missing_vector_mapping(proposals_raw: object, vocab_raw: object) -> bool:
    proposal_items = _as_sequence(proposals_raw)
    if not proposal_items:
        return True
    proposal_mappable = False
    for item in proposal_items:
        mapping = _as_mapping(item)
        if mapping is not None and _item_has_mapping_key(mapping):
            proposal_mappable = True
            break
    vocab_mapping = _as_mapping(vocab_raw)
    vocab_mappable = vocab_mapping is not None and _vocab_has_mapping_surface(
        vocab_mapping
    )
    return not proposal_mappable or not vocab_mappable


def _truthy_flag(value: object) -> bool:
    return value is True or value == "true" or value == 1


def _falsey_flag(value: object) -> bool:
    return value is False or value == "false" or value == 0


def _backward_compatibility_break(proposals_raw: object) -> bool:
    items = _as_sequence(proposals_raw)
    if items is None:
        return False
    for item in items:
        mapping = _as_mapping(item)
        if mapping is None:
            continue
        for key in _BREAKING_TRUE_KEYS:
            if _truthy_flag(mapping.get(key)):
                return True
        for key in _BREAKING_FALSE_KEYS:
            if key in mapping and _falsey_flag(mapping[key]):
                return True
    return False


def _canonical_events(raw: object) -> object:
    items = _as_sequence(raw)
    if items is None:
        return None
    out: list[object] = []
    for item in items:
        mapping = _as_mapping(item)
        out.append(dict(mapping) if mapping is not None else None)
    return out


def _canonical_mapping(raw: object) -> object:
    mapping = _as_mapping(raw)
    return dict(mapping) if mapping is not None else None


def _input_hash(
    vector_proposals: object,
    current_vocabulary: object,
    promotion_evidence: object,
    thresholds: object,
    seed: object,
    run_id: object,
    timestamp: str | None,
    catalog_hash: object,
) -> str:
    payload = {
        "catalog_hash": catalog_hash if isinstance(catalog_hash, str) else None,
        "current_vocabulary": _canonical_mapping(current_vocabulary),
        "promotion_evidence": _canonical_mapping(promotion_evidence),
        "run_id": run_id if isinstance(run_id, str) else None,
        "seed": seed if isinstance(seed, (int, str)) and not isinstance(seed, bool) else None,
        "thresholds": _canonical_mapping(thresholds),
        "timestamp": timestamp,
        "vector_proposals": _canonical_events(vector_proposals),
    }
    return sha256_hex(canonical_json(payload))


def _unique_flags(flags: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for flag in flags:
        if flag not in seen:
            seen.add(flag)
            out.append(flag)
    return out


def _body(
    proposal: VectorProposalStub | None,
    promotion: VectorPromotionStub | None,
    deprecation: VectorDeprecationStub | None,
    mapping: VectorMappingStub | None,
    flags: list[str],
) -> dict[str, object]:
    return {
        "auto_active_write": False,
        "executable_ontology": None,
        "live_vocabulary": None,
        "not_computable_flags": flags,
        "vector_deprecation": None if deprecation is None else deprecation.model_dump(),
        "vector_mapping": None if mapping is None else mapping.model_dump(),
        "vector_promotion": None if promotion is None else promotion.model_dump(),
        "vector_proposal": None if proposal is None else proposal.model_dump(),
        "vocabulary_mutated": False,
    }


def _finalize(
    *,
    proposal: VectorProposalStub | None,
    promotion: VectorPromotionStub | None,
    deprecation: VectorDeprecationStub | None,
    mapping: VectorMappingStub | None,
    flags: list[str],
    path: list[str],
    input_hash: str,
    run_id: object,
    catalog_hash: object,
    timestamp: str | None,
) -> OntEvoResult:
    unique = _unique_flags(flags)
    provenance = OntEvoProvenance(
        run_id=run_id if isinstance(run_id, str) else None,
        input_hash=input_hash,
        output_hash=sha256_hex(
            canonical_json(_body(proposal, promotion, deprecation, mapping, unique))
        ),
        catalog_hash=catalog_hash if isinstance(catalog_hash, str) else None,
        timestamp=timestamp,
        computation_path=list(path),
    )
    return OntEvoResult(
        vector_proposal=proposal,
        vector_promotion=promotion,
        vector_deprecation=deprecation,
        vector_mapping=mapping,
        vocabulary_mutated=False,
        auto_active_write=False,
        executable_ontology=None,
        live_vocabulary=None,
        not_computable_flags=unique,
        provenance=provenance,
    )


def _null_result(
    *,
    flags: list[str],
    path: list[str],
    input_hash: str,
    run_id: object,
    catalog_hash: object,
    timestamp: str | None,
) -> OntEvoResult:
    return _finalize(
        proposal=None,
        promotion=None,
        deprecation=None,
        mapping=None,
        flags=flags,
        path=path,
        input_hash=input_hash,
        run_id=run_id,
        catalog_hash=catalog_hash,
        timestamp=timestamp,
    )


def _placeholder_result(
    *,
    flags: list[str],
    path: list[str],
    input_hash: str,
    run_id: object,
    catalog_hash: object,
    timestamp: str | None,
) -> OntEvoResult:
    return _finalize(
        proposal=VectorProposalStub(),
        promotion=VectorPromotionStub(),
        deprecation=VectorDeprecationStub(),
        mapping=VectorMappingStub(),
        flags=flags,
        path=path,
        input_hash=input_hash,
        run_id=run_id,
        catalog_hash=catalog_hash,
        timestamp=timestamp,
    )
