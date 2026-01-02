from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class DomainRegistryV1:
    """
    Minimal deterministic domain/subdomain registry for MDA.

    This is intentionally small and local-only; no external loading.
    """

    _domains: Dict[str, Tuple[str, ...]] = (
        {
            # NOTE: keep this list stable; add-only.
            "tech_ai": ("foundation_models",),
        }
    )

    def domains(self) -> List[str]:
        return sorted(self._domains.keys())

    def subdomains(self, domain: str) -> Tuple[str, ...]:
        return self._domains.get(domain, tuple())

    def all_subdomain_keys(self) -> List[str]:
        # "domain:subdomain"
        keys: List[str] = []
        for d in sorted(self._domains.keys()):
            for s in self._domains[d]:
                keys.append(f"{d}:{s}")
        return keys

