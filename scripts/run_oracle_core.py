from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from typing import Any

from abraxas.semantic.contracts import ContractLoadError, canonical_hash, load_contract


def _load_input(path: Path) -> tuple[list[dict[str, Any]], str | None]:
    try:
        data = load_contract(path, "OracleInput.v1")
    except ContractLoadError as exc:
        return [], exc.reason
    rows = data.get("signals", [])
    return [r for r in rows if isinstance(r, dict)], None


def _classify_lane(rows: list[dict[str, Any]]) -> str:
    allowed = {"SHADOW", "FORECAST", "OBSERVATION"}
    lanes = {str(r.get("lane", "")).upper() for r in rows if str(r.get("lane", "")).upper() in allowed}
    if not lanes:
        return "NOT_COMPUTABLE"
    if "FORECAST" in lanes:
        return "FORECAST"
    if "SHADOW" in lanes:
        return "SHADOW"
    return "OBSERVATION"


def main() -> None:
    rows, contract_reason = _load_input(Path("out/oracle/oracle_input.latest.json"))
    lane = _classify_lane(rows)
    structural_keys = sorted({k for row in rows for k in row.keys()})
    source_ids = {str(row.get("source_id")) for row in rows if row.get("source_id") is not None}
    status = "COMPUTABLE" if rows else "NOT_COMPUTABLE"

    payload: dict[str, Any] = {
        "schema_version": "OracleSignalPacket.v1",
        "status": status,
        "reason": None if rows else contract_reason,
        "lane": lane,
        "source_count": len(source_ids),
        "signal_count": len(rows),
        "structural_keys": structural_keys,
        "signals": rows,
        "authority": {"mutation": False, "promotion": False, "execution": False, "observe_only": True, "forecast_authority": False},
    }
    payload["packet_hash"] = canonical_hash(payload)
    out_path = Path("out/oracle/oracle_signal_packet.latest.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
