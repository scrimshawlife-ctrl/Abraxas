from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List
import os
import time
from pathlib import Path

from abx.ingest.jobs_schema import load_jobs, IngestJob
from abx.ingest.decodo_client import scrape_url
from abx.store.sqlite_store import connect, init_db, upsert_document
from abx.util.hashutil import sha256_bytes
from abx.util.logging import log, warn, err

@dataclass
class JobState:
    next_run: int = 0
    last_ok: int = 0
    last_error: str = ""

def _doc_id(job: IngestJob, sha: str) -> str:
    # deterministic id for snapshot; can also use job name + sha prefix
    return f"{job.name}:{sha[:16]}"

def run_ingest_forever(jobs_path: str, interval_s: int) -> None:
    con = connect()
    init_db(con)

    states: Dict[str, JobState] = {}
    log("ingest_start", jobs_path=jobs_path, interval_s=interval_s)

    while True:
        jobs = load_jobs(jobs_path)
        now = int(time.time())

        for job in jobs:
            if not job.enabled:
                continue
            st = states.setdefault(job.name, JobState(next_run=0))
            if now < st.next_run:
                continue

            try:
                log("ingest_job_start", name=job.name, url=job.url)
                res = scrape_url(job.url, target=job.target, headless=job.headless, locale=job.locale, device_type=job.device_type)
                raw = (str(res)).encode("utf-8")
                sha = sha256_bytes(raw)
                doc_id = _doc_id(job, sha)
                upsert_document(
                    con,
                    doc_id=doc_id,
                    source=f"decodo:{job.name}",
                    url=job.url,
                    content_type="application/json",
                    payload=res,
                    sha256=sha,
                )
                st.last_ok = now
                st.last_error = ""
                st.next_run = now + max(5, int(job.every_s))
                log("ingest_job_ok", name=job.name, sha256=sha, next_run=st.next_run)
            except Exception as e:
                st.last_error = str(e)
                # backoff: try again later but not too fast
                st.next_run = now + max(30, int(job.every_s // 3) or 60)
                warn("ingest_job_fail", name=job.name, error=st.last_error, next_run=st.next_run)

        time.sleep(max(1, interval_s))
