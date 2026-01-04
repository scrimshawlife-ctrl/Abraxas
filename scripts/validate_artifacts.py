#!/usr/bin/env python3
"""
Abraxas Artifact Validator — Validate artifacts against JSON schemas.

Usage:
  python -m scripts.validate_artifacts --artifacts_dir ./artifacts --run_id seal --tick 0
  python -m scripts.validate_artifacts --artifacts_dir ./artifacts --run_id seal  # all ticks

Validates:
  - RunIndex.v0
  - TrendPack.v0
  - ResultsPack.v0
  - ViewPack.v0
  - RunHeader.v0
  - PolicySnapshot.v0 (if present)
  - RunStability.v0 (if present)
  - StabilityRef.v0 (if present)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Schema loader and cache
_SCHEMA_CACHE: Dict[str, Dict[str, Any]] = {}


def _load_schema(schema_name: str, schemas_dir: Optional[str] = None) -> Dict[str, Any]:
    """Load a JSON schema by name (e.g., 'runindex.v0')."""
    if schema_name in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[schema_name]

    if schemas_dir is None:
        # Default to schemas/ relative to repo root
        schemas_dir = str(Path(__file__).parent.parent / "schemas")

    schema_file = Path(schemas_dir) / f"{schema_name}.schema.json"
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema not found: {schema_file}")

    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    _SCHEMA_CACHE[schema_name] = schema
    return schema


def _validate_type(value: Any, expected_type: Any) -> bool:
    """Validate value against JSON Schema type."""
    if expected_type == "string":
        return isinstance(value, str)
    elif expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected_type == "boolean":
        return isinstance(value, bool)
    elif expected_type == "object":
        return isinstance(value, dict)
    elif expected_type == "array":
        return isinstance(value, list)
    elif expected_type == "null":
        return value is None
    elif isinstance(expected_type, list):
        # Union type: ["string", "null"]
        return any(_validate_type(value, t) for t in expected_type)
    return True


def _validate_const(value: Any, const_value: Any) -> bool:
    """Validate const constraint."""
    return value == const_value


def _validate_object(obj: Any, schema: Dict[str, Any], path: str = "") -> List[str]:
    """
    Validate an object against a JSON Schema (minimal implementation).
    Returns list of error messages.
    """
    errors: List[str] = []

    if not isinstance(obj, dict):
        errors.append(f"{path}: expected object, got {type(obj).__name__}")
        return errors

    # Check required fields
    required = schema.get("required", [])
    for field in required:
        if field not in obj:
            errors.append(f"{path}.{field}: required field missing")

    # Check properties
    properties = schema.get("properties", {})
    for prop_name, prop_schema in properties.items():
        if prop_name not in obj:
            continue

        prop_path = f"{path}.{prop_name}" if path else prop_name
        prop_value = obj[prop_name]

        # Type check
        if "type" in prop_schema:
            if not _validate_type(prop_value, prop_schema["type"]):
                errors.append(f"{prop_path}: type mismatch, expected {prop_schema['type']}")
                continue

        # Const check
        if "const" in prop_schema:
            if not _validate_const(prop_value, prop_schema["const"]):
                errors.append(f"{prop_path}: const mismatch, expected {prop_schema['const']!r}, got {prop_value!r}")

        # Pattern check for strings
        if "pattern" in prop_schema and isinstance(prop_value, str):
            import re
            if not re.match(prop_schema["pattern"], prop_value):
                errors.append(f"{prop_path}: pattern mismatch, expected {prop_schema['pattern']}")

        # Recursive object validation
        if prop_schema.get("type") == "object" and isinstance(prop_value, dict):
            errors.extend(_validate_object(prop_value, prop_schema, prop_path))

        # Array items validation
        if prop_schema.get("type") == "array" and isinstance(prop_value, list):
            items_schema = prop_schema.get("items", {})
            for i, item in enumerate(prop_value):
                item_path = f"{prop_path}[{i}]"
                if items_schema.get("type") == "object":
                    errors.extend(_validate_object(item, items_schema, item_path))

    return errors


def validate_artifact(artifact_path: str, schema_name: str, schemas_dir: Optional[str] = None) -> Tuple[bool, List[str]]:
    """
    Validate an artifact file against its schema.
    
    Returns:
        (ok, errors) tuple
    """
    path = Path(artifact_path)
    if not path.exists():
        return False, [f"File not found: {artifact_path}"]

    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, [f"JSON parse error: {e}"]

    try:
        schema = _load_schema(schema_name, schemas_dir)
    except FileNotFoundError as e:
        return False, [str(e)]

    errors = _validate_object(obj, schema)
    return len(errors) == 0, errors


def validate_tick(
    artifacts_dir: str,
    run_id: str,
    tick: int,
    schemas_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validate all artifacts for a single tick.
    
    Returns:
        {ok: bool, tick: int, failures: [{artifact_kind, path, errors}]}
    """
    failures: List[Dict[str, Any]] = []
    base = Path(artifacts_dir)

    # 1) Validate RunIndex
    runindex_path = base / "run_index" / run_id / f"{tick:06d}.runindex.json"
    ok, errs = validate_artifact(str(runindex_path), "runindex.v0", schemas_dir)
    if not ok:
        failures.append({"artifact_kind": "RunIndex.v0", "path": str(runindex_path), "errors": errs})
        # If RunIndex is invalid, we can't validate others via refs
        return {"ok": False, "tick": tick, "failures": failures}

    # Load RunIndex to get refs
    runindex = json.loads(runindex_path.read_text(encoding="utf-8"))
    refs = runindex.get("refs", {})

    # 2) Validate TrendPack
    trendpack_path = refs.get("trendpack")
    if trendpack_path:
        ok, errs = validate_artifact(trendpack_path, "trendpack.v0", schemas_dir)
        if not ok:
            failures.append({"artifact_kind": "TrendPack.v0", "path": trendpack_path, "errors": errs})

    # 3) Validate ResultsPack
    results_pack_path = refs.get("results_pack")
    if results_pack_path:
        ok, errs = validate_artifact(results_pack_path, "resultspack.v0", schemas_dir)
        if not ok:
            failures.append({"artifact_kind": "ResultsPack.v0", "path": results_pack_path, "errors": errs})

    # 4) Validate RunHeader
    run_header_path = refs.get("run_header")
    if run_header_path:
        ok, errs = validate_artifact(run_header_path, "runheader.v0", schemas_dir)
        if not ok:
            failures.append({"artifact_kind": "RunHeader.v0", "path": run_header_path, "errors": errs})

    # 5) Validate ViewPack (derive path from convention)
    viewpack_path = base / "view" / run_id / f"{tick:06d}.viewpack.json"
    if viewpack_path.exists():
        ok, errs = validate_artifact(str(viewpack_path), "viewpack.v0", schemas_dir)
        if not ok:
            failures.append({"artifact_kind": "ViewPack.v0", "path": str(viewpack_path), "errors": errs})

    # 6) Cross-check: TrendPack events' result_ref.results_pack should match ResultsPack path
    if trendpack_path and results_pack_path:
        tp = json.loads(Path(trendpack_path).read_text(encoding="utf-8"))
        for i, event in enumerate(tp.get("timeline", [])):
            result_ref = event.get("meta", {}).get("result_ref", {})
            rp_path = result_ref.get("results_pack")
            if rp_path:
                # Normalize paths for comparison (just filenames)
                rp_name = Path(rp_path).name
                expected_name = Path(results_pack_path).name
                if rp_name != expected_name:
                    failures.append({
                        "artifact_kind": "TrendPack.v0",
                        "path": trendpack_path,
                        "errors": [f"timeline[{i}].meta.result_ref.results_pack filename mismatch: {rp_name} != {expected_name}"],
                    })

    return {"ok": len(failures) == 0, "tick": tick, "failures": failures}


def validate_run(
    artifacts_dir: str,
    run_id: str,
    tick: Optional[int] = None,
    schemas_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validate artifacts for a run (single tick or all ticks).
    
    Returns:
        {ok: bool, validated_ticks: [int], failures: [{tick, artifact_kind, path, errors}]}
    """
    base = Path(artifacts_dir)
    all_failures: List[Dict[str, Any]] = []
    validated_ticks: List[int] = []

    if tick is not None:
        # Single tick
        result = validate_tick(artifacts_dir, run_id, tick, schemas_dir)
        validated_ticks.append(tick)
        for f in result.get("failures", []):
            all_failures.append({**f, "tick": tick})
    else:
        # All ticks: discover from run_index/<run_id>/*.runindex.json
        runindex_dir = base / "run_index" / run_id
        if not runindex_dir.exists():
            return {"ok": False, "validated_ticks": [], "failures": [{"tick": None, "artifact_kind": "RunIndex", "path": str(runindex_dir), "errors": ["Directory not found"]}]}

        tick_files = sorted(runindex_dir.glob("*.runindex.json"))
        for tf in tick_files:
            # Extract tick from filename (000000.runindex.json -> 0)
            try:
                t = int(tf.stem.split(".")[0])
            except ValueError:
                continue
            result = validate_tick(artifacts_dir, run_id, t, schemas_dir)
            validated_ticks.append(t)
            for f in result.get("failures", []):
                all_failures.append({**f, "tick": t})

    # Also validate run-level artifacts (RunHeader, stability)
    run_header_path = base / "runs" / f"{run_id}.runheader.json"
    if run_header_path.exists():
        ok, errs = validate_artifact(str(run_header_path), "runheader.v0", schemas_dir)
        if not ok:
            all_failures.append({"tick": None, "artifact_kind": "RunHeader.v0", "path": str(run_header_path), "errors": errs})

    stability_path = base / "runs" / f"{run_id}.runstability.json"
    if stability_path.exists():
        ok, errs = validate_artifact(str(stability_path), "runstability.v0", schemas_dir)
        if not ok:
            all_failures.append({"tick": None, "artifact_kind": "RunStability.v0", "path": str(stability_path), "errors": errs})

    stability_ref_path = base / "runs" / f"{run_id}.stability_ref.json"
    if stability_ref_path.exists():
        ok, errs = validate_artifact(str(stability_ref_path), "stabilityref.v0", schemas_dir)
        if not ok:
            all_failures.append({"tick": None, "artifact_kind": "StabilityRef.v0", "path": str(stability_ref_path), "errors": errs})

    return {
        "ok": len(all_failures) == 0,
        "validated_ticks": sorted(validated_ticks),
        "failures": all_failures,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Abraxas artifacts against schemas")
    ap.add_argument("--artifacts_dir", required=True, help="Root artifacts directory")
    ap.add_argument("--run_id", required=True, help="Run ID to validate")
    ap.add_argument("--tick", type=int, default=None, help="Specific tick to validate (default: all)")
    ap.add_argument("--schemas_dir", default=None, help="Schemas directory (default: schemas/)")
    ap.add_argument("--json", action="store_true", help="Output as JSON")
    args = ap.parse_args()

    result = validate_run(
        artifacts_dir=args.artifacts_dir,
        run_id=args.run_id,
        tick=args.tick,
        schemas_dir=args.schemas_dir,
    )

    # Deterministic JSON output
    output = json.dumps(result, sort_keys=True, separators=(",", ":"))

    if args.json:
        print(output)
    else:
        if result["ok"]:
            print(f"VALIDATION: PASS")
            print(f"Validated ticks: {result['validated_ticks']}")
        else:
            print(f"VALIDATION: FAIL")
            print(f"Validated ticks: {result['validated_ticks']}")
            print(f"Failures:")
            for f in result["failures"]:
                print(f"  - tick={f.get('tick')}, kind={f['artifact_kind']}, path={f['path']}")
                for e in f.get("errors", []):
                    print(f"      {e}")

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
