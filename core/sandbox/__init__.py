"""core.sandbox - v2.0.5 governed adaptive sandbox package.

Provides:
- AdaptiveSandboxBranch.v1
- CandidateMutationPacket.v1
- SandboxReplayPacket.v1
- SandboxStabilizationPacket.v1
- SandboxPromotionCandidate.v1
- AdaptiveBranchLineage.v1
- MutationProposalReceipt.v1
- AdaptiveSimulationRun.v1
- sandbox runtime engine
- adaptive replay validator
- promotion gating validator
- doctrine validator extensions

Everything remains:
- deterministic
- replayable
- governance-first
- fail-closed
- shadow-only
- projection-safe
- sandbox-isolated
"""
from __future__ import annotations
