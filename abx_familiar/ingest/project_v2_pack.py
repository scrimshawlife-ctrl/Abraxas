"""Project EvidencePack.v0 (sources+claims) onto execution local IR (items[]).

SHADOW adapter. Does not copy Abraxas-v2.0 core.ingest.
Does not grant authority. Receipt claim_count stays 0 on the local builder.
"""

from __future__ import annotations

from typing import Any

from abx_familiar.ir.evidence_pack_v0 import EvidenceItem, EvidencePack

SOURCE_CLASS_TO_TYPE = {
    "primary": "web",
    "secondary": "web",
    "social": "web",
    "market": "web",
    "code": "file",
    "session": "file",
}


def _source_item(src: dict[str, Any]) -> EvidenceItem:
    sid = str(src.get("source_id") or "")
    locator = str(src.get("url_or_path") or "")
    source_class = str(src.get("source_class") or "primary")
    source_type = SOURCE_CLASS_TO_TYPE.get(source_class, "web")
    url = locator if locator.startswith("http") else None
    path = None if url else (locator or None)
    if source_type == "file" and url:
        # GitHub blob URLs are locators; keep them on url, type file is metadata only.
        source_type = "web"
    return EvidenceItem(
        evidence_id=f"src_{sid}",
        source_type=source_type if (url or path) else "none",
        url=url,
        path=path,
        source_id=sid or None,
        timestamp=None,
        provenance_hash=None,
        confidence_class="unknown",
        meta={
            "kind": "source",
            "title": src.get("title"),
            "publisher": src.get("publisher"),
            "source_class": source_class,
            "excerpt": src.get("excerpt"),
        },
        not_computable=False,
        missing_fields=[],
    )


def _claim_item(claim: dict[str, Any]) -> EvidenceItem:
    cid = str(claim.get("claim_id") or "")
    register = str(claim.get("register") or "").upper()
    nc = register == "NOT_COMPUTABLE"
    return EvidenceItem(
        evidence_id=f"claim_{cid}",
        source_type="none" if nc else "file",
        url=None,
        path=None if nc else f"claim:{cid}",
        source_id=None if nc else cid,
        timestamp=None,
        provenance_hash=None,
        confidence_class="unknown",
        meta={
            "kind": "claim_projection",
            "claim_id": cid,
            "register": register,
            "text": claim.get("text"),
            "source_ids": claim.get("source_ids") or [],
            "supports_questions": claim.get("supports_questions") or [],
        },
        not_computable=nc,
        missing_fields=["local_ir_has_no_claim_register"] if nc else [],
    )


def project_v2_pack_dict(pack: dict[str, Any]) -> tuple[EvidencePack, dict[str, Any]]:
    """Return local EvidencePack plus FamiliarClaimProjection.v0 sidecar."""
    if pack.get("schema_version") != "EvidencePack.v0":
        raise ValueError("expected schema_version EvidencePack.v0")
    pack_id = str(pack.get("pack_id") or "")
    if not pack_id:
        raise ValueError("pack_id required")

    items: list[EvidenceItem] = []
    for src in pack.get("sources") or []:
        if isinstance(src, dict) and src.get("source_id"):
            items.append(_source_item(src))
    projection: list[dict[str, Any]] = []
    for claim in pack.get("claims") or []:
        if not isinstance(claim, dict) or not claim.get("claim_id"):
            continue
        items.append(_claim_item(claim))
        projection.append(
            {
                "claim_id": claim.get("claim_id"),
                "register": str(claim.get("register") or "").upper(),
                "text": claim.get("text"),
                "source_ids": claim.get("source_ids") or [],
                "truth_assignment": False,
            }
        )

    local = EvidencePack(
        pack_id=pack_id,
        items=items,
        collection_context={
            "topic": pack.get("topic"),
            "intent": pack.get("intent"),
            "must_answer": pack.get("must_answer") or [],
            "projected_from": "EvidencePack.v0",
            "authority": pack.get("authority") or {},
        },
        not_computable=False,
        missing_fields=[],
    )
    local.validate()
    sidecar = {
        "schema_version": "FamiliarClaimProjection.v0",
        "pack_id": pack_id,
        "lane": "SHADOW",
        "advisory_only": True,
        "claim_count": len(projection),
        "claims": projection,
        "authority": {
            "execution_authority": False,
            "promotion_authorized": False,
            "forecast_routing_authorized": False,
            "canon_mutation_allowed": False,
        },
        "note": "Sidecar only. FamiliarIngestionReceipt.v0 keeps claim_count 0.",
    }
    return local, sidecar


def should_project_v2_pack(raw: dict[str, Any]) -> bool:
    items = raw.get("items")
    sources = raw.get("sources")
    return (
        raw.get("schema_version") == "EvidencePack.v0"
        and (not isinstance(items, list) or len(items) == 0)
        and isinstance(sources, list)
        and len(sources) > 0
    )
