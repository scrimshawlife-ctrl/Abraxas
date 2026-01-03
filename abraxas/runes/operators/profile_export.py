"""ABX-PROFILE_EXPORT rune operator."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from abraxas.core.canonical import canonical_json
from abraxas.profile.schema import ProfilePack
from abraxas.storage.cas import CASStore


def apply_profile_export(
    *,
    profile_pack: Dict[str, Any],
    out_path: str,
    strict_execution: bool = True,
) -> Dict[str, Any]:
    pack = ProfilePack(**profile_pack)
    cas_store = CASStore()
    ref = cas_store.store_json(pack.model_dump(), subdir="profiles", suffix=".json")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(canonical_json(pack.model_dump()), encoding="utf-8")
    return {"cas_ref": ref.to_dict(), "out_path": out_path, "profile_hash": pack.profile_hash()}
