from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from typing import Any, Dict

try:
    import requests
except ImportError:  # pragma: no cover - optional dependency
    requests = None

from .types import OSHFetchJob, RawFetchArtifact


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def decodo_fetch(job: OSHFetchJob, out_raw_dir: str) -> RawFetchArtifact:
    """
    Transport layer: Decodo Web Scraping API.
    v0.1 uses a simple HTTP call pattern and stores raw bytes.
    """
    api_key = os.getenv("DECODO_API_KEY")
    if not api_key:
        raise RuntimeError("DECODO_API_KEY is not set.")

    endpoint = os.getenv("DECODO_SCRAPE_ENDPOINT", "https://api.decodo.com/scrape")
    timeout_s = int(os.getenv("DECODO_TIMEOUT_S", "60"))
    max_retries = int(os.getenv("DECODO_MAX_RETRIES", "2"))

    payload: Dict[str, Any] = {
        "url": job.url,
        **(job.params or {}),
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_exc: Exception | None = None
    status_code: int | None = None
    response_headers: dict[str, str] = {}
    body = b""
    for _ in range(max_retries + 1):
        try:
            if requests is not None:
                resp = requests.post(endpoint, json=payload, headers=headers, timeout=timeout_s)
                status_code = int(resp.status_code)
                response_headers = dict(resp.headers)
                body = resp.content or b""
            else:
                import json
                from urllib.request import Request, urlopen

                req = Request(
                    endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urlopen(req, timeout=timeout_s) as resp:
                    status_code = int(getattr(resp, "status", 200))
                    response_headers = dict(resp.headers)
                    body = resp.read() or b""
            break
        except Exception as exc:
            last_exc = exc
            status_code = None
            response_headers = {}
            body = b""

    if status_code is None:
        raise RuntimeError(f"Decodo request failed after retries: {last_exc}")

    body_sha = _sha_bytes(body)
    artifact_id = _sha(f"{job.job_id}:{body_sha}")[:16]

    os.makedirs(out_raw_dir, exist_ok=True)
    body_path = os.path.join(out_raw_dir, f"{artifact_id}.bin")
    with open(body_path, "wb") as f:
        f.write(body)

    content_type = response_headers.get("Content-Type", "application/octet-stream")

    return RawFetchArtifact(
        artifact_id=artifact_id,
        run_id=job.run_id,
        job_id=job.job_id,
        fetched_ts=_utc_now_iso(),
        url=job.url,
        status_code=status_code,
        content_type=content_type,
        body_path=body_path,
        body_sha256=body_sha,
        meta={"attempts": max_retries + 1, "endpoint": endpoint},
        provenance={"transport": "decodo", "source_label": job.source_label},
    )
