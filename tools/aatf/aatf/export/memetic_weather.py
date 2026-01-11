from __future__ import annotations

from typing import Any, Dict, List

from ..provenance import sha256_hex
from ..storage import list_queue_items


def export_memetic_weather() -> Dict[str, Any]:
    motifs: List[Dict[str, Any]] = []
    evidence: List[Dict[str, Any]] = []
    emergent_terms: List[str] = []

    for item in [i for i in list_queue_items() if i.get("state") in {"APPROVED", "EXPORTED"}]:
        motifs.append(
            {
                "handle": f"signal_{item['item_id'][:8]}",
                "description": "approved signal",
                "velocity": 0.4,
                "volatility": 0.2,
                "polarity": 0.0,
            }
        )
        evidence.append({"source_id": item["source_hash"], "title": item["source_path"], "url": None})
        emergent_terms.append(sha256_hex(f"aalmanac:{item['item_id']}")[:16])

    return {
        "report_id": sha256_hex("memetic_weather")[:16],
        "date": "1970-01-01",
        "regions": ["los_angeles"],
        "motifs": motifs,
        "emergent_terms": emergent_terms,
        "evidence": evidence,
    }
