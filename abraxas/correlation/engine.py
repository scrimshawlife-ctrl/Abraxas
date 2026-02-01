"""Correlation Engine v1: Deterministic windowed correlation delta generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.core.provenance import Provenance
from abraxas.oracle.transforms import CorrelationDelta


@dataclass(frozen=True)
class CorrelationEvent:
    """Single correlation event with domain, key, value, and timestamp."""

    domain: str
    key: str
    value: float
    observed_at_utc: str  # ISO Z


@dataclass(frozen=True)
class CorrelationConfig:
    """Configuration for correlation engine."""

    pair_rules: Tuple[Tuple[str, str], ...]  # allowed domain pairs
    max_pairs: int


@dataclass(frozen=True)
class CorrelationResult:
    """Result of correlation analysis with provenance."""

    deltas: Tuple[CorrelationDelta, ...]
    provenance: Provenance


class CorrelationEngine:
    """
    Deterministic correlation delta generator.
    Working theory: simple co-movement proxy via keyed value alignment.
    No ML, no hidden state.
    """

    def run(
        self,
        events_a: Iterable[CorrelationEvent],
        events_b: Iterable[CorrelationEvent],
        *,
        domain_a: str,
        domain_b: str,
        config: CorrelationConfig,
        run_id: str,
        git_sha: Optional[str] = None,
        host: Optional[str] = None,
    ) -> CorrelationResult:
        """
        Generate correlation deltas between two event streams.

        Args:
            events_a: Events from domain A
            events_b: Events from domain B
            domain_a: Domain A identifier
            domain_b: Domain B identifier
            config: Correlation configuration
            run_id: Run identifier for provenance
            git_sha: Optional git commit SHA
            host: Optional host identifier

        Returns:
            CorrelationResult with deltas and provenance

        Raises:
            ValueError: If domain pair not allowed by config
        """
        if (domain_a, domain_b) not in set(config.pair_rules) and (domain_b, domain_a) not in set(
            config.pair_rules
        ):
            raise ValueError("domain pair not allowed by config")

        a = list(events_a)
        b = list(events_b)

        # stable maps: key -> latest value (ties resolved deterministically by timestamp string sort)
        map_a = _latest_by_key(a)
        map_b = _latest_by_key(b)

        shared_keys = sorted(set(map_a.keys()) & set(map_b.keys()))
        deltas: List[CorrelationDelta] = []

        for k in shared_keys:
            va, ta = map_a[k]
            vb, tb = map_b[k]
            # simple delta proxy: product sign + magnitude min; deterministic
            delta = _delta_proxy(va, vb)

            observed_at = max(ta, tb)  # lexicographic ISO Z max = latest
            deltas.append(CorrelationDelta(domain_a, domain_b, k, float(delta), observed_at))

        # deterministic cap
        deltas.sort(key=lambda d: (-abs(d.delta), d.key, d.observed_at_utc))
        deltas = deltas[: int(config.max_pairs)]

        inputs_hash = sha256_hex(
            canonical_json(
                {
                    "domain_a": domain_a,
                    "domain_b": domain_b,
                    "events_a": [e.__dict__ for e in a],
                    "events_b": [e.__dict__ for e in b],
                }
            )
        )
        config_hash = sha256_hex(
            canonical_json({"engine": "CorrelationEngine.v1", "cfg": config.__dict__})
        )

        prov = Provenance(
            run_id=run_id,
            started_at_utc=Provenance.now_iso_z(),
            inputs_hash=inputs_hash,
            config_hash=config_hash,
            git_sha=git_sha,
            host=host,
        )

        return CorrelationResult(deltas=tuple(deltas), provenance=prov)


def _latest_by_key(events: List[CorrelationEvent]) -> Dict[str, Tuple[float, str]]:
    """
    Get latest value for each key (deterministic).

    Args:
        events: List of correlation events

    Returns:
        Dict mapping key -> (value, timestamp)
    """
    # sort by observed_at_utc then key for determinism
    events_sorted = sorted(events, key=lambda e: (e.key, e.observed_at_utc))
    out: Dict[str, Tuple[float, str]] = {}
    for e in events_sorted:
        out[e.key] = (float(e.value), e.observed_at_utc)
    return out


def _delta_proxy(a: float, b: float) -> float:
    """
    Bounded deterministic proxy in [-1,1] scaled by min magnitude.

    Args:
        a: First value
        b: Second value

    Returns:
        Correlation delta proxy
    """
    mag = min(abs(a), abs(b))
    sign = 1.0 if (a * b) >= 0 else -1.0
    return sign * mag
