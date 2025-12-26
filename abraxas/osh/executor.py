from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Tuple, Optional

from .ledger import append_chained_jsonl
from .normalize import normalize_artifact_to_ingest_packet
from .registry_loaders import build_allowlist_url_map, load_vector_map
from .transport import fetch_with_fallback, TransportMode
from .types import OSHFetchJob, RawFetchArtifact


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def compile_jobs_from_dap(
    dap_json_path: str,
    run_id: str,
    allowlist_spec_path: Optional[str] = None,
    allowlist_map_fallback_path: Optional[str] = None,
    vector_map_path: Optional[str] = None,
    max_actions_per_run: int = 10,
) -> List[OSHFetchJob]:
    with open(dap_json_path, "r", encoding="utf-8") as f:
        dap = json.load(f)

    actions = [a for a in dap.get("actions", []) if a.get("kind") == "ONLINE_FETCH"]
    actions = actions[:max_actions_per_run]

    allowlist_url_map, _ = build_allowlist_url_map(
        allowlist_spec_path, allowlist_map_fallback_path
    )
    vector_map = None
    if vector_map_path:
        try:
            vector_map = load_vector_map(vector_map_path)
        except Exception:
            vector_map = None

    jobs: List[OSHFetchJob] = []
    for action in actions:
        selector = action.get("selector", {}) or {}
        vector_node_ids = selector.get("vector_node_ids", []) or []
        allowlist_source_ids: List[str] = []
        if vector_node_ids:
            if vector_map:
                for node_id in vector_node_ids:
                    allowlist_source_ids.extend(
                        vector_map.node_to_sources.get(node_id, [])
                    )
            else:
                allowlist_source_ids.extend(vector_node_ids)

        allowlist_source_ids.extend(selector.get("allowlist_source_ids", []) or [])
        seen: set[str] = set()
        deduped_source_ids: List[str] = []
        for source_id in allowlist_source_ids:
            source_id = str(source_id)
            if source_id in seen:
                continue
            seen.add(source_id)
            deduped_source_ids.append(source_id)

        for source_id in deduped_source_ids:
            url = allowlist_url_map.get(source_id)
            if not url:
                continue
            job_id = _sha(f"{run_id}:{action.get('action_id')}:{source_id}:{url}")[:16]
            jobs.append(
                OSHFetchJob(
                    job_id=job_id,
                    run_id=run_id,
                    action_id=action.get("action_id"),
                    url=url,
                    method="POST",
                    params={},
                    source_label=str(source_id),
                    vector_node_id=(vector_node_ids[0] if vector_node_ids else None),
                    allowlist_source_id=str(source_id),
                    budget={"max_requests": 3, "max_bytes": 5_000_000, "timeout_s": 60},
                    provenance={
                        "dap_plan_id": dap.get("plan_id"),
                        "dap_action_id": action.get("action_id"),
                    },
                )
            )

    jobs.sort(key=lambda job: (job.vector_node_id or "", job.allowlist_source_id or "", job.url))
    return jobs


def run_osh_jobs(
    jobs: List[OSHFetchJob],
    out_dir: str,
) -> Tuple[List[RawFetchArtifact], List[Dict[str, Any]]]:
    out_raw_dir = os.path.join(out_dir, "osh", "raw")
    out_queue_dir = os.path.join(out_dir, "osh", "ingest_queue")
    os.makedirs(out_queue_dir, exist_ok=True)

    jobs_ledger = os.path.join(out_dir, "osh_ledgers", "fetch_jobs.jsonl")
    artifacts_ledger = os.path.join(out_dir, "osh_ledgers", "fetch_artifacts.jsonl")
    offline_dir = os.path.join(out_dir, "osh", "offline_requests")
    os.makedirs(offline_dir, exist_ok=True)

    artifacts: List[RawFetchArtifact] = []
    packets: List[Dict[str, Any]] = []

    for job in jobs:
        append_chained_jsonl(jobs_ledger, {"run_id": job.run_id, "job": job.to_dict()})
        artifact, mode, note = fetch_with_fallback(job, out_raw_dir=out_raw_dir)
        if artifact is None:
            stub = {
                "run_id": job.run_id,
                "job_id": job.job_id,
                "action_id": job.action_id,
                "url": job.url,
                "source_label": job.source_label,
                "vector_node_id": job.vector_node_id,
                "allowlist_source_id": job.allowlist_source_id,
                "transport_mode": mode.value,
                "reason": note,
                "suggested_user_action": (
                    "Acquire this content manually (download/export), then upload as an evidence_pack. "
                    "If paywalled, paste a redacted summary + key quotes with dates."
                ),
            }
            offline_path = os.path.join(offline_dir, f"{job.run_id}.json")
            existing: List[Dict[str, Any]] = []
            if os.path.exists(offline_path):
                with open(offline_path, "r", encoding="utf-8") as f:
                    try:
                        existing = json.load(f) or []
                    except Exception:
                        existing = []
            existing.append(stub)
            with open(offline_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2, sort_keys=True)

            append_chained_jsonl(
                artifacts_ledger,
                {
                    "run_id": job.run_id,
                    "status": "offline_required",
                    "transport_mode": mode.value,
                    "job_id": job.job_id,
                    "note": note,
                },
            )
            continue

        artifacts.append(artifact)
        append_chained_jsonl(
            artifacts_ledger,
            {
                "run_id": job.run_id,
                "status": "ok",
                "transport_mode": mode.value,
                "note": note,
                "artifact": artifact.to_dict(),
            },
        )
        packet = normalize_artifact_to_ingest_packet(artifact)
        packets.append(packet)

    queue_path = os.path.join(out_queue_dir, f"{jobs[0].run_id if jobs else 'run'}.json")
    with open(queue_path, "w", encoding="utf-8") as f:
        json.dump(packets, f, ensure_ascii=False, indent=2)

    return artifacts, packets
