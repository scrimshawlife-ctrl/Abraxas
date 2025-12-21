"""Lexicon Engine v1: Domain-scoped, versioned, deterministic token-weight mapping."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Protocol, Tuple

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.core.provenance import Provenance


@dataclass(frozen=True)
class LexiconEntry:
    """Single token-weight mapping with metadata."""

    token: str
    weight: float
    meta: Dict[str, str]  # provenance notes, tags, etc.


@dataclass(frozen=True)
class LexiconPack:
    """Versioned collection of lexicon entries for a domain."""

    domain: str
    version: str
    entries: Tuple[LexiconEntry, ...]
    created_at_utc: str  # ISO8601 Z

    @staticmethod
    def now_iso_z() -> str:
        """Generate ISO8601 timestamp with Zulu timezone (no microseconds)."""
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class LexiconRegistry(Protocol):
    """Protocol for lexicon storage backends."""

    def register(self, pack: LexiconPack) -> None:
        """Store a lexicon pack."""
        ...

    def get(self, domain: str, version: Optional[str]) -> Optional[LexiconPack]:
        """Retrieve a lexicon pack by domain and version (None = latest)."""
        ...

    def latest(self, domain: str) -> Optional[LexiconPack]:
        """Retrieve the latest version for a domain."""
        ...

    def list_versions(self, domain: str) -> List[str]:
        """List all versions for a domain."""
        ...


class InMemoryLexiconRegistry:
    """In-memory lexicon registry for testing and development."""

    def __init__(self) -> None:
        self._packs: Dict[Tuple[str, str], LexiconPack] = {}
        self._latest: Dict[str, str] = {}

    def register(self, pack: LexiconPack) -> None:
        """Store a lexicon pack."""
        key = (pack.domain, pack.version)
        self._packs[key] = pack
        self._latest[pack.domain] = pack.version

    def get(self, domain: str, version: Optional[str]) -> Optional[LexiconPack]:
        """Retrieve a lexicon pack by domain and version (None = latest)."""
        if version is None:
            return self.latest(domain)
        return self._packs.get((domain, version))

    def latest(self, domain: str) -> Optional[LexiconPack]:
        """Retrieve the latest version for a domain."""
        v = self._latest.get(domain)
        if v is None:
            return None
        return self._packs.get((domain, v))

    def list_versions(self, domain: str) -> List[str]:
        """List all versions for a domain."""
        vs = [v for (d, v) in self._packs.keys() if d == domain]
        return sorted(vs)


@dataclass(frozen=True)
class CompressionResult:
    """Result of lexicon compression with full provenance."""

    domain: str
    version: str
    tokens_in: Tuple[str, ...]
    weights_out: Dict[str, float]
    matched: Tuple[str, ...]
    unmatched: Tuple[str, ...]
    provenance: Provenance


class LexiconEngine:
    """
    Deterministic token-weight mapping.
    No inference, no learning here: just versioned lookup and compression.
    """

    def __init__(self, registry: LexiconRegistry) -> None:
        self._registry = registry

    def register(self, pack: LexiconPack) -> None:
        """Register a lexicon pack."""
        self._registry.register(pack)

    def resolve(self, domain: str, version: Optional[str] = None) -> LexiconPack:
        """Resolve a lexicon pack by domain and version (None = latest)."""
        pack = self._registry.get(domain, version)
        if pack is None:
            raise KeyError(f"Lexicon not found: domain={domain} version={version or 'latest'}")
        return pack

    def compress(
        self,
        domain: str,
        tokens: Iterable[str],
        *,
        version: Optional[str] = None,
        run_id: str,
        git_sha: Optional[str] = None,
        host: Optional[str] = None,
    ) -> CompressionResult:
        """
        Compress tokens using a lexicon pack.

        Returns:
            CompressionResult with matched/unmatched tokens, weights, and provenance.
        """
        pack = self.resolve(domain, version)
        token_list = tuple(tokens)

        table: Dict[str, float] = {e.token: float(e.weight) for e in pack.entries}

        matched: List[str] = []
        unmatched: List[str] = []
        weights_out: Dict[str, float] = {}

        # deterministic iteration order: input order preserved, aggregation stable
        for t in token_list:
            if t in table:
                matched.append(t)
                weights_out[t] = table[t]
            else:
                unmatched.append(t)

        inputs_hash = sha256_hex(
            canonical_json(
                {
                    "domain": domain,
                    "version": pack.version,
                    "tokens": token_list,
                }
            )
        )
        config_hash = sha256_hex(
            canonical_json(
                {
                    "engine": "LexiconEngine.v1",
                }
            )
        )

        prov = Provenance(
            run_id=run_id,
            started_at_utc=Provenance.now_iso_z(),
            inputs_hash=inputs_hash,
            config_hash=config_hash,
            git_sha=git_sha,
            host=host,
        )

        return CompressionResult(
            domain=domain,
            version=pack.version,
            tokens_in=token_list,
            weights_out=weights_out,
            matched=tuple(matched),
            unmatched=tuple(unmatched),
            provenance=prov,
        )
