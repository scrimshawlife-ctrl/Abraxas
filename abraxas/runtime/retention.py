"""
Artifact Retention — Deterministic pruning for Abraxas artifacts.

Keep disk from turning into a cursed landfill—deterministically.

Features:
- RetentionPolicy.v0 (JSON) stored under artifacts_dir/policy/retention.json
- ArtifactPruner that:
  - Prunes by tick count (keep last N)
  - Optionally prunes by byte budget
  - Never deletes manifests (can compact them deterministically)
  - Deterministic ordering for all operations

Usage:
    from abraxas.runtime.retention import ArtifactPruner

    pruner = ArtifactPruner(artifacts_dir)
    policy = pruner.load_policy()
    policy["enabled"] = True
    policy["keep_last_ticks"] = 100
    pruner.save_policy(policy)

    report = pruner.prune_run(run_id)
    print(f"Deleted {len(report.deleted_files)} files ({report.deleted_bytes} bytes)")
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_POLICY: Dict[str, Any] = {
    "schema": "RetentionPolicy.v0",
    # Retention is disabled by default (explicit opt-in required)
    "enabled": False,
    # Keep last N ticks per run_id (by tick number)
    "keep_last_ticks": 200,
    # Optional total byte cap per run_id across artifact files (excluding manifests/policy)
    # Set to None for no limit
    "max_bytes_per_run": None,
    # Do not delete these directories under artifacts root
    "protected_roots": ["manifests", "policy"],
    # Compact manifests by removing records for missing files after prune
    "compact_manifest": True,
}


def _stable_json_write(path: Path, obj: Dict[str, Any]) -> None:
    """Write JSON deterministically (sorted keys, minimal whitespace)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    path.write_text(s, encoding="utf-8")


def _read_json(path: Path) -> Dict[str, Any]:
    """Read JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_tick_from_name(name: str) -> Optional[int]:
    """
    Extract tick from filenames like:
      000123.trendpack.json
      000123.resultspack.json
      000123.runindex.json
      000123.viewpack.json

    Returns None if tick cannot be parsed.
    """
    if "." not in name:
        return None
    head = name.split(".", 1)[0]
    if not head.isdigit():
        return None
    try:
        return int(head)
    except Exception:
        return None


@dataclass(frozen=True)
class PruneReport:
    """Report from a prune operation."""
    run_id: str
    kept_ticks: List[int]
    deleted_files: List[str]
    deleted_bytes: int
    policy: Dict[str, Any]


class ArtifactPruner:
    """
    Deterministic artifact retention for Abraxas artifacts directory.

    - Prunes by tick count and (optionally) byte budget.
    - Never deletes manifests/ or policy/.
    - Can compact per-run manifest after deletions.
    - All operations are deterministic (stable ordering).
    """

    # Known artifact roots emitted by runtime
    ARTIFACT_ROOTS = ["viz", "results", "run_index", "view"]

    def __init__(self, artifacts_dir: str):
        """
        Initialize pruner for an artifacts directory.

        Args:
            artifacts_dir: Path to artifacts root directory
        """
        self.root = Path(artifacts_dir)
        self.policy_path = self.root / "policy" / "retention.json"

    def ensure_policy(self) -> Dict[str, Any]:
        """
        Ensure policy file exists, creating default if needed.

        Returns:
            Current policy dict
        """
        if not self.policy_path.exists():
            _stable_json_write(self.policy_path, dict(DEFAULT_POLICY))
        pol = _read_json(self.policy_path)
        if pol.get("schema") != "RetentionPolicy.v0":
            raise ValueError(f"Expected RetentionPolicy.v0, got {pol.get('schema')}")
        return pol

    def load_policy(self) -> Dict[str, Any]:
        """
        Load retention policy (creates default if not exists).

        Returns:
            Policy dict with schema RetentionPolicy.v0
        """
        return self.ensure_policy()

    def save_policy(self, policy: Dict[str, Any]) -> None:
        """
        Save retention policy.

        Args:
            policy: Policy dict (must have schema RetentionPolicy.v0)
        """
        if policy.get("schema") != "RetentionPolicy.v0":
            raise ValueError("policy must have schema RetentionPolicy.v0")
        _stable_json_write(self.policy_path, policy)

    def discover_run_ids(self) -> List[str]:
        """
        Discover all run_ids that have artifacts.

        Returns:
            Sorted list of run_id strings
        """
        run_ids = set()
        for root_name in self.ARTIFACT_ROOTS:
            root_path = self.root / root_name
            if root_path.exists():
                for child in root_path.iterdir():
                    if child.is_dir():
                        run_ids.add(child.name)
        return sorted(run_ids)

    def prune_run(
        self,
        run_id: str,
        policy: Optional[Dict[str, Any]] = None,
    ) -> PruneReport:
        """
        Prune artifacts for a specific run_id according to policy.

        Args:
            run_id: Run identifier to prune
            policy: Optional policy override (uses loaded policy if None)

        Returns:
            PruneReport with details of what was kept/deleted
        """
        policy = policy or self.load_policy()

        # If retention disabled, return empty report
        if not policy.get("enabled", False):
            return PruneReport(
                run_id=run_id,
                kept_ticks=[],
                deleted_files=[],
                deleted_bytes=0,
                policy=policy,
            )

        keep_last = int(policy.get("keep_last_ticks", 200))
        max_bytes = policy.get("max_bytes_per_run")
        protected = set(policy.get("protected_roots", ["manifests", "policy"]))
        compact = bool(policy.get("compact_manifest", True))

        # Discover tick files across known artifact roots
        # Filenames are authoritative for tick numbering: <tick>.ext with tick as zero-padded int
        files: List[Tuple[int, Path]] = []

        for r in self.ARTIFACT_ROOTS:
            base = self.root / r / run_id
            if not base.exists():
                continue
            for p in sorted(base.glob("*")):
                if not p.is_file():
                    continue
                tick = _parse_tick_from_name(p.name)
                if tick is None:
                    continue
                files.append((tick, p))

        # Determine ticks present
        ticks = sorted({t for t, _ in files})
        if not ticks:
            return PruneReport(
                run_id=run_id,
                kept_ticks=[],
                deleted_files=[],
                deleted_bytes=0,
                policy=policy,
            )

        # Keep set: last N ticks by tick number
        keep_set = set(ticks[-keep_last:]) if keep_last > 0 else set()

        # Candidate deletions: files from ticks not in keep set
        to_delete: List[Path] = []
        for t, p in files:
            if t not in keep_set:
                to_delete.append(p)

        # Optional byte-budget pruning within kept set
        # Delete oldest kept files first until under budget
        if max_bytes is not None:
            max_bytes_int = int(max_bytes)
            kept_files = [p for (t, p) in files if t in keep_set]
            # Sort by tick (ascending) then name for determinism
            kept_files_sorted = sorted(
                kept_files,
                key=lambda x: (_parse_tick_from_name(x.name) or 0, x.name),
            )

            # Calculate total size
            total = sum(p.stat().st_size for p in kept_files_sorted if p.exists())

            # Delete oldest kept files until under budget
            for p in kept_files_sorted:
                if total <= max_bytes_int:
                    break
                # Skip protected roots (shouldn't happen but be defensive)
                if any(part in protected for part in p.parts):
                    continue
                sz = p.stat().st_size if p.exists() else 0
                to_delete.append(p)
                total -= sz
                # Also remove from keep_set tracking
                tick = _parse_tick_from_name(p.name)
                if tick is not None:
                    # Check if all files for this tick are being deleted
                    pass  # Keep set is by tick, not by file

        # Execute deletions (deterministic ordering)
        deleted_files: List[str] = []
        deleted_bytes = 0

        for p in sorted(set(to_delete), key=lambda x: str(x)):
            # Safety: never delete protected roots
            if any(part in protected for part in p.parts):
                continue
            if p.exists() and p.is_file():
                deleted_bytes += p.stat().st_size
                deleted_files.append(str(p))
                p.unlink()

        # Compact manifest if requested
        if compact:
            self._compact_manifest(run_id=run_id)

        # Recalculate kept ticks after deletions
        remaining_ticks = set()
        for r in self.ARTIFACT_ROOTS:
            base = self.root / r / run_id
            if not base.exists():
                continue
            for p in base.glob("*"):
                if p.is_file():
                    tick = _parse_tick_from_name(p.name)
                    if tick is not None:
                        remaining_ticks.add(tick)

        kept_ticks = sorted(remaining_ticks)

        return PruneReport(
            run_id=run_id,
            kept_ticks=kept_ticks,
            deleted_files=deleted_files,
            deleted_bytes=deleted_bytes,
            policy=policy,
        )

    def prune_all(self, policy: Optional[Dict[str, Any]] = None) -> List[PruneReport]:
        """
        Prune all discovered run_ids according to policy.

        Args:
            policy: Optional policy override

        Returns:
            List of PruneReport for each run_id
        """
        policy = policy or self.load_policy()
        reports = []
        for run_id in self.discover_run_ids():
            reports.append(self.prune_run(run_id, policy=policy))
        return reports

    def _compact_manifest(self, run_id: str) -> None:
        """
        Remove manifest records whose path no longer exists.

        Deterministic: stable sort by (tick, kind, schema, path).

        Args:
            run_id: Run identifier
        """
        mpath = self.root / "manifests" / f"{run_id}.manifest.json"
        if not mpath.exists():
            return

        cur = _read_json(mpath)
        if cur.get("schema") != "Manifest.v0":
            return

        recs = cur.get("records", []) or []

        # Keep only records for existing files
        kept = []
        for r in recs:
            p = r.get("path")
            if isinstance(p, str) and Path(p).exists():
                kept.append(r)

        # Deterministic sort
        kept = sorted(
            kept,
            key=lambda e: (
                int(e.get("tick", 0)),
                str(e.get("kind", "")),
                str(e.get("schema", "")),
                str(e.get("path", "")),
            ),
        )

        cur["records"] = kept
        _stable_json_write(mpath, cur)

    def get_run_stats(self, run_id: str) -> Dict[str, Any]:
        """
        Get statistics for a run's artifacts.

        Args:
            run_id: Run identifier

        Returns:
            Dict with tick_count, file_count, total_bytes
        """
        files: List[Tuple[int, Path]] = []
        for r in self.ARTIFACT_ROOTS:
            base = self.root / r / run_id
            if not base.exists():
                continue
            for p in base.glob("*"):
                if p.is_file():
                    tick = _parse_tick_from_name(p.name)
                    if tick is not None:
                        files.append((tick, p))

        ticks = sorted({t for t, _ in files})
        total_bytes = sum(p.stat().st_size for _, p in files if p.exists())

        return {
            "run_id": run_id,
            "tick_count": len(ticks),
            "file_count": len(files),
            "total_bytes": total_bytes,
            "oldest_tick": min(ticks) if ticks else None,
            "newest_tick": max(ticks) if ticks else None,
        }


__all__ = [
    "DEFAULT_POLICY",
    "PruneReport",
    "ArtifactPruner",
]
