from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from webpanel.ui_signal_sections import normalize_signal_sections

ORACLE_OUTPUT_KIND = "OracleOutput.v2"


def canonical_json_bytes(obj: Any) -> bytes:
    rendered = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return rendered.encode("utf-8")


def canonical_json_str(obj: Any) -> str:
    return canonical_json_bytes(obj).decode("utf-8")


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def extract_oracle_output(run: Any) -> Optional[Dict[str, Any]]:
    if run is None:
        return None
    oracle_output = getattr(run, "oracle_output", None)
    if isinstance(oracle_output, dict):
        return oracle_output
    step_results = getattr(run, "step_results", [])
    for result in reversed(step_results or []):
        if not isinstance(result, dict):
            continue
        if result.get("kind") != ORACLE_OUTPUT_KIND:
            continue
        payload = result.get("oracle_output") if "oracle_output" in result else result
        if isinstance(payload, dict):
            return payload
    return None


def validate_oracle_output_v2(obj: Any) -> Tuple[bool, List[str]]:
    if not isinstance(obj, dict):
        return False, ["oracle_output is not a dict"]
    try:
        import jsonschema

        schema_path = Path("schemas/oracle_output.v2.json")
        with open(schema_path, encoding="utf-8") as handle:
            schema = json.load(handle)
        jsonschema.validate(instance=obj, schema=schema)
        return True, []
    except Exception as exc:
        try:
            return _validate_oracle_output_minimal(obj)
        except Exception:
            return False, [str(exc)]


def _validate_oracle_output_minimal(obj: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    required = ["signal_id", "tier", "lane", "indicators", "evidence", "flags", "provenance"]
    for key in required:
        if key not in obj:
            errors.append(f"missing:{key}")
    provenance = _safe_dict(obj.get("provenance"))
    for key in ["input_hash", "policy_hash", "operator_versions", "stability_status"]:
        if key not in provenance:
            errors.append(f"missing:provenance.{key}")
    return (len(errors) == 0), errors


def _flatten_indicators(indicators: Any, prefix: str = "") -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if isinstance(indicators, dict):
        for key in sorted(indicators.keys(), key=lambda k: str(k)):
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            out.update(_flatten_indicators(indicators[key], next_prefix))
        return out
    if isinstance(indicators, list):
        for idx, item in enumerate(indicators):
            if isinstance(item, dict) and ("path" in item or "name" in item):
                label = str(item.get("path") or item.get("name") or idx)
                next_prefix = f"{prefix}.{label}" if prefix else label
                if "value" in item and len(item.keys()) <= 2:
                    out[next_prefix] = item.get("value")
                    continue
                out.update(_flatten_indicators(item, next_prefix))
                continue
            next_prefix = f"{prefix}[{idx}]" if prefix else f"[{idx}]"
            out.update(_flatten_indicators(item, next_prefix))
        return out
    key = prefix or "value"
    out[key] = indicators
    return out


def flatten_indicator_map(indicators: Any) -> Dict[str, Any]:
    return _flatten_indicators(indicators, prefix="")


def normalize_indicator_list(indicators: Any, limit: int = 20) -> List[Dict[str, Any]]:
    flat = flatten_indicator_map(indicators)
    items = [{"path": path, "value": flat[path]} for path in sorted(flat.keys())]
    return items[:limit]


def normalize_evidence_list(evidence: Any, limit: int = 20) -> List[str]:
    items = []
    for entry in _safe_list(evidence):
        if isinstance(entry, dict):
            items.append(canonical_json_str(entry))
        else:
            items.append(str(entry))
    return sorted(items)[:limit]


def normalize_flags(flags: Any) -> List[str]:
    items = []
    for key, value in sorted(_safe_dict(flags).items(), key=lambda kv: kv[0]):
        if isinstance(value, dict):
            rendered = canonical_json_str(value)
        else:
            rendered = str(value)
        items.append(f"{key}={rendered}")
    return items


def _build_structured_signal_payload(
    *,
    raw_signal: Dict[str, Any],
    structural_model: Dict[str, Any],
    optional_lenses: Dict[str, Any],
    claim_status: Dict[str, Any],
    omissions: List[Dict[str, str]],
) -> Dict[str, Any]:
    return {
        "raw_signal": raw_signal,
        "structural_model": structural_model,
        "optional_lenses": optional_lenses,
        "claim_status": claim_status,
        "omissions": omissions,
    }


def _legacy_oracle_payload_adapter(
    *,
    oracle_output: Dict[str, Any],
    summary: str,
    indicator_items: List[Dict[str, Any]],
    operator_version_list: List[Dict[str, Any]],
    flags_items: List[str],
    omissions: List[Dict[str, str]],
) -> Dict[str, Any]:
    suppressed = bool(_safe_dict(oracle_output.get("flags")).get("suppressed"))
    return normalize_signal_sections(
        _build_structured_signal_payload(
            raw_signal={
                "signal_id": str(oracle_output.get("signal_id", "")),
                "tier": str(oracle_output.get("tier", "")),
                "lane": str(oracle_output.get("lane", "")),
                "evidence": list(_safe_list(oracle_output.get("evidence"))),
            },
            structural_model={
                "indicator_total": len(flatten_indicator_map(oracle_output.get("indicators"))),
                "indicator_items": indicator_items,
                "operator_versions": operator_version_list,
                "legacy_summary": summary,
            },
            optional_lenses={
                "flags_items": flags_items,
                "stability_status": _safe_dict(oracle_output.get("provenance")).get("stability_status"),
            },
            claim_status={
                "label": "SUPPRESSED" if suppressed else "VISIBLE",
                "status": "SUCCESS",
                "suppressed": suppressed,
            },
            omissions=omissions,
        )
    )


def build_oracle_view(oracle_output: Dict[str, Any]) -> Dict[str, Any]:
    indicators = oracle_output.get("indicators")
    evidence = oracle_output.get("evidence")
    flags = oracle_output.get("flags")
    provenance = _safe_dict(oracle_output.get("provenance"))

    indicator_list = normalize_indicator_list(indicators, limit=20)
    evidence_list = normalize_evidence_list(evidence, limit=20)
    flags_list = normalize_flags(flags)

    operator_versions = _safe_dict(provenance.get("operator_versions"))
    operator_version_list = [
        {"name": key, "version": operator_versions[key]}
        for key in sorted(operator_versions.keys())
    ]

    summary = (
        f"Indicators: {len(flatten_indicator_map(indicators))} · "
        f"Evidence: {len(_safe_list(evidence))} · "
        f"Suppressed: {bool(_safe_dict(flags).get('suppressed'))}"
    )
    omissions: List[Dict[str, str]] = []
    if bool(_safe_dict(flags).get("suppressed")):
        omissions.append(
            {
                "omitted_by": "oracle_output.flags.suppressed",
                "omitted_reason": "hard_boundary_suppression",
                "source_pointer": "oracle_output.flags.suppressed",
                "boundary_type": "hard_boundary",
            }
        )
    structured_signal_payload = _legacy_oracle_payload_adapter(
        oracle_output=oracle_output,
        summary=summary,
        indicator_items=indicator_list,
        operator_version_list=operator_version_list,
        flags_items=flags_list,
        omissions=omissions,
    )

    return {
        "structured_signal_payload": structured_signal_payload,
        "tier": oracle_output.get("tier"),
        "lane": oracle_output.get("lane"),
        "summary": str(structured_signal_payload["structural_model"].get("legacy_summary", summary)),
        "indicator_items": indicator_list,
        "indicator_total": len(flatten_indicator_map(indicators)),
        "evidence_items": evidence_list,
        "evidence_total": len(_safe_list(evidence)),
        "flags_items": flags_list,
        "provenance": {
            "input_hash": provenance.get("input_hash"),
            "policy_hash": provenance.get("policy_hash"),
            "stability_status": provenance.get("stability_status"),
            "operator_versions": operator_version_list,
        },
    }


def evidence_entries(evidence: Any) -> List[str]:
    items = []
    for entry in _safe_list(evidence):
        if isinstance(entry, dict):
            items.append(canonical_json_str(entry))
        else:
            items.append(str(entry))
    return sorted(items)


def flag_entries(flags: Any) -> List[str]:
    return normalize_flags(flags)


def indicator_entries(indicators: Any) -> Dict[str, Any]:
    return flatten_indicator_map(indicators)


def oracle_hash_prefix(oracle_output: Dict[str, Any], key: str, length: int = 8) -> Optional[str]:
    provenance = _safe_dict(oracle_output.get("provenance"))
    value = provenance.get(key)
    if not isinstance(value, str):
        return None
    return value[:length]


def build_oracle_json(run: Any) -> Optional[str]:
    oracle_output = extract_oracle_output(run)
    if not oracle_output:
        return None
    return canonical_json_str(oracle_output)
