from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import json
from typing import Iterable, List, Optional, Sequence


@dataclass(frozen=True)
class AuditFileEntry:
    path: str
    commit_sha: str
    blob_hash: str
    classification: str
    timestamp_utc: str


@dataclass(frozen=True)
class AuditContext:
    base_ref: Optional[str]
    head_ref: Optional[str]


GOVERNANCE_FILES = {
    "webpanel/gates.py",
    "webpanel/session_mode.py",
    "webpanel/agency_toggle.py",
    "webpanel/task_router.py",
    "webpanel/burst_dry_run.py",
}


def _load_jsonl(path: Path) -> List[dict]:
    rows: List[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _extract_context(rows: Sequence[dict]) -> AuditContext:
    base_ref = None
    head_ref = None
    for row in rows:
        range_info = row.get("range") if isinstance(row.get("range"), dict) else None
        if base_ref is None:
            range_base = range_info.get("base") if range_info else None
            base_ref = range_base or row.get("base_ref") or row.get("base")
        if head_ref is None:
            range_head = range_info.get("head") if range_info else None
            head_ref = range_head or row.get("head_ref") or row.get("head")
    return AuditContext(base_ref=base_ref, head_ref=head_ref)


def _extract_files(rows: Sequence[dict]) -> List[AuditFileEntry]:
    out: List[AuditFileEntry] = []
    for row in rows:
        commit_sha = row.get("commit_sha") or row.get("commit") or row.get("sha") or ""
        timestamp_utc = row.get("timestamp_utc") or row.get("timestamp") or ""
        commit_info = row.get("commit") if isinstance(row.get("commit"), dict) else None
        if commit_info:
            commit_sha = commit_info.get("sha") or commit_sha
            time_info = commit_info.get("time") if isinstance(commit_info.get("time"), dict) else None
            if time_info:
                timestamp_utc = time_info.get("iso_utc") or timestamp_utc
        files = row.get("files") or []
        if not isinstance(files, list):
            continue
        for file_info in files:
            if not isinstance(file_info, dict):
                continue
            path = str(file_info.get("path") or "")
            blob_hash = str(file_info.get("blob_hash") or file_info.get("blob") or "")
            classification = str(file_info.get("classification") or file_info.get("class") or "")
            out.append(
                AuditFileEntry(
                    path=path,
                    commit_sha=commit_sha,
                    blob_hash=blob_hash,
                    classification=classification,
                    timestamp_utc=timestamp_utc,
                )
            )
    return out


def _should_include(entry: AuditFileEntry, include_governance: bool) -> bool:
    if entry.classification in {"schema", "ir", "models"}:
        return True
    if entry.path.endswith("models.py"):
        return True
    if include_governance and entry.path in GOVERNANCE_FILES:
        return True
    return False


def _promotion_status(path: str) -> str:
    if path.startswith("tests/"):
        return "NON_CANON_EVIDENCE"
    if path.startswith("webpanel/") and ("templates/" in path or path.endswith("app.py")):
        return "CANON_SHADOW_CANDIDATE"
    if "schemas/" in path or "schema/" in path or "ir" in path or path.endswith("models.py"):
        return "PENDING_REVIEW"
    return "PENDING_REVIEW"


def _date_range(entries: Sequence[AuditFileEntry]) -> str:
    stamps = sorted({entry.timestamp_utc for entry in entries if entry.timestamp_utc})
    if not stamps:
        return "unknown"
    if len(stamps) == 1:
        return stamps[0]
    return f"{stamps[0]} -> {stamps[-1]}"


def generate_markdown(
    entries: Sequence[AuditFileEntry],
    context: AuditContext,
) -> str:
    lines = ["# Canon Ledger Append (Diff Audit)"]
    lines.append(f"Date Range (UTC): {_date_range(entries)}")
    lines.append(f"Base: {context.base_ref or 'unknown'}")
    lines.append(f"Head: {context.head_ref or 'unknown'}")
    lines.append("")
    lines.append("## Files")
    if not entries:
        lines.append("(none)")
        return "\n".join(lines) + "\n"

    ordered = sorted(
        entries,
        key=lambda item: (item.timestamp_utc, item.path, item.commit_sha, item.blob_hash),
    )
    for entry in ordered:
        status = _promotion_status(entry.path)
        lines.append(f"- path: {entry.path}")
        lines.append(f"  commit: {entry.commit_sha}")
        lines.append(f"  blob: {entry.blob_hash}")
        lines.append(f"  status: {status}")
    return "\n".join(lines) + "\n"


def build_ledger_from_audit(
    *,
    audit_jsonl: Path,
    include_governance: bool = False,
) -> str:
    rows = _load_jsonl(audit_jsonl)
    context = _extract_context(rows)
    files = _extract_files(rows)
    included = [entry for entry in files if _should_include(entry, include_governance)]
    return generate_markdown(included, context)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build canon ledger append from diff audit JSONL.")
    parser.add_argument("--audit-jsonl", required=True, type=Path)
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--include-governance", action="store_true")
    args = parser.parse_args(argv)

    _ = args.repo
    output = build_ledger_from_audit(
        audit_jsonl=args.audit_jsonl,
        include_governance=bool(args.include_governance),
    )
    args.out.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
