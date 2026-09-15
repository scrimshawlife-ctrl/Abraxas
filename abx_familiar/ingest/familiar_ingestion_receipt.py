"""FamiliarIngestionReceipt.v0 from local EvidencePack IR.

Adapter, not a copy of Abraxas-v2.0 core.ingest.
Local pack has items[] and no claim registers. Claim counts stay 0.
Does not network, promote, or grant execution authority.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from abx_familiar.ingest.pack_io import load_evidence_pack
from abx_familiar.ir.evidence_pack_v0 import EvidencePack

SCHEMA_VERSION = "FamiliarIngestionReceipt.v0"
PIPELINE_ID = "familiar_ingestion"
DETERMINISTIC_TIMESTAMP = "familiar_ingestion_receipt_v0_ts_0"
DEFAULT_AUTHORITY = {
    "execution_authority": False,
    "promotion_authorized": False,
    "forecast_routing_authorized": False,
    "canon_mutation_allowed": False,
}
PRODUCER = {
    "module": "abx_familiar.ingest.familiar_ingestion_receipt",
    "skill_id": "abx-familiar-signal-forager",
    "source_contract": "Abraxas-v2.0 contracts/ingest/familiar_ingestion_receipt.v0.schema.json",
}


def _stable_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _canonical_hash(data: dict[str, Any]) -> str:
    return hashlib.sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _finalize(body: dict[str, Any]) -> dict[str, Any]:
    sealed = dict(body)
    sealed.pop("receipt_hash", None)
    sealed["receipt_hash"] = _canonical_hash(sealed)
    return sealed


def _empty_counts() -> dict[str, int]:
    return {
        "OBSERVED": 0,
        "INFERRED": 0,
        "SPECULATIVE": 0,
        "NOT_COMPUTABLE": 0,
    }


def _source_summaries(pack: EvidencePack) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in pack.items:
        locator = item.url or item.path or item.source_id or ""
        out.append(
            {
                "source_id": item.evidence_id,
                "source_class": item.source_type,
                "url_or_path": str(locator),
                "title": str((item.meta or {}).get("title", "")),
            }
        )
    out.sort(key=lambda s: s["source_id"])
    return out


def _base(
    *,
    receipt_id: str,
    pack_id: str,
    pack_hash: str,
    pack_ref: str,
    status: str,
    validation_status: str,
    blockers: list[str],
    validation_errors: list[str],
    source_count: int = 0,
    not_computable_count: int = 0,
    summaries: list[dict[str, Any]] | None = None,
    topic: str = "",
    intent: str = "",
) -> dict[str, Any]:
    counts = _empty_counts()
    counts["NOT_COMPUTABLE"] = not_computable_count
    return _finalize(
        {
            "schema_version": SCHEMA_VERSION,
            "receipt_id": receipt_id,
            "pipeline_id": PIPELINE_ID,
            "pack_id": pack_id,
            "pack_hash": pack_hash,
            "pack_ref": pack_ref,
            "topic": topic,
            "intent": intent,
            "register_counts": counts,
            "source_count": source_count,
            "claim_count": 0,
            "observed_claim_count": 0,
            "validation_status": validation_status,
            "status": status,
            "blockers": blockers,
            "validation_errors": validation_errors,
            "commercial_claims_blocked": True,
            "evidence_density": 0.1 if source_count == 0 else min(1.0, source_count / 10.0),
            "authority": dict(DEFAULT_AUTHORITY),
            "advisory_only": True,
            "lane": "SHADOW",
            "deterministic_timestamp": DETERMINISTIC_TIMESTAMP,
            "source_summaries": summaries or [],
            "producer": dict(PRODUCER),
        }
    )


def build_familiar_ingestion_receipt(
    pack: EvidencePack | None,
    *,
    pack_ref: str = "",
    load_error: str | None = None,
) -> dict[str, Any]:
    if pack is None and load_error:
        return _base(
            receipt_id="fir_load_failed",
            pack_id="missing",
            pack_hash=_canonical_hash({"load_error": load_error}),
            pack_ref=pack_ref or "",
            status="REJECTED_INVALID_PACK",
            validation_status="FAIL",
            blockers=["pack_load_failed"],
            validation_errors=[load_error],
        )
    if pack is None:
        return _base(
            receipt_id="fir_no_input",
            pack_id="missing",
            pack_hash=_canonical_hash({"empty": True}),
            pack_ref=pack_ref or "",
            status="NO_INPUT",
            validation_status="NOT_COMPUTABLE",
            blockers=["no_input"],
            validation_errors=[],
        )
    try:
        pack.validate()
        pack_hash = pack.hash()
    except ValueError as exc:
        return _base(
            receipt_id="fir_invalid_pack",
            pack_id=str(getattr(pack, "pack_id", "") or "invalid"),
            pack_hash=_canonical_hash({"invalid": str(exc)}),
            pack_ref=pack_ref,
            status="REJECTED_INVALID_PACK",
            validation_status="FAIL",
            blockers=["invalid_evidence_pack"],
            validation_errors=[str(exc)],
        )

    nc = sum(1 for item in pack.items if item.not_computable)
    if pack.not_computable:
        nc += 1
    ctx = pack.collection_context or {}
    return _base(
        receipt_id=f"fir_{pack_hash[:16]}",
        pack_id=str(pack.pack_id),
        pack_hash=pack_hash,
        pack_ref=pack_ref,
        status="INGESTED_SHADOW",
        validation_status="PASS",
        blockers=[],
        validation_errors=[],
        source_count=len(pack.items),
        not_computable_count=nc,
        summaries=_source_summaries(pack),
        topic=str(ctx.get("topic", "")),
        intent=str(ctx.get("intent", "")),
    )


def build_familiar_ingestion_receipt_from_path(path: str | Path) -> dict[str, Any]:
    p = Path(path).expanduser()
    try:
        pack = load_evidence_pack(p)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        return build_familiar_ingestion_receipt(None, pack_ref=str(p), load_error=str(exc))
    return build_familiar_ingestion_receipt(pack, pack_ref=str(p))


def build_familiar_ingestion_receipt_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# Familiar Ingestion Receipt",
        "",
        f"- receipt_id: `{packet.get('receipt_id')}`",
        f"- status: `{packet.get('status')}`",
        f"- validation_status: `{packet.get('validation_status')}`",
        f"- pack_id: `{packet.get('pack_id')}`",
        f"- pack_hash: `{packet.get('pack_hash')}`",
        f"- source_count: `{packet.get('source_count')}`",
        f"- claim_count: `{packet.get('claim_count')}` (local IR has no claims)",
        f"- lane: `{packet.get('lane')}`",
        f"- receipt_hash: `{packet.get('receipt_hash')}`",
        "",
        "Authority: execution/promotion/forecast/canon all **false** (SHADOW).",
        "",
    ]
    return "\n".join(lines)


def write_familiar_ingestion_receipt(path: Path, packet: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.with_suffix(".md").write_text(
        build_familiar_ingestion_receipt_markdown(packet), encoding="utf-8"
    )
