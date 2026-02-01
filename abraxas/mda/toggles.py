from __future__ import annotations

from typing import Any, Dict, List, Tuple


def load_toggle_file(obj: Dict[str, Any]) -> Tuple[str, ...]:
    """
    Parse a minimal toggle file into enabled subdomain keys ("domain:subdomain").

    Supported shapes (additive):
      - {"enabled_subdomains": ["d:s", ...]}
      - {"domains": {"d": ["s", ...]}}
    """
    if isinstance(obj.get("enabled_subdomains"), list):
        out = [str(x) for x in obj["enabled_subdomains"] if str(x).strip()]
        return tuple(sorted(set(out)))

    domains = obj.get("domains")
    if isinstance(domains, dict):
        keys: List[str] = []
        for d in sorted(domains.keys()):
            subs = domains[d]
            if not isinstance(subs, list):
                continue
            for s in subs:
                keys.append(f"{d}:{s}")
        return tuple(sorted(set(keys)))

    return tuple()

