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

    def iter_pairs(self) -> List[Tuple[str, str]]:
        pairs: List[Tuple[str, str]] = []
        for d in self.domains:
            for s in self.subdomains_by_domain.get(d, ()):
                pairs.append((d, s))
        return pairs

    def filter_pairs(
        self,
        domains: Union[str, Sequence[str]],
        subdomains: Union[str, Sequence[str]],
    ) -> List[Tuple[str, str]]:
        # Supports both:
        # - legacy CLI strings: "*" or "a,b"
        # - v1.1 canary tuples: ("a", "b") and ("a:x", "b:y")

        if isinstance(domains, str):
            if domains.strip() == "*":
                allowed_domains = set(self.domains)
            else:
                allowed_domains = {d.strip() for d in domains.split(",") if d.strip()}
        else:
            allowed_domains = {str(d).strip() for d in domains if str(d).strip()}

        if isinstance(subdomains, str):
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
        else:
            allowed_pairs = set()
            for item in subdomains:
                item = str(item).strip()
                if not item or ":" not in item:
                    continue
                d, s = item.split(":", 1)
                allowed_pairs.add((d.strip(), s.strip()))

        out: List[Tuple[str, str]] = []
        for d, s in self.iter_pairs():
            if d in allowed_domains and (d, s) in allowed_pairs:
                out.append((d, s))
        return sorted(out, key=lambda x: (x[0], x[1]))

