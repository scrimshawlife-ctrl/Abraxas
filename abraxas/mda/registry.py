from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class DomainRegistryV1:
    """
    Minimal registry for practice runs.

    The registry is intentionally small: just a set of known (domain, subdomain)
    pairs derived from the fixture vectors.
    """

    domains: Tuple[str, ...]
    subdomains_by_domain: Dict[str, Tuple[str, ...]]

    @classmethod
    def from_vectors(cls, vectors: Dict[str, Dict[str, object]]) -> "DomainRegistryV1":
        domains = tuple(sorted(vectors.keys()))
        subdomains_by_domain: Dict[str, Tuple[str, ...]] = {}
        for d in domains:
            subs = vectors.get(d, {}) or {}
            subdomains_by_domain[d] = tuple(sorted(subs.keys()))
        return cls(domains=domains, subdomains_by_domain=subdomains_by_domain)

    def iter_pairs(self) -> List[Tuple[str, str]]:
        pairs: List[Tuple[str, str]] = []
        for d in self.domains:
            for s in self.subdomains_by_domain.get(d, ()):
                pairs.append((d, s))
        return pairs

    def filter_pairs(self, domains: str, subdomains: str) -> List[Tuple[str, str]]:
        # domains: "*" or comma list
        if domains.strip() == "*":
            allowed_domains = set(self.domains)
        else:
            allowed_domains = {d.strip() for d in domains.split(",") if d.strip()}

        # subdomains: "*" or comma list of "domain:subdomain"
        if subdomains.strip() == "*":
            allowed_pairs = set(self.iter_pairs())
        else:
            allowed_pairs = set()
            for item in subdomains.split(","):
                item = item.strip()
                if not item or ":" not in item:
                    continue
                d, s = item.split(":", 1)
                allowed_pairs.add((d.strip(), s.strip()))

        out: List[Tuple[str, str]] = []
        for d, s in self.iter_pairs():
            if d in allowed_domains and (d, s) in allowed_pairs:
                out.append((d, s))
        return sorted(out, key=lambda x: (x[0], x[1]))

