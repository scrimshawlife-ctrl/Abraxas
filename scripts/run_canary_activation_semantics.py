from __future__ import annotations
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from typing import Any

from abraxas.semantic.contracts import ContractLoadError, canonical_hash, load_contract


def _load(path: Path) -> tuple[list[dict[str, Any]], str | None]:
    try:
        data = load_contract(path, "CanaryCandidateSet.v1")
    except ContractLoadError as exc:
        return [], exc.reason
    return [r for r in data["candidates"] if isinstance(r, dict)], None


def main() -> None:
    rows, reason = _load(Path("out/canary/canary_candidate_set.latest.json"))
    entries = []
    for row in rows:
        required = all(k in row for k in ("id", "target", "approval", "safety", "rollback_ready"))
        entries.append({"id": row.get("id"), "target": row.get("target"), "approval": row.get("approval"), "safety": row.get("safety"), "rollback_ready": row.get("rollback_ready"), "status": "READY_FOR_OPERATOR_REVIEW" if required else "NOT_COMPUTABLE"})

    payload: dict[str, Any] = {"schema_version": "CanaryActivationPacket.v1", "status": "COMPUTABLE" if entries else "NOT_COMPUTABLE", "reason": None if entries else reason, "entries": entries, "authority": {"mutation": False, "promotion": False, "execution": False, "packet_only": True, "review_only": True}}
    payload["packet_hash"] = canonical_hash(payload)
    out = Path("out/canary/canary_activation_packet.latest.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
