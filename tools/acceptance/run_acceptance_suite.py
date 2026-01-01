from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# -----------------------------
# Deterministic helpers (stdlib)
# -----------------------------

# Ensure repo root is on sys.path when executed as a file path.
# (Needed so `import tools.acceptance...` works under `python tools/acceptance/run_acceptance_suite.py`.)
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(obj: Any) -> str:
    # Canonical encoding: stable ordering, no whitespace, ASCII escapes.
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def write_status(out_dir: Path, status: Dict[str, Any]) -> None:
    target = out_dir / "acceptance" / "acceptance_status_v1.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(status, indent=2, sort_keys=True), encoding="utf-8")


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    details: str


# Hard gates are the release gates. If any of these fail, overall.ok is false.
HARD_GATES = {
    "A1_JSON_PARSE",
    "A2_LEDGER_HASH_CHAIN",
}


def _extract_created_at(obj: Any) -> Optional[str]:
    if not isinstance(obj, dict):
        return None
    for k in ("created_at", "createdAt", "timestamp"):
        v = obj.get(k)
        if isinstance(v, str) and len(v) >= 10:
            return v
    return None


def _iter_artifact_files(out_dir: Path) -> List[Path]:
    # Acceptance reads only artifacts from out/. Exclude its own output folder.
    if not out_dir.exists():
        return []
    files: List[Path] = []
    for p in out_dir.glob("**/*"):
        if not p.is_file():
            continue
        rel = p.relative_to(out_dir)
        if rel.parts and rel.parts[0] == "acceptance":
            continue
        if p.suffix not in (".json", ".jsonl"):
            continue
        files.append(p)
    files.sort(key=lambda x: str(x.relative_to(out_dir)))
    return files


def _diff_objects(before: Any, after: Any, pointer: str = "") -> List[Dict[str, Any]]:
    # Deterministic structural diff using JSON Pointer-like paths.
    if before == after:
        return []
    if isinstance(before, dict) and isinstance(after, dict):
        changes: List[Dict[str, Any]] = []
        keys = sorted(set(before.keys()) | set(after.keys()))
        for k in keys:
            bp = before.get(k, None)
            ap = after.get(k, None)
            next_ptr = f"{pointer}/{k}"
            if k not in before:
                changes.append({"pointer": next_ptr, "before": None, "after": ap})
            elif k not in after:
                changes.append({"pointer": next_ptr, "before": bp, "after": None})
            else:
                changes.extend(_diff_objects(bp, ap, next_ptr))
        return changes
    if isinstance(before, list) and isinstance(after, list):
        changes = []
        n = max(len(before), len(after))
        for i in range(n):
            next_ptr = f"{pointer}/{i}"
            if i >= len(before):
                changes.append({"pointer": next_ptr, "before": None, "after": after[i]})
            elif i >= len(after):
                changes.append({"pointer": next_ptr, "before": before[i], "after": None})
            else:
                changes.extend(_diff_objects(before[i], after[i], next_ptr))
        return changes
    return [{"pointer": pointer or "/", "before": before, "after": after}]


def _validate_hash_chain(
    rel_path: str,
    records: List[Dict[str, Any]],
) -> Tuple[bool, List[str], List[Dict[str, Any]]]:
    """
    Validate prev_hash/step_hash chain for a JSONL ledger.

    Expected behavior mirrors `abraxas.core.provenance.hash_canonical_json`:
    step_hash == sha256(canonical_json(entry_without_step_hash)).
    """
    errors: List[str] = []
    changes: List[Dict[str, Any]] = []

    # If it doesn't look like a hash-chained ledger, do nothing.
    any_chain = any(isinstance(r, dict) and "prev_hash" in r and "step_hash" in r for r in records)
    if not any_chain:
        return True, errors, changes

    prev = "genesis"
    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            errors.append(f"{rel_path}: record {i} is not an object")
            continue

        if "prev_hash" not in rec or "step_hash" not in rec:
            errors.append(f"{rel_path}: record {i} missing prev_hash/step_hash")
            changes.append(
                {
                    "pointer": f"/{rel_path}/{i}",
                    "before": {"has_prev_hash": "prev_hash" in rec, "has_step_hash": "step_hash" in rec},
                    "after": {"has_prev_hash": True, "has_step_hash": True},
                }
            )
            continue

        if rec.get("prev_hash") != prev:
            errors.append(f"{rel_path}: record {i} prev_hash mismatch")
            changes.append(
                {
                    "pointer": f"/{rel_path}/{i}/prev_hash",
                    "before": rec.get("prev_hash"),
                    "after": prev,
                }
            )

        entry = {k: v for k, v in rec.items() if k != "step_hash"}
        expected = sha256(canonical_json(entry))
        if rec.get("step_hash") != expected:
            errors.append(f"{rel_path}: record {i} step_hash mismatch")
            changes.append(
                {
                    "pointer": f"/{rel_path}/{i}/step_hash",
                    "before": rec.get("step_hash"),
                    "after": expected,
                }
            )

        prev = rec.get("step_hash") or prev

    return len(errors) == 0, errors, changes


def run(out_dir: Path) -> int:
    files = _iter_artifact_files(out_dir)

    envelopes: List[Dict[str, Any]] = []
    parse_errors: List[str] = []
    chain_errors: List[str] = []
    drift_changes: List[Dict[str, Any]] = []

    for p in files:
        rel = str(p.relative_to(out_dir))
        text = p.read_text(encoding="utf-8")
        created_min: Optional[str] = None
        created_max: Optional[str] = None

        if p.suffix == ".jsonl":
            records: List[Dict[str, Any]] = []
            for i, line in enumerate(text.splitlines()):
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except Exception as e:
                    parse_errors.append(f"{rel}: line {i + 1}: {e}")
                    continue
                if isinstance(obj, dict):
                    records.append(obj)
                    t = _extract_created_at(obj)
                    if t is not None:
                        created_min = t if created_min is None else min(created_min, t)
                        created_max = t if created_max is None else max(created_max, t)
                else:
                    # Still count it, but record parse error for non-object records.
                    parse_errors.append(f"{rel}: line {i + 1}: expected object, got {type(obj).__name__}")

            ok, errs, changes = _validate_hash_chain(rel, records)
            if not ok:
                chain_errors.extend(errs)
                drift_changes.extend(changes)

            envelopes.append(
                {
                    "path": rel,
                    "created_at": created_min,
                    "record_count": len(records),
                    "sha256": sha256(text),
                    "kind": "jsonl",
                    "window": {"start": created_min, "end": created_max},
                }
            )

        elif p.suffix == ".json":
            try:
                obj = json.loads(text) if text.strip() else None
            except Exception as e:
                parse_errors.append(f"{rel}: {e}")
                obj = None
            t = _extract_created_at(obj)
            envelopes.append(
                {
                    "path": rel,
                    "created_at": t,
                    "sha256": sha256(text),
                    "kind": "json",
                }
            )

        else:
            # Should not happen due to filtering.
            continue

    # Checks
    results: List[CheckResult] = []

    results.append(
        CheckResult(
            name="A1_JSON_PARSE",
            ok=len(parse_errors) == 0,
            details=(
                f"Parsed {len(files)} artifact files (json/jsonl)."
                if len(parse_errors) == 0
                else f"JSON parse errors: {len(parse_errors)} (showing up to 5): {parse_errors[:5]}"
            ),
        )
    )

    results.append(
        CheckResult(
            name="A2_LEDGER_HASH_CHAIN",
            ok=len(chain_errors) == 0,
            details=(
                "Verified hash chains where present."
                if len(chain_errors) == 0
                else f"Ledger hash-chain errors: {len(chain_errors)} (showing up to 5): {chain_errors[:5]}"
            ),
        )
    )

    # Build acceptance status capsule (UI-friendly)
    created: List[str] = []
    for env in envelopes:
        t = env.get("created_at") or env.get("createdAt")
        if isinstance(t, str) and len(t) >= 10:
            created.append(t)
    created.sort()

    failures_names = [r.name for r in results if (not r.ok and r.name in HARD_GATES)]
    status: Dict[str, Any] = {
        "schema_version": "1.0.0",
        "created_at": now_iso(),
        "run_window": {
            "artifact_count": len(envelopes),
            "start_created_at": created[0] if created else None,
            "end_created_at": created[-1] if created else None,
        },
        "hard_gates": sorted(list(HARD_GATES)),
        "results": [{"name": r.name, "ok": r.ok, "details": r.details} for r in results],
        "overall": {"ok": len(failures_names) == 0, "failures": failures_names},
    }
    write_status(out_dir, status)

    if failures_names:
        # Optional: emit drift artifact for UI + debugging (artifact-only)
        try:
            if len(envelopes) >= 2:
                drift_changes.extend(_diff_objects(envelopes[0], envelopes[-1]))
        except Exception:
            pass
        try:
            from tools.acceptance.emit_drift_on_failure import emit

            emit(out_dir, envelopes, drift_changes)
        except Exception:
            pass

    return 0 if len(failures_names) == 0 else 1


def main() -> None:
    ap = argparse.ArgumentParser(description="Run Abraxas Acceptance Suite (artifact-only)")
    ap.add_argument("--out", default="out", help="Artifact output directory (default: out)")
    args = ap.parse_args()

    out_dir = Path(args.out)
    raise SystemExit(run(out_dir))


if __name__ == "__main__":
    main()

