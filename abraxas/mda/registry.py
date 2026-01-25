from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple, Union


@dataclass(frozen=True)
class DomainRegistryV1:
    """
    Minimal registry for MDA v1.x runs.

    This is intentionally small and deterministic: just enough structure to
    filter (domain, subdomain) pairs given user selections.
    """

    subdomains_by_domain: Dict[str, Tuple[str, ...]] = None  # type: ignore[assignment]

    @classmethod
    def from_vectors(cls, vectors: Dict[str, Dict[str, object]]) -> "DomainRegistryV1":
        subdomains_by_domain: Dict[str, Tuple[str, ...]] = {}
        for d in sorted(vectors.keys()):
            subs = vectors.get(d, {}) or {}
            subdomains_by_domain[d] = tuple(sorted(subs.keys()))
        return cls(subdomains_by_domain=subdomains_by_domain)

    def __post_init__(self) -> None:
        # Allow `DomainRegistryV1()` with a deterministic default set.
        if self.subdomains_by_domain is None:
            object.__setattr__(
                self,
                "subdomains_by_domain",
                {
                    # Canonical canary pairs
                    "tech_ai": ("foundation_models",),
                    "culture_memes": ("slang_language_drift",),
                },
            )

    @property
    def domains(self) -> Tuple[str, ...]:
        return tuple(sorted(self.subdomains_by_domain.keys()))

    @property
    def all_pairs(self) -> List[Tuple[str, str]]:
        pairs: List[Tuple[str, str]] = []
        for d in self.domains:
            for sub in self.subdomains_by_domain.get(d, ()):
                pairs.append((d, sub))
        return pairs

    def filter_pairs(
        self,
        *,
        enabled_domains: Sequence[str],
        enabled_subdomains: Sequence[str],
    ) -> List[Tuple[str, str]]:
        """
        Return pairs (domain, subdomain) that match user selections.

        Filtering logic:
          - If both enabled_domains and enabled_subdomains are empty → all pairs
          - If only enabled_domains is non-empty → all subdomains for those domains
          - If only enabled_subdomains is non-empty → any (domain, subdomain) that matches subdomain
          - If both are non-empty → intersection (domain in enabled_domains AND subdomain in enabled_subdomains)
        """
        if not enabled_domains and not enabled_subdomains:
            return self.all_pairs

        enabled_domains_set = set(enabled_domains) if enabled_domains else set()
        enabled_subdomains_set = set(enabled_subdomains) if enabled_subdomains else set()

        filtered: List[Tuple[str, str]] = []
        for d, sub in self.all_pairs:
            domain_match = d in enabled_domains_set if enabled_domains_set else True
            subdomain_match = sub in enabled_subdomains_set if enabled_subdomains_set else True
            if domain_match and subdomain_match:
                filtered.append((d, sub))

        return filtered

    def __repr__(self) -> str:
        return f"DomainRegistryV1(domains={len(self.domains)}, pairs={len(self.all_pairs)})"
