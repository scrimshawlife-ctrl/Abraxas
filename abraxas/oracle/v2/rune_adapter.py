"""Rune adapter for Oracle V2 pipeline.

Thin adapter layer exposing oracle.v2 via ABX-Runes capability system.
SEED Compliant: Deterministic, provenance-tracked.

Repaired 2026-10-06
-------------------
This module previously did

    from abraxas.oracle.v2.pipeline import run_oracle as run_oracle_core

and `pipeline.py` defines no `run_oracle` — it exposes `OracleV2Pipeline` and
`create_oracle_v2_pipeline`. So the module FAILED TO IMPORT, which made the binding
`ϟ_ORACLE_RUN` entirely dead. Nothing noticed because nothing called
`run_oracle_deterministic`; it was found by resolving every declared operator path
(`abraxas/yggdrasil/binding_matrix.py`).

The interface was never in doubt, which is what makes this a repair rather than an
invention. Two canonical witnesses fix it:

* ``schemas/capabilities/oracle_run_input.schema.json`` — the contract for
  ``RUNE.ORACLE.V2.RUN``: ``observations`` is an array of ``{term, context, timestamp}``
  with ``minItems 1``. The signature below already matched it and is unchanged.
* ``schemas/capabilities/oracle_run_output.schema.json`` — the return contract:
  either ``{oracle_output, provenance}`` or ``{not_computable}``, with ``provenance``
  requiring ``timestamp_utc``, ``config_sha256`` and ``inputs_sha256``. Also unchanged.

Only the invocation was wrong. The pipeline takes an ``OracleSignal``, whose
``observations`` are raw text and whose ``tokens`` are extracted terms, so the adapter now
maps the schema-shaped records onto it. Every mapping decision is forced by a witness: the
field names come from the signature, the semantics from the schema, and the determinism
requirement from the binding's ``deterministic: true``.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Optional

from abraxas.core.provenance import canonical_envelope
from abraxas.oracle.v2.pipeline import OracleSignal, create_oracle_v2_pipeline

#: Used when the caller supplies no `config.domain`. A constant, not a default from the
#: environment: the binding declares `deterministic: true`, so two identical calls must
#: produce identical output. `OracleSignal.domain` is required, so something must be chosen.
DEFAULT_DOMAIN = "unspecified"

#: The operation this adapter implements, as declared in the binding.
OPERATION_ID = "RUNE.ORACLE.V2.RUN"


def _to_signal(run_id: str, observations: List[dict], config: dict) -> OracleSignal:
    """Map schema-shaped observation records onto the pipeline's `OracleSignal`.

    ``OracleSignal.observations`` is ``List[str]`` (raw text) and ``tokens`` is
    ``List[str]`` (extracted terms), while the input schema describes records of
    ``{term, context, timestamp}``. So `context` supplies the raw text and `term` the
    token — the only reading consistent with both.

    ``timestamp_utc`` is the LATEST record timestamp rather than "now": the binding is
    deterministic, and a wall clock would make identical inputs hash differently.
    """
    texts = [str(record.get("context") or record.get("term") or "") for record in observations]
    tokens = [str(record["term"]) for record in observations if record.get("term")]

    timestamps = sorted(str(record["timestamp"]) for record in observations if record.get("timestamp"))
    timestamp_utc = timestamps[-1] if timestamps else ""

    return OracleSignal(
        domain=str(config.get("domain") or DEFAULT_DOMAIN),
        subdomain=None,
        observations=texts,
        tokens=tokens,
        timestamp_utc=timestamp_utc,
        source_id=None,
        meta={"run_id": run_id},
    )


def _as_jsonable(value: Any) -> Any:
    """Convert the pipeline's dataclasses into plain data for the provenance envelope.

    `canonical_envelope` hashes ``result``, so a dataclass left in place would either raise
    or hash by ``repr`` and become unstable across field ordering.
    """
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(value)
    if isinstance(value, dict):
        return {key: _as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_as_jsonable(item) for item in value]
    return value


def run_oracle_deterministic(
    run_id: str,
    observations: list[dict],
    config: Optional[dict] = None,
    seed: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Rune-compatible oracle V2 runner.

    Wraps the oracle V2 pipeline with provenance envelope and validation.

    Args:
        run_id: Unique run identifier
        observations: Observation records of {term, context, timestamp}
        config: Optional configuration dictionary (may carry `domain`)
        seed: Optional deterministic seed

    Returns:
        Dictionary with oracle_output, provenance, and optionally not_computable
    """
    config = config or {}

    # The input schema declares minItems 1. Report the absence rather than inventing a
    # signal, so a caller can tell "no input" from "computed nothing".
    if not observations:
        return {
            "oracle_output": None,
            "not_computable": {
                "reason": "observations is empty; the input schema requires at least one",
                "missing_inputs": ["observations"],
            },
            "provenance": None,
        }

    try:
        signal = _to_signal(run_id, observations, config)
        pipeline = create_oracle_v2_pipeline(config)
        oracle_output = _as_jsonable(pipeline.process(signal, run_id=run_id))
    except Exception as e:  # noqa: BLE001 - reported as not_computable, never faked
        return {
            "oracle_output": None,
            "not_computable": {
                "reason": f"{type(e).__name__}: {e}",
                "missing_inputs": [],
            },
            "provenance": None,
        }

    # Wrap in canonical envelope
    envelope = canonical_envelope(
        result=oracle_output,
        config=config,
        inputs={"run_id": run_id, "observations": observations},
        operation_id=OPERATION_ID,
        seed=seed,
    )

    # Rename 'result' key to 'oracle_output' for clarity
    return {
        "oracle_output": envelope["result"],
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"],
    }


__all__ = ["DEFAULT_DOMAIN", "OPERATION_ID", "run_oracle_deterministic"]
