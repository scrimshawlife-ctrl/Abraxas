from __future__ import annotations

from pathlib import Path

from abx.governance.types import DeadPathRecord, LegacySurfaceRecord


SCRIPT_DEPRECATION_CANDIDATES = {
    "scripts/run_frame_assembly.py": "Superseded by repo audit and source-of-truth reports for operator baseline checks.",
    "scripts/run_adapter_audit.py": "Adapter audit is now embedded in repo baseline audit.",
}


LEGACY_SURFACES = [
    LegacySurfaceRecord(
        surface_id="legacy.operator.inspect-validation",
        surface_path="abx/operator_console.py::inspect-validation",
        reason="Standalone validation inspector duplicates proof/closure governance surfaces.",
        status="DEPRECATED_CANDIDATE",
    ),
    LegacySurfaceRecord(
        surface_id="legacy.operator.inspect-rejections",
        surface_path="abx/operator_console.py::inspect-rejections",
        reason="Diagnostic view only; not canonical runtime truth.",
        status="LEGACY",
    ),
]


def _path_references(repo_root: Path, relative_path: str) -> int:
    needle = Path(relative_path).name
    count = 0
    for scan_root in [repo_root / "tests", repo_root / "scripts", repo_root / "abx"]:
        if not scan_root.exists():
            continue
        for file_path in sorted(scan_root.rglob("*.py")):
            text = file_path.read_text(encoding="utf-8")
            if needle in text:
                count += 1
    return count


def build_dead_path_records(repo_root: Path) -> list[DeadPathRecord]:
    rows: list[DeadPathRecord] = []
    for rel_path, reason in sorted(SCRIPT_DEPRECATION_CANDIDATES.items()):
        refs = _path_references(repo_root, rel_path)
        confidence = "high" if refs <= 1 else "medium"
        rows.append(
            DeadPathRecord(
                path=rel_path,
                path_type="script",
                evidence=f"reference_count={refs}; {reason}",
                confidence=confidence,
            )
        )
    return rows


def pruning_audit_report(repo_root: Path) -> dict[str, object]:
    dead_paths = build_dead_path_records(repo_root)
    legacy = sorted(LEGACY_SURFACES, key=lambda x: x.surface_id)
    return {
        "artifactType": "PruningAuditArtifact.v1",
        "artifactId": "pruning-audit-abx",
        "deadPaths": [row.__dict__ for row in dead_paths],
        "legacySurfaces": [row.__dict__ for row in legacy],
        "stagedDeprecations": [row.path for row in dead_paths if row.confidence in {"high", "medium"}],
    }
