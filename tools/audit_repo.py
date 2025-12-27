import hashlib
import json
import os
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from collections import defaultdict

from shared.policy import load_policy

ROOT = Path(__file__).resolve().parents[1]

PY_IMPORT = re.compile(
    r"^\s*(from\s+([a-zA-Z0-9_\.]+)\s+import|import\s+([a-zA-Z0-9_\.]+))"
)
TS_IMPORT = re.compile(
    r"^\s*import\s+.*from\s+['\"]([^'\"]+)['\"]|^\s*require\(['\"]([^'\"]+)['\"]\)"
)
PY_INVOKE = re.compile(r"\bkernel\.invoke\(|\binvoke\(", re.I)
TS_INVOKE = re.compile(
    r"\bkernelInvoke\(|\binvokeRune\(|\b/abx/invoke\b|\brune_id\b", re.I
)
SIDE_EFFECT_PATTERNS = [
    (
        "filesystem_write",
        re.compile(
            r"\b(open\(|write\(|os\.remove|shutil\.rmtree|Path\(.+\)\.write_)",
            re.I,
        ),
    ),
    (
        "network_call",
        re.compile(
            r"\b(requests\.(get|post|put|delete)|httpx\.|fetch\(|axios\.|node-fetch)",
            re.I,
        ),
    ),
    (
        "process_exec",
        re.compile(r"\b(subprocess\.|os\.system\(|exec\(|spawn\(|child_process)", re.I),
    ),
]
DETECTOR_HINT = re.compile(r"(detect|watch|monitor|guard|heal|self[_-]?heal)", re.I)

FORBIDDEN_ACTUATION = [
    ("systemctl", re.compile(r"\bsystemctl\b", re.I)),
    ("subprocess_call", re.compile(r"\bsubprocess\.(check_call|call|run)\b", re.I)),
    ("os_system", re.compile(r"\bos\.system\(", re.I)),
    ("rm_rf", re.compile(r"\brm\s+-rf\b", re.I)),
    ("shutil_rmtree", re.compile(r"\bshutil\.rmtree\b", re.I)),
]

ACTUATION_ALLOWLIST = {
    "infra/actuator.py",
}


def boundary_of(relpath: str, boundaries: List[str]) -> str:
    rel = relpath.replace("\\", "/")
    top = rel.split("/", 1)[0]
    return top if top in boundaries else "root"


def import_target_boundary(sym: str, boundaries: List[str]) -> str:
    if not sym:
        return "unknown"
    if sym.startswith("."):
        return "relative"
    head = sym.split(".", 1)[0].strip()
    if head in boundaries:
        return head
    for boundary in boundaries:
        if f"/{boundary}/" in sym or sym.startswith(f"{boundary}/"):
            return boundary
    return "external"


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_commit() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT)
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def git_dirty() -> bool:
    try:
        out = (
            subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)
            .decode()
            .strip()
        )
        return len(out) > 0
    except Exception:
        return True


def list_files():
    excludes = {".git", "node_modules", "dist", "build", ".next", ".venv", "__pycache__"}
    for path in ROOT.rglob("*"):
        if any(part in excludes for part in path.parts):
            continue
        if path.is_file() and path.suffix in {".py", ".ts", ".tsx", ".js"}:
            yield path


def load_registry():
    registry_path = ROOT / "registry" / "abx_rune_registry.json"
    if not registry_path.exists():
        return None, None
    return json.loads(registry_path.read_text(encoding="utf-8")), sha256_file(
        registry_path
    )


def count_untyped_registry_inputs(registry: dict) -> list:
    """Flag runes that still use old-format string-list inputs."""
    out = []
    if not registry:
        return out
    for r in (registry.get("runes", []) or []):
        rid = r.get("rune_id")
        ins = r.get("inputs")
        if isinstance(ins, list) and ins and isinstance(ins[0], str):
            out.append({"rune_id": rid, "reason": "inputs_untyped_string_list"})
    return out


def find_imports(path: Path):
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    out = []
    for index, line in enumerate(lines, start=1):
        if path.suffix == ".py":
            match = PY_IMPORT.match(line)
            if match:
                out.append((index, (match.group(2) or match.group(3) or "").strip()))
        else:
            match = TS_IMPORT.match(line)
            if match:
                out.append((index, (match.group(1) or match.group(2) or "").strip()))
    return out


def find_side_effects(path: Path):
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    hits = []
    for index, line in enumerate(lines, start=1):
        for kind, rx in SIDE_EFFECT_PATTERNS:
            if rx.search(line):
                hits.append((index, kind, line.strip()[:240]))
    return hits


def likely_detector_file(path: Path) -> bool:
    return bool(DETECTOR_HINT.search(str(path)))


def find_forbidden_actuation(path: Path) -> List[tuple[int, str, str]]:
    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    if rel in ACTUATION_ALLOWLIST:
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    hits = []
    for index, line in enumerate(lines, start=1):
        for kind, rx in FORBIDDEN_ACTUATION:
            if rx.search(line):
                hits.append((index, kind, line.strip()[:240]))
    return hits


def audit():
    policy_doc = load_policy()
    coupling_policy = policy_doc.get("coupling", {}) or {}
    boundaries = coupling_policy.get("boundaries", []) or []
    allowed_edges = coupling_policy.get("allowed_cross_imports", []) or []

    registry, registry_sha = load_registry()
    untyped_inputs = count_untyped_registry_inputs(registry)

    hidden_coupling = []
    side_effects = []
    detector_purity = []
    forbidden_actuation = []
    cross_boundary = []
    coupling_graph: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    invoke_hits = 0
    direct_import_hits = 0

    for path in list_files():
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        src_boundary = boundary_of(rel, boundaries)

        imports = find_imports(path)
        # Hidden coupling heuristic:
        # - If server/client/scheduler directly imports domain modules without kernel/rune mediation,
        #   flag as potential bypass (youll tighten rules later).
        for line, sym in imports:
            if sym.startswith(("abraxas.", "abx.", "scheduler.", "server.")):
                # allow kernel/rune paths later; for now record everything & filter downstream
                hidden_coupling.append(
                    {
                        "kind": "direct_import",
                        "file": str(path.relative_to(ROOT)),
                        "line": line,
                        "symbol": sym,
                        "recommendation": (
                            "Route cross-module calls through kernel.invoke(rune_id, ...) "
                            "and rune registry."
                        ),
                    }
                )
                direct_import_hits += 1

            tgt_boundary = import_target_boundary(sym, boundaries)
            if tgt_boundary not in {"unknown", "external", "relative"}:
                coupling_graph[src_boundary].append(
                    {
                        "to": tgt_boundary,
                        "file": rel,
                        "line": line,
                        "symbol": sym,
                    }
                )

            if (
                src_boundary != "root"
                and tgt_boundary in boundaries
                and tgt_boundary != src_boundary
            ):
                allowed = any(
                    edge.get("from") == src_boundary
                    and edge.get("to") == tgt_boundary
                    for edge in allowed_edges
                )
                if not allowed:
                    cross_boundary.append(
                        {
                            "kind": "cross_boundary_import",
                            "from": src_boundary,
                            "to": tgt_boundary,
                            "file": rel,
                            "line": line,
                            "symbol": sym,
                            "recommendation": (
                                "Replace cross-boundary imports with "
                                "kernel.invoke(rune_id, ...) + rune registry."
                            ),
                        }
                    )

        effects = find_side_effects(path)
        for line, kind, snippet in effects:
            side_effects.append(
                {
                    "kind": kind,
                    "file": str(path.relative_to(ROOT)),
                    "line": line,
                    "symbol": snippet,
                    "risk": (
                        "Potential side effect. Requires governance/actuator separation "
                        "if detector-adjacent."
                    ),
                    "recommendation": (
                        "If detector path: convert to advisory + governed actuator; "
                        "otherwise log provenance + ensure deterministic inputs."
                    ),
                }
            )

        if likely_detector_file(path):
            for line, kind, snippet in effects:
                detector_purity.append(
                    {
                        "file": str(path.relative_to(ROOT)),
                        "line": line,
                        "symbol": snippet,
                        "violation": (
                            f"Detector-adjacent file contains side effect pattern: {kind}"
                        ),
                        "recommendation": (
                            "Detectors must annotate/log only. Move side effects behind "
                            "governance-gated actuator."
                        ),
                    }
                )

        forbidden = find_forbidden_actuation(path)
        for line, kind, snippet in forbidden:
            forbidden_actuation.append(
                {
                    "kind": kind,
                    "file": str(path.relative_to(ROOT)),
                    "line": line,
                    "symbol": snippet,
                    "recommendation": (
                        "Move all actuation into infra/actuator.py behind governance gate."
                    ),
                }
            )

        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if path.suffix == ".py" and PY_INVOKE.search(text):
                invoke_hits += 1
            if path.suffix in {".ts", ".tsx", ".js"} and TS_INVOKE.search(text):
                invoke_hits += 1
        except Exception:
            pass

    # Rune coverage (heuristic): count occurrences of invoke/rune_id usage
    rune_coverage_pct = 0.0
    if registry:
        rune_ids = [r["rune_id"] for r in registry.get("runes", [])]
        total = len(rune_ids)
        used = 0
        corpus = "\n".join(
            (ROOT / folder).read_text(encoding="utf-8", errors="ignore")
            for folder in ["server"]
            if (ROOT / folder).exists()
        )
        # above is intentionally light; youll expand to full scan later
        for rune_id in rune_ids:
            if rune_id in corpus:
                used += 1
        rune_coverage_pct = (used / total * 100.0) if total else 0.0

    denom = float(invoke_hits + direct_import_hits) or 1.0
    rune_invoke_ratio = float(invoke_hits) / denom

    report = {
        "schema_version": "0.1",
        "name": "AbraxasCanonAuditReport",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repo": {
            "url": "scrimshawlife-ctrl/Abraxas",
            "commit": git_commit(),
            "dirty": git_dirty(),
        },
        "runtime_fingerprint": {
            "python": platform.python_version(),
            "node": os.getenv("NODE_VERSION", "unknown"),
            "platform": platform.platform(),
        },
        "canon_targets": {
            "seed_enforced": False,
            "provenance_embedded": False,
            "abx_runes_only_coupling": False,
            "detector_purity": False,
            "governance_gates": False,
            "aalmanac_append_only": False,
            "ipo_incremental_patch_only": False,
            "stabilization_window": False,
        },
        "scores": {
            "rune_coverage_pct": rune_coverage_pct,
            "rune_invoke_ratio": rune_invoke_ratio,
            "untyped_rune_inputs_count": len(untyped_inputs),
            "hidden_coupling_count": len(hidden_coupling),
            "side_effect_count": len(side_effects),
            "governance_bypass_count": 0,
            "detector_purity_violations": len(detector_purity),
            "forbidden_actuation_count": len(forbidden_actuation),
            "cross_boundary_import_count": len(cross_boundary),
        },
        "findings": {
            "untyped_rune_inputs": untyped_inputs[:500],
            "hidden_coupling": hidden_coupling[:500],
            "side_effects": side_effects[:500],
            "governance": [],
            "detector_purity": detector_purity[:500],
            "forbidden_actuation": forbidden_actuation[:500],
            "cross_boundary_imports": cross_boundary[:500],
            "coupling_graph": dict(coupling_graph),
            "stabilization_window": [],
            "ipo_policy": [],
        },
        "provenance_bundle": {
            "config_sha256": sha256_bytes(b"default"),
            "report_sha256": "PENDING",
            "inputs": {
                "registry_sha256": registry_sha or "missing",
                "schema_sha256": "add docs/AUDIT_REPORT_SCHEMA.json and hash it here",
            },
        },
    }

    report_bytes = json.dumps(report, sort_keys=True).encode("utf-8")
    report["provenance_bundle"]["report_sha256"] = sha256_bytes(report_bytes)
    return report


if __name__ == "__main__":
    output = audit()
    output_path = ROOT / "data" / "audit_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(str(output_path))
