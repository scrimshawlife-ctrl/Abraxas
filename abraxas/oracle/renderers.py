from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
import json


@dataclass(frozen=True)
class Rendered:
    markdown: str


def _json_block(obj: Any) -> str:
    return "```json\n" + json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n```"


def _iter_domains(sig: Dict[str, Any]) -> List[str]:
    vectors = ((sig.get("oracle_signal_v2") or {}).get("vectors") or {})
    if not isinstance(vectors, dict):
        return []
    return sorted([k for k in vectors.keys() if isinstance(k, str)])


def render_from_signal_v2(sig: Dict[str, Any], *, mode: str) -> Rendered:
    """
    Deterministic renderer for oracle_signal_v2.

    Modes:
      - analyst: debug-focused, includes the full signal as JSON.
      - oracle: compact domain/subdomain listing.
      - ritual: symbolic stub.
    """

    root = sig.get("oracle_signal_v2") if isinstance(sig, dict) else None
    if not isinstance(root, dict):
        raise ValueError("signal must include 'oracle_signal_v2' object")
    meta = root.get("meta") if isinstance(root.get("meta"), dict) else {}
    slice_hash = meta.get("slice_hash", "")
    bundle_id = root.get("bundle_id")

    if mode == "analyst":
        md = "\n".join(
            [
                "# Oracle (Analyst)",
                "",
                f"- bundle_id: `{bundle_id}`" if bundle_id else "- bundle_id: `null`",
                f"- slice_hash: `{slice_hash}`",
                "",
                "## signal_v2",
                "",
                _json_block(sig),
                "",
            ]
        )
        return Rendered(markdown=md)

    if mode == "ritual":
        md = "\n".join(
            [
                "# Oracle (Ritual)",
                "",
                f"- slice_hash: `{slice_hash}`",
                "",
                "This is a symbolic projection shell (non-authoritative).",
                "",
            ]
        )
        return Rendered(markdown=md)

    # default "oracle" mode (compact)
    vectors = root.get("vectors", {})
    lines: List[str] = []
    lines.append("# Oracle (Snapshot)")
    lines.append("")
    lines.append(f"- slice_hash: `{slice_hash}`")
    lines.append("")
    for domain in _iter_domains(sig):
        sub = vectors.get(domain, {})
        if not isinstance(sub, dict):
            continue
        subnames = sorted([k for k in sub.keys() if isinstance(k, str)])
        lines.append(f"## {domain}")
        lines.append("")
        if subnames:
            for s in subnames:
                lines.append(f"- {domain}:{s}")
        else:
            lines.append("- (no subdomains)")
        lines.append("")
    return Rendered(markdown="\n".join(lines))

