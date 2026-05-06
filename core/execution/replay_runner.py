from __future__ import annotations
from typing import Dict, Any
from core.execution.shadow_runner import ShadowExecutionRun, run_shadow_execution
from core.runes.replay import RuneReplayPacket
from core.models.governance import Authority
import hashlib


def replay_execution(
    run: ShadowExecutionRun,
    contract: Dict[str, Any],
    route_graph: Dict[str, Any],
    rune_catalog: Dict[str, Any],
) -> RuneReplayPacket:
    """Re-runs execution deterministically and compares receipt hashes."""
    new_run = run_shadow_execution(contract, route_graph, rune_catalog)

    source_hash = run.execution_context_hash
    replay_hash = new_run.execution_context_hash

    source_chain = run.receipt_chain_hash
    replay_chain = new_run.receipt_chain_hash

    mismatched = []
    if source_chain != replay_chain:
        mismatched.append(f"receipt_chain: {source_chain} != {replay_chain}")

    identical = (source_chain == replay_chain)
    deterministic = identical

    replay_id = hashlib.sha256(
        f"{source_hash}:{replay_hash}".encode("utf-8")
    ).hexdigest()

    return RuneReplayPacket(
        replay_id=replay_id,
        source_execution_hash=source_hash,
        replay_execution_hash=replay_hash,
        identical_output=identical,
        deterministic_match=deterministic,
        mismatched_receipts=mismatched,
        authority=run.authority,
        status="matched" if identical else "mismatch",
    )
