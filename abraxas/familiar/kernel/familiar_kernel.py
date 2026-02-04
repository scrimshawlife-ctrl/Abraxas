from __future__ import annotations

from typing import Any, Dict, List, Optional
from pathlib import Path
import json

import jsonschema

from abraxas.familiar.adapters.forager_registry import ForagerRegistry
from abraxas.familiar.kernel.capability_gate import evaluate_capabilities
from abraxas.familiar.kernel.ers_adapter import ERSAdapter
from abraxas.familiar.kernel.run_planner import build_run_plan, PlanError
from abraxas.familiar.ledger.hash_chain import build_ledger_event
from abraxas.familiar.ledger.ledger_store import InMemoryLedgerStore
from abraxas.util.canonical_hash import canonical_hash


_RUN_REQUEST_SCHEMA = "run_request.v0.json"
_UNKNOWN_RUN_ID = "unknown_run"


def _contracts_root() -> Path:
    return Path(__file__).resolve().parents[1] / "contracts"


def _load_schema(schema_name: str) -> Dict[str, Any]:
    schema_path = _contracts_root() / schema_name
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _format_error_path(path: List[Any]) -> str:
    if not path:
        return "$"
    parts = []
    for item in path:
        if isinstance(item, int):
            parts.append(f"[{item}]")
        else:
            parts.append(f".{item}")
    return "$" + "".join(parts)


class FamiliarKernel:
    def __init__(
        self,
        *,
        ledger_store: Optional[InMemoryLedgerStore] = None,
        ers_adapter: Optional[ERSAdapter] = None,
        forager_registry: Optional[ForagerRegistry] = None,
    ) -> None:
        self.ledger_store = ledger_store or InMemoryLedgerStore()
        self.ers_adapter = ers_adapter or ERSAdapter()
        self.forager_registry = forager_registry or ForagerRegistry()
        schema = _load_schema(_RUN_REQUEST_SCHEMA)
        self._validator = jsonschema.Draft202012Validator(schema)

    def _validate_request(self, run_request: Dict[str, Any]) -> List[Dict[str, str]]:
        errors = sorted(self._validator.iter_errors(run_request), key=lambda e: list(e.path))
        return [
            {"path": _format_error_path(list(e.path)), "message": e.message}
            for e in errors
        ]

    def _load_policy_snapshot(self, run_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if isinstance(run_request.get("policy_snapshot"), dict):
            return run_request.get("policy_snapshot")
        policy_id = run_request.get("policy_snapshot_id")
        if isinstance(policy_id, str):
            return self.forager_registry.get_policy_snapshot(policy_id)
        return None

    def _missing_inputs(
        self,
        *,
        inputs: Dict[str, Any],
        required_inputs: List[str],
    ) -> List[str]:
        missing = []
        for key in required_inputs:
            if key not in inputs or inputs.get(key) is None:
                missing.append(key)
        return sorted(set(missing))

    def _build_run_result(
        self,
        *,
        run_id: str,
        status: str,
        not_computable: bool,
        reason_code: str,
        missing_inputs: List[str],
        outputs: Optional[Dict[str, Any]],
        input_hash: Optional[str],
        plan_hash: Optional[str],
        policy_hash: Optional[str],
        capability_decision_hash: Optional[str],
        details: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        payload = {
            "schema_version": "v0",
            "run_id": run_id,
            "status": status,
            "not_computable": not_computable,
            "reason_code": reason_code,
            "missing_inputs": list(missing_inputs),
            "outputs": outputs,
            "input_hash": input_hash,
            "plan_hash": plan_hash,
            "policy_hash": policy_hash,
            "capability_decision_hash": capability_decision_hash,
            "details": details,
        }
        result_hash = canonical_hash(payload)
        return {**payload, "result_hash": result_hash}

    def _build_provenance_record(
        self,
        *,
        run_id: str,
        input_hash: Optional[str],
        plan_hash: Optional[str],
        policy_hash: Optional[str],
        capability_decision_hash: Optional[str],
        result_hash: str,
        details: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        payload = {
            "schema_version": "v0",
            "run_id": run_id,
            "input_hash": input_hash,
            "plan_hash": plan_hash,
            "policy_hash": policy_hash,
            "capability_decision_hash": capability_decision_hash,
            "result_hash": result_hash,
            "details": details,
        }
        provenance_hash = canonical_hash(payload)
        return {**payload, "provenance_hash": provenance_hash}

    def run(self, run_request: Dict[str, Any]) -> Dict[str, Any]:
        run_id = run_request.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            run_id = _UNKNOWN_RUN_ID

        validation_errors = self._validate_request(run_request)
        if validation_errors:
            run_result = self._build_run_result(
                run_id=run_id,
                status="not_computable",
                not_computable=True,
                reason_code="invalid_request",
                missing_inputs=[],
                outputs=None,
                input_hash=None,
                plan_hash=None,
                policy_hash=None,
                capability_decision_hash=None,
                details={"validation_errors": validation_errors},
            )
            provenance = self._build_provenance_record(
                run_id=run_id,
                input_hash=None,
                plan_hash=None,
                policy_hash=None,
                capability_decision_hash=None,
                result_hash=run_result["result_hash"],
                details={"validation_errors": validation_errors},
            )
            ledger_event = self._append_ledger_event(
                run_id=run_id,
                run_result=run_result,
                provenance=provenance,
                input_hash=None,
                plan_hash=None,
                policy_hash=None,
                capability_decision_hash=None,
            )
            return {
                "run_result": run_result,
                "provenance_record": provenance,
                "ledger_event": ledger_event,
                "run_plan": None,
                "capability_decision": None,
            }

        inputs = run_request.get("inputs")
        if not isinstance(inputs, dict):
            inputs = {}
        input_hash = canonical_hash(inputs)

        policy_snapshot = self._load_policy_snapshot(run_request)
        if policy_snapshot is None:
            missing_inputs = ["policy_snapshot"]
            run_result = self._build_run_result(
                run_id=run_id,
                status="not_computable",
                not_computable=True,
                reason_code="missing_input",
                missing_inputs=missing_inputs,
                outputs=None,
                input_hash=input_hash,
                plan_hash=None,
                policy_hash=None,
                capability_decision_hash=None,
                details={"missing_inputs": missing_inputs},
            )
            provenance = self._build_provenance_record(
                run_id=run_id,
                input_hash=input_hash,
                plan_hash=None,
                policy_hash=None,
                capability_decision_hash=None,
                result_hash=run_result["result_hash"],
                details={"missing_inputs": missing_inputs},
            )
            ledger_event = self._append_ledger_event(
                run_id=run_id,
                run_result=run_result,
                provenance=provenance,
                input_hash=input_hash,
                plan_hash=None,
                policy_hash=None,
                capability_decision_hash=None,
            )
            return {
                "run_result": run_result,
                "provenance_record": provenance,
                "ledger_event": ledger_event,
                "run_plan": None,
                "capability_decision": None,
            }

        policy_hash = canonical_hash(policy_snapshot)
        requested_caps = run_request.get("requested_capabilities") or []
        capability_decision = evaluate_capabilities(policy_snapshot, requested_caps)
        capability_decision_hash = canonical_hash(capability_decision)
        if not capability_decision.get("allowed", False):
            run_result = self._build_run_result(
                run_id=run_id,
                status="not_computable",
                not_computable=True,
                reason_code=capability_decision.get("reason_code", "capability_denied"),
                missing_inputs=[],
                outputs=None,
                input_hash=input_hash,
                plan_hash=None,
                policy_hash=policy_hash,
                capability_decision_hash=capability_decision_hash,
                details={"denied_capabilities": capability_decision.get("denied_capabilities", [])},
            )
            provenance = self._build_provenance_record(
                run_id=run_id,
                input_hash=input_hash,
                plan_hash=None,
                policy_hash=policy_hash,
                capability_decision_hash=capability_decision_hash,
                result_hash=run_result["result_hash"],
                details={"capability_decision": capability_decision},
            )
            ledger_event = self._append_ledger_event(
                run_id=run_id,
                run_result=run_result,
                provenance=provenance,
                input_hash=input_hash,
                plan_hash=None,
                policy_hash=policy_hash,
                capability_decision_hash=capability_decision_hash,
            )
            return {
                "run_result": run_result,
                "provenance_record": provenance,
                "ledger_event": ledger_event,
                "run_plan": None,
                "capability_decision": capability_decision,
            }

        required_inputs = run_request.get("required_inputs") or []
        if not isinstance(required_inputs, list):
            required_inputs = []
        missing_inputs = self._missing_inputs(inputs=inputs, required_inputs=required_inputs)
        if missing_inputs:
            run_result = self._build_run_result(
                run_id=run_id,
                status="not_computable",
                not_computable=True,
                reason_code="missing_input",
                missing_inputs=missing_inputs,
                outputs=None,
                input_hash=input_hash,
                plan_hash=None,
                policy_hash=policy_hash,
                capability_decision_hash=capability_decision_hash,
                details={"missing_inputs": missing_inputs},
            )
            provenance = self._build_provenance_record(
                run_id=run_id,
                input_hash=input_hash,
                plan_hash=None,
                policy_hash=policy_hash,
                capability_decision_hash=capability_decision_hash,
                result_hash=run_result["result_hash"],
                details={"missing_inputs": missing_inputs},
            )
            ledger_event = self._append_ledger_event(
                run_id=run_id,
                run_result=run_result,
                provenance=provenance,
                input_hash=input_hash,
                plan_hash=None,
                policy_hash=policy_hash,
                capability_decision_hash=capability_decision_hash,
            )
            return {
                "run_result": run_result,
                "provenance_record": provenance,
                "ledger_event": ledger_event,
                "run_plan": None,
                "capability_decision": capability_decision,
            }

        try:
            run_plan = build_run_plan(run_request)
        except PlanError as exc:
            run_result = self._build_run_result(
                run_id=run_id,
                status="not_computable",
                not_computable=True,
                reason_code="plan_invalid",
                missing_inputs=[],
                outputs=None,
                input_hash=input_hash,
                plan_hash=None,
                policy_hash=policy_hash,
                capability_decision_hash=capability_decision_hash,
                details={"error": str(exc)},
            )
            provenance = self._build_provenance_record(
                run_id=run_id,
                input_hash=input_hash,
                plan_hash=None,
                policy_hash=policy_hash,
                capability_decision_hash=capability_decision_hash,
                result_hash=run_result["result_hash"],
                details={"error": str(exc)},
            )
            ledger_event = self._append_ledger_event(
                run_id=run_id,
                run_result=run_result,
                provenance=provenance,
                input_hash=input_hash,
                plan_hash=None,
                policy_hash=policy_hash,
                capability_decision_hash=capability_decision_hash,
            )
            return {
                "run_result": run_result,
                "provenance_record": provenance,
                "ledger_event": ledger_event,
                "run_plan": None,
                "capability_decision": capability_decision,
            }

        plan_hash = canonical_hash(run_plan)
        execution = self.ers_adapter.execute(run_plan, inputs)
        outputs = execution.get("outputs") if isinstance(execution, dict) else None

        run_result = self._build_run_result(
            run_id=run_id,
            status="ok",
            not_computable=False,
            reason_code="ok",
            missing_inputs=[],
            outputs=outputs,
            input_hash=input_hash,
            plan_hash=plan_hash,
            policy_hash=policy_hash,
            capability_decision_hash=capability_decision_hash,
            details={"step_count": len(run_plan.get("steps", []))},
        )
        provenance = self._build_provenance_record(
            run_id=run_id,
            input_hash=input_hash,
            plan_hash=plan_hash,
            policy_hash=policy_hash,
            capability_decision_hash=capability_decision_hash,
            result_hash=run_result["result_hash"],
            details={"execution": execution},
        )
        ledger_event = self._append_ledger_event(
            run_id=run_id,
            run_result=run_result,
            provenance=provenance,
            input_hash=input_hash,
            plan_hash=plan_hash,
            policy_hash=policy_hash,
            capability_decision_hash=capability_decision_hash,
        )
        return {
            "run_result": run_result,
            "provenance_record": provenance,
            "ledger_event": ledger_event,
            "run_plan": run_plan,
            "capability_decision": capability_decision,
        }

    def _append_ledger_event(
        self,
        *,
        run_id: str,
        run_result: Dict[str, Any],
        provenance: Dict[str, Any],
        input_hash: Optional[str],
        plan_hash: Optional[str],
        policy_hash: Optional[str],
        capability_decision_hash: Optional[str],
    ) -> Dict[str, Any]:
        payload = {
            "run_id": run_id,
            "result_hash": run_result.get("result_hash"),
            "provenance_hash": provenance.get("provenance_hash"),
            "input_hash": input_hash,
            "plan_hash": plan_hash,
            "policy_hash": policy_hash,
            "capability_decision_hash": capability_decision_hash,
            "status": run_result.get("status"),
            "reason_code": run_result.get("reason_code"),
        }
        prev_hash = self.ledger_store.last_hash()
        event = build_ledger_event(
            run_id=run_id,
            event_type="familiar_run",
            payload=payload,
            prev_hash=prev_hash,
        )
        self.ledger_store.append(event)
        return event
