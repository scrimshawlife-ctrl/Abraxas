from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_default_vectors() -> Dict[str, Dict[str, object]]:
    """Union the ``vectors`` maps of every bundled MDA fixture.

    Deterministic: fixtures are read in sorted path order and domain/subdomain
    keys are sorted, so the resulting registry is stable across runs.
    """
    vectors: Dict[str, Dict[str, object]] = {}
    if not _FIXTURES_DIR.is_dir():
        return vectors
    for path in sorted(_FIXTURES_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        file_vectors = data.get("vectors") if isinstance(data, dict) else None
        if not isinstance(file_vectors, dict):
            continue
        for domain, subs in file_vectors.items():
            if not isinstance(subs, dict):
                continue
            bucket = vectors.setdefault(str(domain), {})
            for sub in subs:
                bucket.setdefault(str(sub), None)
    return vectors


def _default_domain_set() -> Tuple[str, ...]:
    return tuple(sorted(_load_default_vectors().keys()))


def _default_subdomains_map() -> Dict[str, Tuple[str, ...]]:
    vectors = _load_default_vectors()
    return {d: tuple(sorted(subs.keys())) for d, subs in vectors.items()}


@dataclass(frozen=True)
class DomainRegistryV1:
    """
    Minimal registry for practice runs.

    The registry is intentionally small: just a set of known (domain, subdomain)
    pairs derived from the fixture vectors. Calling ``DomainRegistryV1()`` with
    no arguments loads the bundled fixtures.
    """

    domain_set: Tuple[str, ...] = field(default_factory=_default_domain_set)
    subdomains_by_domain: Dict[str, Tuple[str, ...]] = field(
        default_factory=_default_subdomains_map
    )

    # --- Accessors (method API used by adapters / oracle bridge) -----------
    def domains(self) -> Tuple[str, ...]:
        """Return the known domains, sorted."""
        return self.domain_set

    def subdomains(self, domain: str) -> Tuple[str, ...]:
        """Return known subdomains for ``domain`` (empty tuple if unknown)."""
        return self.subdomains_by_domain.get(domain, ())

    def all_subdomain_keys(self) -> Tuple[str, ...]:
        """Return every known ``domain:subdomain`` key, sorted."""
        keys: List[str] = []
        for d in self.domain_set:
            for s in self.subdomains_by_domain.get(d, ()):
                keys.append(f"{d}:{s}")
        return tuple(sorted(keys))

    @classmethod
    def from_vectors(cls, vectors: Dict[str, Dict[str, object]]) -> "DomainRegistryV1":
        domains = tuple(sorted(vectors.keys()))
        subdomains_by_domain: Dict[str, Tuple[str, ...]] = {}
        for d in domains:
            subs = vectors.get(d, {}) or {}
            subdomains_by_domain[d] = tuple(sorted(subs.keys()))
        return cls(domain_set=domains, subdomains_by_domain=subdomains_by_domain)

    def iter_pairs(self) -> List[Tuple[str, str]]:
        pairs: List[Tuple[str, str]] = []
        for d in self.domain_set:
            for s in self.subdomains_by_domain.get(d, ()):
                pairs.append((d, s))
        return pairs

    def filter_pairs(self, domains: str, subdomains: str) -> List[Tuple[str, str]]:
        # domains: "*" or comma list
        if domains.strip() == "*":
            allowed_domains = set(self.domain_set)
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
