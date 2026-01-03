"""ABX-PROFILE_INGEST rune operator."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from abraxas.core.canonical import canonical_json
from abraxas.profile.schema import ProfilePack


def apply_profile_ingest(
    *,
    profile_pack: Dict[str, Any],
    strict_execution: bool = True,
) -> Dict[str, Any]:
    pack = ProfilePack(**profile_pack)
    ledger_path = Path("out/profile_ledgers/profile_ingest.jsonl")
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "profile_hash": pack.profile_hash(),
        "profile": pack.model_dump(),
    }
    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(canonical_json(payload) + "\n")
    return {"ingested": True, "ledger_path": str(ledger_path), "profile_hash": pack.profile_hash()}
