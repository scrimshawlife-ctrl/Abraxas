from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .provenance import sha256_hex, stable_json_dumps


CSV_NEWLINE = "\n"


def _hash_bytes(data: bytes) -> str:
    return sha256_hex(data)


def _hash_file(path: Path) -> str:
    return _hash_bytes(path.read_bytes())


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    _write_text(path, stable_json_dumps(payload) + "\n")


def _write_csv(path: Path, headers: List[str], rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, lineterminator=CSV_NEWLINE)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in headers})


def _sorted_high_tap(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(rows, key=lambda r: (-float(r.get("tap", 0.0)), str(r.get("token", ""))))


def _sorted_sas(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(rows, key=lambda r: (-float(r.get("sas", 0.0)), str(r.get("sub", ""))))


def _sorted_hits(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        rows,
        key=lambda r: (
            str(r.get("sub", "")),
            str(r.get("token", "")),
            str(r.get("source", "")),
            str(r.get("item_id", "")),
        ),
    )


def _lane_counts(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {"core": 0, "canary": 0}
    for r in rows:
        lane = str(r.get("lane", "core"))
        if lane in counts:
            counts[lane] += 1
    return counts


def build_export_pack(
    outdir: Path,
    report: Dict[str, Any],
    tier: str,
    safe_export: bool,
    include_urls: bool,
) -> Dict[str, Any]:
    tier_norm = (tier or "psychonaut").lower()
    pack_dir = outdir / f"pack_{tier_norm}"
    pack_dir.mkdir(parents=True, exist_ok=True)

    daily_report_path = pack_dir / "daily_report.json"
    _write_json(daily_report_path, report)

    tables_dir = pack_dir / "tables"
    diagnostics_dir = pack_dir / "diagnostics"

    tap_rows = _sorted_high_tap(report.get("high_tap_tokens", []))
    tap_headers = ["token", "tap", "letter_entropy", "length", "unique_letters"]
    _write_csv(tables_dir / "tap_top.csv", tap_headers, tap_rows)

    sas_rows = report.get("sas", {}).get("rows", [])
    if tier_norm in {"academic", "enterprise"}:
        sas_headers = ["sub", "sas", "mentions", "sources_count", "events_count", "lane"]
        _write_csv(tables_dir / "sas.csv", sas_headers, _sorted_sas(sas_rows))

    hits_rows = report.get("verified_sub_anagrams", [])
    if tier_norm in {"academic", "enterprise"}:
        hits_headers = ["sub", "token", "lane", "source", "item_id"]
        _write_csv(tables_dir / "sub_anagrams.csv", hits_headers, _sorted_hits(hits_rows))

    if tier_norm == "enterprise":
        promotions = report.get("enterprise_diagnostics", {}).get("promotion", {})
        pfdi_alerts = report.get("pfdi_alerts", [])
        _write_json(diagnostics_dir / "promotions.json", promotions)
        _write_json(diagnostics_dir / "pfdi_alerts.json", {"alerts": pfdi_alerts})

        index = {
            "date": report.get("date"),
            "run_id": report.get("run_id"),
            "key_fingerprint": report.get("key_fingerprint"),
            "counts": report.get("stats", {}),
            "top_tap": tap_rows[:10],
            "top_sas": _sorted_sas(sas_rows)[:10],
            "lane_counts": _lane_counts(hits_rows),
            "alerts": {"pfdi": len(pfdi_alerts)},
            "links": {
                "sas_csv": "tables/sas.csv",
                "tap_csv": "tables/tap_top.csv",
                "sub_anagrams_csv": "tables/sub_anagrams.csv",
                "promotions_json": "diagnostics/promotions.json",
                "pfdi_alerts_json": "diagnostics/pfdi_alerts.json",
            },
        }
        _write_json(pack_dir / "index.json", index)

    manifest = {
        "tier": tier_norm,
        "safe_export": bool(safe_export),
        "include_urls": bool(include_urls),
        "schema_versions": report.get("schema_versions", {}),
        "counts": report.get("stats", {}),
        "key_fingerprint": report.get("key_fingerprint"),
        "files": {},
    }
    file_hashes = {}
    for path in sorted(pack_dir.rglob("*")):
        if path.is_file():
            rel = path.relative_to(pack_dir).as_posix()
            if rel == "manifest.json":
                continue
            file_hashes[rel] = _hash_file(path)

    manifest["files"] = file_hashes
    manifest_json = stable_json_dumps(manifest)
    manifest_hash = _hash_bytes((manifest_json + "\n").encode("utf-8"))
    manifest["manifest_sha256"] = manifest_hash
    _write_json(pack_dir / "manifest.json", manifest)

    pack_hash = _hash_bytes(stable_json_dumps(file_hashes).encode("utf-8"))
    return {
        "pack_dir": str(pack_dir),
        "pack_sha256": pack_hash,
        "manifest_sha256": manifest_hash,
        "files": file_hashes,
    }
