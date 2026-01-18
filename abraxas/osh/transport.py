from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Tuple

try:
    import requests
except ImportError:  # pragma: no cover - optional dependency
    requests = None

from .decodo_client import decodo_fetch
from .types import OSHFetchJob, RawFetchArtifact


class TransportMode(str, Enum):
    DECODO = "decodo"
    DIRECT_HTTP = "direct_http"
    OFFLINE_REQUIRED = "offline_required"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def direct_http_fetch(job: OSHFetchJob, out_raw_dir: str) -> RawFetchArtifact:
    """
    Secondary transport for allowlisted URLs only.
    Guardrail: require allowlist_source_id to be present.
    """
    if not job.allowlist_source_id:
        raise ValueError("direct_http_fetch refused: missing allowlist_source_id (allowlist-only guardrail).")
    if not (job.url.startswith("http://") or job.url.startswith("https://")):
        raise ValueError("direct_http_fetch refused: URL must be http(s).")

    timeout_s = int(os.getenv("DIRECT_HTTP_TIMEOUT_S", "30"))
    max_retries = int(os.getenv("DIRECT_HTTP_MAX_RETRIES", "1"))

    last_exc: Exception | None = None
    status_code: int | None = None
    headers: dict[str, str] = {}
    body = b""
    for _ in range(max_retries + 1):
        try:
            if requests is not None:
                resp = requests.get(job.url, timeout=timeout_s)
                status_code = int(resp.status_code)
                headers = dict(resp.headers)
                body = resp.content or b""
            else:
                from urllib.request import urlopen

                with urlopen(job.url, timeout=timeout_s) as resp:
                    status_code = int(getattr(resp, "status", 200))
                    headers = dict(resp.headers)
                    body = resp.read() or b""
            break
        except Exception as exc:
            last_exc = exc
            status_code = None
            headers = {}
            body = b""

    if status_code is None:
        raise RuntimeError(f"Direct HTTP fetch failed after retries: {last_exc}")
    body_sha = _sha_bytes(body)
    artifact_id = _sha(f"{job.job_id}:{body_sha}")[:16]

    os.makedirs(out_raw_dir, exist_ok=True)
    body_path = os.path.join(out_raw_dir, f"{artifact_id}.bin")
    with open(body_path, "wb") as f:
        f.write(body)

    content_type = headers.get("Content-Type", "application/octet-stream")
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
        meta={"attempts": max_retries + 1, "endpoint": "direct_http"},
        provenance={"transport": TransportMode.DIRECT_HTTP.value, "source_label": job.source_label},
    )


def fetch_with_fallback(
    job: OSHFetchJob,
    out_raw_dir: str,
) -> Tuple[Optional[RawFetchArtifact], TransportMode, Optional[str]]:
    """
    Transport ladder:
      1) Decodo (if configured)
      2) Direct HTTP (allowlist-only)
      3) Offline required (return None + reason)
    """
    if os.getenv("DECODO_API_KEY"):
        try:
            art = decodo_fetch(job, out_raw_dir=out_raw_dir)
            return art, TransportMode.DECODO, None
        except Exception as exc:
            decodo_err = f"decodo_failed: {type(exc).__name__}: {exc}"
    else:
        decodo_err = "decodo_unavailable: missing DECODO_API_KEY"

    try:
        art = direct_http_fetch(job, out_raw_dir=out_raw_dir)
        return art, TransportMode.DIRECT_HTTP, decodo_err
    except Exception as exc:
        http_err = f"direct_http_failed: {type(exc).__name__}: {exc}"

    return None, TransportMode.OFFLINE_REQUIRED, f"{decodo_err}; {http_err}"
