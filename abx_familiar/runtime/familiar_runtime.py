from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from abx_familiar.ir.continuity_ledger_v0 import ContinuityLedgerEntry


@dataclass(frozen=True)
class ScheduledOp:
    invocation_id: str
    rune_id: str
    state: str


class Keeper:
    def run(self, **kwargs: Any) -> ContinuityLedgerEntry:
        return ContinuityLedgerEntry(
            run_id=str(kwargs.get("run_id", "")),
            input_hash=str(kwargs.get("input_hash", "")),
            task_graph_hash=str(kwargs.get("task_graph_hash", "")),
            invocation_plan_hash=str(kwargs.get("invocation_plan_hash", "")),
            output_hash=kwargs.get("output_hash"),
            prior_run_id=kwargs.get("prior_run_id"),
            delta_summary=kwargs.get("delta_summary"),
            stabilization_cycle=int(kwargs.get("stabilization_cycle", 0)),
            meta=dict(kwargs.get("meta", {})),
            not_computable=bool(kwargs.get("not_computable", False)),
            missing_fields=list(kwargs.get("missing_fields", [])),
        )


class TaskGraph:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    def hash(self) -> str:
        return _hash_payload(self._payload)


class InvocationPlan:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    def hash(self) -> str:
        return _hash_payload(self._payload)


class DeliveryPack:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    def hash(self) -> str:
        return _hash_payload(self._payload)


def _hash_payload(payload: Dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class FamiliarRuntime:
    def __init__(self, *, ledger_store: Optional[Any] = None) -> None:
        self._ledger_writer = ledger_store
        self.keeper = Keeper()

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        run_id = str(context.get("run_id", ""))
        summoner = context.get("summoner", {})
        task_graph = TaskGraph({"summoner": summoner})
        invocation_plan = InvocationPlan({"requested_ops": summoner.get("requested_ops", [])})
        delivery_pack = DeliveryPack({"run_id": run_id, "task_id": summoner.get("task_id")})

        artifacts: Dict[str, Any] = {
            "task_graph": task_graph,
            "delivery_pack": delivery_pack,
        }
        scheduled_ops: List[ScheduledOp] = []

        # 7) Keeper (with stabilization window + prior run linking when ledger is configured)
        prior_entry = None
        if self._ledger_writer is not None:
            # Safe: ledger_writer.read_all() returns iterable; store preserves insertion order.
            from abx_familiar.ledger.ledger_tools import get_last_entry

            # NOTE: read_all() is a Protocol; some stores may not support multiple passes.
            # In v0.1 we assume in-memory store or equivalent stable iterable.
            prior_entry = get_last_entry(self._ledger_writer.read_all())

        stabilization_enabled = bool(context.get("stabilization_enabled", False))
        window_size = int(context.get("stabilization_window_size", 0)) if stabilization_enabled else 0

        prior_run_id = prior_entry.run_id if prior_entry is not None else None
        prior_task_graph_hash = prior_entry.task_graph_hash if prior_entry is not None else None

        # Deterministic cycle increment when enabled
        if stabilization_enabled and prior_entry is not None:
            stabilization_cycle = prior_entry.stabilization_cycle + 1
        elif stabilization_enabled and prior_entry is None:
            stabilization_cycle = 1
        else:
            stabilization_cycle = 0

        # Mechanical delta summary: compare prior vs current task_graph hashes only.
        delta_summary = None
        if prior_entry is not None:
            from abx_familiar.ledger.diff_tools import diff_hashes

            d = diff_hashes(
                prior_run_id=prior_run_id,
                current_run_id=run_id,
                prior_hash=prior_task_graph_hash,
                current_hash=task_graph.hash(),
                meta={"window_size": window_size, "stabilization_enabled": stabilization_enabled},
            )
            delta_summary = d.reason

        if "keeper" in context:
            ledger_entry = self.keeper.run(**context["keeper"])
        else:
            ledger_entry = self.keeper.run(
                run_id=run_id,
                input_hash=context.get("input_hash", "missing"),
                task_graph_hash=task_graph.hash(),
                invocation_plan_hash=invocation_plan.hash(),
                output_hash=None,
                prior_run_id=prior_run_id,
                delta_summary=delta_summary,
                stabilization_cycle=stabilization_cycle,
                meta={
                    "stabilization_enabled": stabilization_enabled,
                    "stabilization_window_size": window_size,
                },
                not_computable=True,
                missing_fields=["keeper"],
            )

        artifacts["ledger_entry"] = ledger_entry
        scheduled_ops.append(ScheduledOp(invocation_id="keeper", rune_id="abx.familiar.keep.v0", state="completed"))

        # Append to ledger store if configured (append-only)
        if self._ledger_writer is not None:
            self._ledger_writer.append(ledger_entry)

        return {
            "ledger_entry": ledger_entry,
            "task_graph": task_graph,
            "delivery_pack": delivery_pack,
            "artifacts": artifacts,
            "scheduled_ops": scheduled_ops,
        }
