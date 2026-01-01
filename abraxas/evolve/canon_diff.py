from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def _latest_canon_snapshot(canon_dir: str = "out/canon_snapshots") -> Optional[str]:
    if not os.path.exists(canon_dir):
        return None
    files = [f for f in os.listdir(canon_dir) if f.endswith(".json")]
    if not files:
        return None
    files.sort()
    return os.path.join(canon_dir, files[-1])


def _intents(policy: Dict[str, Any]) -> Dict[str, Any]:
    overlay = policy.get("overlay", {}) or {}
    if not isinstance(overlay, dict):
        return {}
    intents = overlay.get("intents", {}) or {}
    return intents if isinstance(intents, dict) else {}


def _kind_counts(intents: Dict[str, Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for _, value in intents.items():
        if not isinstance(value, dict):
            continue
        kind = str(value.get("kind") or "unknown")
        counts[kind] = counts.get(kind, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (kv[0], kv[1])))


@dataclass(frozen=True)
class CanonDiffSummary:
    run_id: str
    canon_path: Optional[str]
    candidate_path: str
    added: List[str]
    removed: List[str]
    changed: List[str]
    canon_kind_counts: Dict[str, int]
    candidate_kind_counts: Dict[str, int]
    replay_deltas: Dict[str, Any]
    rim_items: Optional[int]
    notes: List[str]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_canon_diff(
    *,
    run_id: str,
    out_reports_dir: str,
    candidate_policy_path: str,
    epp_path: Optional[str] = None,
    evogate_path: Optional[str] = None,
    rim_manifest_path: Optional[str] = None,
    canon_snapshot_path: Optional[str] = None,
) -> Tuple[str, str, Dict[str, Any]]:
    notes: List[str] = []
    canon_path = canon_snapshot_path or _latest_canon_snapshot()
    if not canon_path:
        notes.append("no_canon_snapshot_found")

    candidate = _read_json(candidate_policy_path)
    cand_intents = _intents(candidate)

    canon = _read_json(canon_path) if canon_path else {}
    canon_intents = _intents(canon) if canon else {}

    canon_keys = set(canon_intents.keys())
    cand_keys = set(cand_intents.keys())

    added = sorted(list(cand_keys - canon_keys))
    removed = sorted(list(canon_keys - cand_keys))
    changed: List[str] = []
    for key in sorted(list(canon_keys & cand_keys)):
        if canon_intents.get(key) != cand_intents.get(key):
            changed.append(key)

    replay_deltas: Dict[str, Any] = {}
    if evogate_path and os.path.exists(evogate_path):
        evog = _read_json(evogate_path)
        replay_deltas = (evog.get("replay", {}) or {}).get("metric_deltas", {}) or {}
    else:
        notes.append("missing_evogate")

    rim_items = None
    if rim_manifest_path and os.path.exists(rim_manifest_path):
        rim = _read_json(rim_manifest_path)
        rim_items = (rim.get("totals", {}) or {}).get("items")
    else:
        notes.append("missing_rim")

    summary = CanonDiffSummary(
        run_id=run_id,
        canon_path=canon_path,
        candidate_path=candidate_policy_path,
        added=added,
        removed=removed,
        changed=changed,
        canon_kind_counts=_kind_counts(canon_intents),
        candidate_kind_counts=_kind_counts(cand_intents),
        replay_deltas=replay_deltas,
        rim_items=int(rim_items) if isinstance(rim_items, int) else None,
        notes=notes,
        provenance={
            "builder": "canon_diff.v0.1",
            "inputs": {
                "epp": epp_path,
                "evogate": evogate_path,
                "rim": rim_manifest_path,
                "canon": canon_path,
                "candidate": candidate_policy_path,
            },
        },
    )

    os.makedirs(out_reports_dir, exist_ok=True)
    json_path = os.path.join(out_reports_dir, f"canon_diff_{run_id}.json")
    md_path = os.path.join(out_reports_dir, f"canon_diff_{run_id}.md")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary.to_dict(), f, ensure_ascii=False, indent=2, sort_keys=True)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Canon Diff v0.1\n\n")
        f.write(f"- run_id: `{run_id}`\n")
        f.write(f"- canon: `{canon_path}`\n")
        f.write(f"- candidate: `{candidate_policy_path}`\n\n")

        f.write("## Overlay intent changes\n")
        f.write(
            f"- added: **{len(added)}**\n- removed: **{len(removed)}**\n"
            f"- changed: **{len(changed)}**\n\n"
        )

        if added:
            f.write("### Added intents\n")
            for key in added:
                value = cand_intents.get(key)
                kind = value.get("kind") if isinstance(value, dict) else None
                target = value.get("target") if isinstance(value, dict) else None
                f.write(f"- `{key}` kind={kind} target={target}\n")
            f.write("\n")

        if removed:
            f.write("### Removed intents\n")
            for key in removed:
                value = canon_intents.get(key)
                kind = value.get("kind") if isinstance(value, dict) else None
                target = value.get("target") if isinstance(value, dict) else None
                f.write(f"- `{key}` kind={kind} target={target}\n")
            f.write("\n")

        if changed:
            f.write("### Changed intents\n")
            for key in changed:
                f.write(f"- `{key}`\n")
            f.write("\n")

        f.write("## Kind counts\n")
        f.write("### Canon\n")
        f.write(json.dumps(summary.canon_kind_counts, ensure_ascii=False, indent=2))
        f.write("\n\n### Candidate\n")
        f.write(json.dumps(summary.candidate_kind_counts, ensure_ascii=False, indent=2))
        f.write("\n\n")

        f.write("## Replay deltas\n")
        f.write(json.dumps(replay_deltas, ensure_ascii=False, indent=2))
        f.write("\n\n")

        f.write("## Evidence slice\n")
        f.write(f"- RIM items: `{summary.rim_items}`\n\n")

        if notes:
            f.write("## Notes\n")
            for note in notes:
                f.write(f"- {note}\n")

    meta = {"added": len(added), "removed": len(removed), "changed": len(changed)}
    return json_path, md_path, meta
