"""
ERSAdapter.v0 (scaffold)

Interface for a scheduler adapter.
No implementation in v0.1.x.
"""

from __future__ import annotations

from typing import Protocol
from abx_familiar.adapters.ers.ers_types_v0 import ERSJobSpec, ERSSubmitResult, ERSStatus


class ERSAdapter(Protocol):
    def submit(self, spec: ERSJobSpec) -> ERSSubmitResult:
        ...

    def status(self, ers_job_id: str) -> ERSStatus:
        ...


class NullERSAdapter:
    """
    Deterministic no-op adapter.
    """

    def submit(self, spec: ERSJobSpec) -> ERSSubmitResult:
        return ERSSubmitResult(accepted=False, reason="null_adapter", ers_job_id=None, meta={"job_id": spec.job_id})

    def status(self, ers_job_id: str) -> ERSStatus:
        return ERSStatus(state="unknown", meta={"reason": "null_adapter"})
