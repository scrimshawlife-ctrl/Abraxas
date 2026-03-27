#!/usr/bin/env python3
"""Build deterministic stub taxonomy artifact for Notion closure tracking."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def classify_stub(entry: Dict[str, Any]) -> str:
    stub_type = str(entry.get("stub_type") or "")
    marker = str(entry.get("marker") or "").lower()
    file_path = str(entry.get("file") or "")

    if stub_type == "interface":
        return "intentional_abstract"
    if "abraxas/detectors/" in file_path and "subclasses must implement" in marker:
        return "intentional_abstract"
    if "abraxas/narratives/" in file_path and "subclasses must implement" in marker:
        return "intentional_abstract"
    if "requires " in marker and "abraxas/runes/operators/" in file_path:
        return "policy_block"
    if "strict_execution" in marker and "unimplemented operator" in marker:
        return "implementation_gap"
    if stub_type in {"operator", "not_implemented", "module", "core"}:
        return "implementation_gap"
    return "implementation_gap"


def build_taxonomy(index: Dict[str, Any]) -> Dict[str, Any]:
    stubs = index.get("stubs") if isinstance(index.get("stubs"), list) else []
    classified = []
    counts = {
        "intentional_abstract": 0,
        "implementation_gap": 0,
        "policy_block": 0,
    }
    for raw in stubs:
        if not isinstance(raw, dict):
            continue
        category = classify_stub(raw)
        item = dict(raw)
        item["gap_category"] = category
        classified.append(item)
        counts[category] = counts.get(category, 0) + 1

    return {
        "version": "stub_taxonomy.v0.1",
        "generated_at": "auto",
        "source": "tools/stub_index.json",
        "n_stubs": len(classified),
        "gap_summary": counts,
        "stubs": classified,
        "notes": "Wave 1 taxonomy for Notion closure: intentional_abstract vs implementation_gap vs policy_block.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Build stub taxonomy artifact from tools/stub_index.json")
    ap.add_argument("--index", default="tools/stub_index.json")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    index_path = Path(args.index)
    if not index_path.exists():
        raise SystemExit(f"stub index missing: {index_path}")

    index = json.loads(index_path.read_text(encoding="utf-8"))
    artifact = build_taxonomy(index)

    out_path = Path(args.out) if args.out else Path("docs/artifacts/notion_stub_taxonomy.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[STUB_TAXONOMY] wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
