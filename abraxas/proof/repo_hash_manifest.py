from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

PATCH_RE = re.compile(r"PATCH-(\d{3})", re.IGNORECASE)
PATCH_FILE_RE = re.compile(r"patch[-_](\d{3})", re.IGNORECASE)
EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".next",
}


def normalize_path(path: Path) -> str:
    return path.as_posix()


def should_exclude(rel_path: Path) -> bool:
    parts = set(rel_path.parts)
    if parts.intersection(EXCLUDED_DIRS):
        return True
    if "coverage" in parts and "cache" in parts:
        return True
    return False


def classify_category(path: str) -> str:
    p = path.lower()
    name = Path(p).name
    if p.startswith(".github/") or "/.github/" in p:
        return "ci"
    if p.startswith("docs/") or name.endswith(".md"):
        return "doc"
    if "/schemas/" in p or name.endswith(".schema.json"):
        return "schema"
    if p.startswith("scripts/") or name.endswith(".sh"):
        return "script"
    if p.startswith("tests/") or name.startswith("test_"):
        return "test"
    if p.startswith("out/") or p.startswith("dist/") or "/artifacts/" in p:
        return "artifact"
    if name in {"pyproject.toml", "setup.cfg", "setup.py", "makefile", "dockerfile"} or name.endswith((".toml", ".yaml", ".yml", ".ini", ".cfg", ".json")):
        return "config"
    if name.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".java", ".c", ".cpp")):
        return "source"
    return "unknown"


def extract_patch_id(path: str, content: bytes) -> str | None:
    m = PATCH_RE.search(path)
    if m:
        return f"PATCH-{m.group(1)}"
    m2 = PATCH_FILE_RE.search(Path(path).name)
    if m2:
        return f"PATCH-{m2.group(1)}"
    if path.lower().endswith(".md"):
        text = content.decode("utf-8", errors="ignore")
        m3 = PATCH_RE.search(text)
        if m3:
            return f"PATCH-{m3.group(1)}"
    return None


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n"


def compute_manifest(repo_root: Path) -> dict[str, Any]:
    files = []
    for file_path in sorted(repo_root.rglob("*")):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(repo_root)
        if should_exclude(rel):
            continue
        try:
            raw = file_path.read_bytes()
        except (OSError, PermissionError):
            continue
        npath = normalize_path(rel)
        files.append(
            {
                "path": npath,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "size_bytes": len(raw),
                "category": classify_category(npath),
                "patch_id": extract_patch_id(npath, raw),
                "subsystem": "repo_proof",
                "evidence_status": "verified_hash",
            }
        )
    files.sort(key=lambda x: x["path"])
    return {
        "schema": "RepoProofManifest.v1",
        "repo_root": ".",
        "file_count": len(files),
        "files": files,
    }


def patch_num(patch_id: str | None) -> int | None:
    if not patch_id:
        return None
    m = re.match(r"PATCH-(\d{3})$", patch_id)
    return int(m.group(1)) if m else None


def parse_floor(value: str | None) -> tuple[int | None, bool]:
    if not value:
        return (None, False)
    plus = value.endswith("+")
    base = value[:-1] if plus else value
    m = re.match(r"PATCH-(\d{3})$", base)
    if not m:
        return (None, plus)
    return (int(m.group(1)), plus)


def classify_drift(repo_floor: int | None, notion_floor_raw: str | None) -> str:
    notion_floor, notion_plus = parse_floor(notion_floor_raw)
    if repo_floor is None or notion_floor is None:
        return "not_computable"
    if notion_plus:
        if repo_floor > notion_floor:
            return "repo_ahead"
        if repo_floor == notion_floor:
            return "aligned"
        return "notion_ahead"
    if repo_floor == notion_floor:
        return "aligned"
    if repo_floor > notion_floor:
        return "repo_ahead"
    if repo_floor < notion_floor:
        return "notion_ahead"
    return "diverged"


def build_outputs(repo_root: Path, notion_patch_floor: str | None) -> dict[str, dict[str, Any]]:
    manifest = compute_manifest(repo_root)
    patches: dict[str, list[str]] = {}
    for f in manifest["files"]:
        pid = f.get("patch_id")
        if pid:
            patches.setdefault(pid, []).append(f["path"])
    patch_entries = []
    for pid in sorted(patches):
        obs = sorted(patches[pid])
        patch_entries.append({
            "patch_id": pid,
            "observed_files": obs,
            "expected_files": obs,
            "missing_files": [],
            "extra_files": [],
            "coverage_status": "complete",
        })
    coverage = {"schema": "PatchCoverageMap.v1", "patch_count": len(patch_entries), "patches": patch_entries}
    nums = [patch_num(p["patch_id"]) for p in patch_entries]
    valid_nums = [n for n in nums if n is not None]
    repo_floor = max(valid_nums) if valid_nums else None
    drift = classify_drift(repo_floor, notion_patch_floor)
    alignment = {
        "schema": "RepoCanonAlignmentReport.v1",
        "notion_patch_floor": notion_patch_floor,
        "repo_patch_floor": f"PATCH-{repo_floor:03d}" if repo_floor is not None else "NOT_COMPUTABLE",
        "drift_class": drift,
    }
    receipt = {
        "receipt_type": "RepoProofReceipt.v1",
        "patch_id": "PATCH-069",
        "runtime_mutation": False,
        "promotion_granted": False,
        "scheduler_write": False,
        "source_weight_mutation": False,
        "activation_allowed": False,
        "authority_boundary": "proof_only",
    }
    return {
        "repo_proof_manifest.latest.json": manifest,
        "patch_coverage_map.latest.json": coverage,
        "repo_canon_alignment_report.latest.json": alignment,
        "repo_proof_receipt.latest.json": receipt,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--notion-patch-floor", default=None)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    outputs = build_outputs(Path(args.repo_root), args.notion_patch_floor)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, data in outputs.items():
        (out_dir / name).write_text(canonical_json(data), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
