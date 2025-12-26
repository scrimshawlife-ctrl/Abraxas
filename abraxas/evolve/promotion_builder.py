from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple


def _utc_today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)


def build_promotion_packet(
    *,
    run_id: str,
    out_dir: str,
    epp_path: str,
    evogate_path: str,
    rim_manifest_path: str,
    candidate_policy_path: str,
    emit_canon_snapshot: bool = False,
    force: bool = False,
) -> Tuple[str, str, Optional[str], Dict[str, Any]]:
    epp = _read_json(epp_path)
    evogate = _read_json(evogate_path)
    rim = _read_json(rim_manifest_path)
    candidate = _read_json(candidate_policy_path)

    promote_rec = bool(evogate.get("promote_recommended", False))
    if emit_canon_snapshot and (not promote_rec) and (not force):
        emit_canon_snapshot = False

    pack_id = str(epp.get("pack_id") or evogate.get("pack_id") or "unknown_pack")
    replay = evogate.get("replay", {}) or {}
    deltas = replay.get("metric_deltas", {}) or {}

    packet = {
        "version": "promotion_packet.v0.1",
        "run_id": run_id,
        "pack_id": pack_id,
        "inputs": {
            "epp": epp_path,
            "evogate": evogate_path,
            "rim_manifest": rim_manifest_path,
            "candidate_policy": candidate_policy_path,
        },
        "promotion_recommended": promote_rec,
        "replay": {
            "method": replay.get("provenance", {}).get("method"),
            "metric_deltas": deltas,
            "notes": replay.get("notes", []),
            "thresholds": evogate.get("thresholds", {}),
        },
        "evidence_slice": {
            "rim_version": rim.get("version"),
            "items": rim.get("totals", {}).get("items"),
        },
        "applied_proposals": evogate.get("applied_proposal_ids", []),
        "candidate_policy_overlay": candidate.get("overlay", {}),
        "notes": [],
        "provenance": {
            "builder": "promotion_builder.v0.1",
            "ts": evogate.get("ts"),
        },
    }

    out_run_dir = os.path.join(out_dir, run_id)
    json_path = os.path.join(out_run_dir, "promotion_packet.json")
    md_path = os.path.join(out_run_dir, "promotion_packet.md")
    _write_json(json_path, packet)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Promotion Packet v0.1\n\n")
        f.write(f"- run_id: `{run_id}`\n- pack_id: `{pack_id}`\n")
        f.write(f"- promotion_recommended: **{promote_rec}**\n\n")
        f.write("## Replay deltas\n")
        f.write(json.dumps(deltas, ensure_ascii=False, indent=2))
        f.write("\n\n## Evidence slice (RIM)\n")
        f.write(f"- manifest: `{rim_manifest_path}`\n")
        f.write(f"- items: `{rim.get('totals', {}).get('items')}`\n\n")
        f.write("## Applied proposals\n")
        for proposal_id in (evogate.get("applied_proposal_ids", []) or []):
            f.write(f"- `{proposal_id}`\n")
        f.write("\n## Candidate overlay intents\n")
        intents = (candidate.get("overlay", {}) or {}).get("intents", {})
        if isinstance(intents, dict) and intents:
            for key, value in intents.items():
                f.write(f"- `{key}`: {value.get('kind')} target={value.get('target')}\n")
        else:
            f.write("- (none)\n")

    canon_snapshot_path = None
    if emit_canon_snapshot:
        date = _utc_today()
        canon_snapshot_path = os.path.join(
            "out", "canon_snapshots", f"{date}_{run_id}_{pack_id}.json"
        )
        _write_json(canon_snapshot_path, candidate)

    meta = {
        "promotion_recommended": promote_rec,
        "emit_canon_snapshot": bool(canon_snapshot_path),
    }
    return json_path, md_path, canon_snapshot_path, meta
