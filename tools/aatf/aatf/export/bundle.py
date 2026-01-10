from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List

from ..config import ensure_paths, resolve_paths
from ..provenance import sha256_hex, stable_dumps
from ..storage import append_ledger, list_queue_items, update_queue_state
from .aalmanac import export_aalmanac
from .memetic_weather import export_memetic_weather
from .neon_genie import export_neon_genie
from .rune_proposals import export_rune_proposals

EXPORTERS = {
    "aalmanac": (export_aalmanac, "aalmanac.v0.json"),
    "memetic_weather": (export_memetic_weather, "memetic_weather.v0.json"),
    "neon_genie": (export_neon_genie, "neon_genie.v0.json"),
    "rune_proposals": (export_rune_proposals, "rune_proposal.v0.json"),
}

FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)


def export_bundle(types: List[str], out_path: str | None = None) -> Dict[str, Any]:
    paths = resolve_paths()
    ensure_paths(paths)
    selected = [t for t in types if t in EXPORTERS]
    selected = sorted(selected)

    file_manifest: List[Dict[str, str]] = []
    written_files: List[Path] = []

    for export_type in selected:
        exporter, filename = EXPORTERS[export_type]
        payload = exporter()
        payload_path = paths.exports / filename
        payload_path.write_text(stable_dumps(payload), encoding="utf-8")
        content_hash = sha256_hex(payload_path.read_text(encoding="utf-8"))
        file_manifest.append({"path": filename, "sha256": content_hash})
        written_files.append(payload_path)

    bundle_id = sha256_hex("|".join([entry["sha256"] for entry in file_manifest]))[:16]
    approved_items = [i for i in list_queue_items() if i.get("state") in {"APPROVED", "EXPORTED"}]
    bundle_payload = {
        "bundle_id": bundle_id,
        "created_date": "1970-01-01",
        "included_types": selected,
        "file_manifest": file_manifest,
        "provenance": {"source_ids": [item["source_hash"] for item in approved_items]},
    }

    bundle_path = paths.exports / "export_bundle.v0.json"
    bundle_path.write_text(stable_dumps(bundle_payload), encoding="utf-8")
    written_files.append(bundle_path)

    zip_path = Path(out_path) if out_path else paths.exports / f"bundle_{bundle_id}.zip"
    _write_deterministic_zip(zip_path, written_files, paths.exports)

    for item in approved_items:
        update_queue_state(item["item_id"], {"state": "EXPORTED"})
    append_ledger("EXPORTED", {"bundle_id": bundle_id, "zip_path": str(zip_path)})

    return {"bundle_id": bundle_id, "zip_path": str(zip_path)}


def _write_deterministic_zip(zip_path: Path, files: List[Path], base_dir: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for file_path in sorted(files, key=lambda p: p.name):
            arcname = file_path.relative_to(base_dir).as_posix()
            info = zipfile.ZipInfo(arcname, date_time=FIXED_ZIP_DATE)
            data = file_path.read_bytes()
            zipf.writestr(info, data)
