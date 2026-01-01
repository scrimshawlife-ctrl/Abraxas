from __future__ import annotations

from typing import Any, Dict, List

from abraxas.evidence.lift import load_bundles


def evidence_by_term(bundles_dir: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    term(lower) -> list[bundle]
    """
    bundles = load_bundles(bundles_dir)
    out: Dict[str, List[Dict[str, Any]]] = {}
    for b in bundles:
        terms = b.get("terms") if isinstance(b.get("terms"), list) else []
        for t in terms:
            tk = str(t or "").strip().lower()
            if not tk:
                continue
            out.setdefault(tk, []).append(b)
    return out
