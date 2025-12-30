"""
Domain Compression Engine (DCE) v2

Extends Lexicon Engine v1 with:
- Lineage tracking (version evolution chains)
- Lifecycle states (proto → front → saturated → dormant → archived)
- Evolution events (what changed, why, when)
- Domain-specific compression operators

Philosophy: Lexicons are compression operators, not static dictionaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.core.provenance import Provenance
from abraxas.lexicon.engine import LexiconEntry, LexiconPack, LexiconRegistry
from abraxas.slang.lifecycle import LifecycleState  # Canonical lifecycle state definition


class EvolutionReason(str, Enum):
    """Reasons for lexicon evolution."""

    INITIAL_CREATION = "initial_creation"
    COMPRESSION_OBSERVED = "compression_observed"  # SCO/ECO detected new pattern
    WEIGHT_ADJUSTMENT = "weight_adjustment"  # Rebalanced weights
    LIFECYCLE_TRANSITION = "lifecycle_transition"  # State change
    DOMAIN_EXPANSION = "domain_expansion"  # Added new subdomain
    PRUNING = "pruning"  # Removed obsolete entries
    MERGE = "merge"  # Merged multiple versions
    FORK = "fork"  # Created variant for subdomain


@dataclass(frozen=True)
class LexiconLineage:
    """Lineage information for a lexicon version."""

    version: str
    parent_version: Optional[str]  # None for initial version
    children_versions: Tuple[str, ...] = field(default_factory=tuple)
    created_at_utc: str = field(default_factory=lambda: _utc_now_iso())
    evolution_reason: EvolutionReason = EvolutionReason.INITIAL_CREATION


@dataclass(frozen=True)
class EvolutionEvent:
    """Records a change in the lexicon."""

    from_version: Optional[str]  # None for initial
    to_version: str
    reason: EvolutionReason
    changes: Dict[str, str]  # token → change_type (added/removed/weight_changed/state_changed)
    created_at_utc: str = field(default_factory=lambda: _utc_now_iso())
    provenance_hash: str = ""  # SHA-256 of evolution metadata

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of evolution event."""
        return sha256_hex(
            canonical_json(
                {
                    "from_version": self.from_version,
                    "to_version": self.to_version,
                    "reason": self.reason.value,
                    "changes": self.changes,
                    "created_at_utc": self.created_at_utc,
                }
            )
        )


@dataclass(frozen=True)
class DCEEntry:
    """Enhanced lexicon entry with lifecycle and metadata."""

    token: str
    weight: float
    lifecycle_state: LifecycleState
    domain: str
    subdomain: Optional[str] = None  # e.g., "politics.us", "media.twitter"
    meta: Dict[str, str] = field(default_factory=dict)
    first_seen_utc: Optional[str] = None
    last_updated_utc: Optional[str] = None

    def to_lexicon_entry(self) -> LexiconEntry:
        """Convert to base LexiconEntry for backward compatibility."""
        meta = dict(self.meta)
        meta["lifecycle_state"] = self.lifecycle_state.value
        if self.subdomain:
            meta["subdomain"] = self.subdomain
        if self.first_seen_utc:
            meta["first_seen_utc"] = self.first_seen_utc
        if self.last_updated_utc:
            meta["last_updated_utc"] = self.last_updated_utc
        return LexiconEntry(token=self.token, weight=self.weight, meta=meta)

    @staticmethod
    def from_lexicon_entry(entry: LexiconEntry, domain: str) -> DCEEntry:
        """Convert from base LexiconEntry."""
        return DCEEntry(
            token=entry.token,
            weight=entry.weight,
            lifecycle_state=LifecycleState(entry.meta.get("lifecycle_state", "Proto")),
            domain=domain,
            subdomain=entry.meta.get("subdomain"),
            meta={k: v for k, v in entry.meta.items() if k not in {"lifecycle_state", "subdomain", "first_seen_utc", "last_updated_utc"}},
            first_seen_utc=entry.meta.get("first_seen_utc"),
            last_updated_utc=entry.meta.get("last_updated_utc"),
        )


@dataclass(frozen=True)
class DCEPack:
    """Enhanced lexicon pack with lineage and evolution tracking."""

    domain: str
    version: str
    entries: Tuple[DCEEntry, ...]
    lineage: LexiconLineage
    created_at_utc: str = field(default_factory=lambda: _utc_now_iso())

    def to_lexicon_pack(self) -> LexiconPack:
        """Convert to base LexiconPack for backward compatibility."""
        base_entries = tuple(e.to_lexicon_entry() for e in self.entries)
        return LexiconPack(
            domain=self.domain,
            version=self.version,
            entries=base_entries,
            created_at_utc=self.created_at_utc,
        )

    @staticmethod
    def from_lexicon_pack(pack: LexiconPack, lineage: Optional[LexiconLineage] = None) -> DCEPack:
        """Convert from base LexiconPack."""
        dce_entries = tuple(DCEEntry.from_lexicon_entry(e, pack.domain) for e in pack.entries)
        if lineage is None:
            lineage = LexiconLineage(
                version=pack.version,
                parent_version=None,
                created_at_utc=pack.created_at_utc,
            )
        return DCEPack(
            domain=pack.domain,
            version=pack.version,
            entries=dce_entries,
            lineage=lineage,
            created_at_utc=pack.created_at_utc,
        )


class DCERegistry:
    """Registry for DCE packs with lineage and evolution tracking."""

    def __init__(self, base_registry: LexiconRegistry) -> None:
        self._base_registry = base_registry
        self._lineages: Dict[Tuple[str, str], LexiconLineage] = {}  # (domain, version) → lineage
        self._evolution_events: List[EvolutionEvent] = []

    def register(self, pack: DCEPack, evolution_event: Optional[EvolutionEvent] = None) -> None:
        """Register a DCE pack with lineage tracking."""
        # Store in base registry
        self._base_registry.register(pack.to_lexicon_pack())

        # Store lineage
        key = (pack.domain, pack.version)
        self._lineages[key] = pack.lineage

        # Record evolution event
        if evolution_event is not None:
            # Compute hash if not already set
            if not evolution_event.provenance_hash:
                evolution_event = EvolutionEvent(
                    from_version=evolution_event.from_version,
                    to_version=evolution_event.to_version,
                    reason=evolution_event.reason,
                    changes=evolution_event.changes,
                    created_at_utc=evolution_event.created_at_utc,
                    provenance_hash=evolution_event.compute_hash(),
                )
            self._evolution_events.append(evolution_event)

    def get(self, domain: str, version: Optional[str] = None) -> Optional[DCEPack]:
        """Retrieve a DCE pack by domain and version (None = latest)."""
        base_pack = self._base_registry.get(domain, version)
        if base_pack is None:
            return None

        key = (domain, base_pack.version)
        lineage = self._lineages.get(key)
        return DCEPack.from_lexicon_pack(base_pack, lineage)

    def get_lineage(self, domain: str, version: str) -> Optional[LexiconLineage]:
        """Get lineage information for a specific version."""
        return self._lineages.get((domain, version))

    def get_evolution_chain(self, domain: str, version: str) -> List[EvolutionEvent]:
        """Get the full evolution chain leading to a version."""
        chain: List[EvolutionEvent] = []
        current_version = version

        while current_version:
            # Find event that created this version
            event = next(
                (e for e in self._evolution_events if e.to_version == current_version),
                None,
            )
            if event is None:
                break
            chain.append(event)
            current_version = event.from_version  # type: ignore

        return list(reversed(chain))  # Return in chronological order

    def list_versions(self, domain: str) -> List[str]:
        """List all versions for a domain."""
        return self._base_registry.list_versions(domain)

    def get_lineage_tree(self, domain: str) -> Dict[str, List[str]]:
        """Get the full lineage tree for a domain (version → children)."""
        tree: Dict[str, List[str]] = {}
        for (d, v), lineage in self._lineages.items():
            if d == domain:
                tree[v] = list(lineage.children_versions)
        return tree


class DomainCompressionEngine:
    """
    Domain Compression Engine (DCE)

    Orchestrates domain-specific compression with:
    - Lifecycle-aware compression (weight different states differently)
    - Lineage tracking (understand evolution)
    - Evolution events (why things changed)
    - Domain-specific operators (beyond simple weight lookup)
    """

    def __init__(self, registry: DCERegistry) -> None:
        self._registry = registry

    def register(self, pack: DCEPack, evolution_event: Optional[EvolutionEvent] = None) -> None:
        """Register a DCE pack."""
        self._registry.register(pack, evolution_event)

    def compress(
        self,
        domain: str,
        tokens: List[str],
        *,
        version: Optional[str] = None,
        lifecycle_weights: Optional[Dict[LifecycleState, float]] = None,
        run_id: str,
        git_sha: Optional[str] = None,
    ) -> DCECompressionResult:
        """
        Compress tokens using lifecycle-aware weighting.

        Args:
            domain: Domain to compress against
            tokens: Input tokens
            version: Specific version (None = latest)
            lifecycle_weights: Multipliers by lifecycle state (None = defaults)
            run_id: Run identifier for provenance
            git_sha: Git SHA for provenance

        Returns:
            DCECompressionResult with lifecycle-aware compression
        """
        pack = self._registry.get(domain, version)
        if pack is None:
            raise KeyError(f"DCE pack not found: domain={domain} version={version or 'latest'}")

        # Default lifecycle weights favor active states
        if lifecycle_weights is None:
            lifecycle_weights = {
                LifecycleState.PROTO: 0.5,  # Lower weight for proto
                LifecycleState.FRONT: 1.0,  # Full weight for active
                LifecycleState.SATURATED: 0.9,  # Slightly lower for saturated
                LifecycleState.DORMANT: 0.3,  # Much lower for dormant
                LifecycleState.ARCHIVED: 0.1,  # Minimal for archived
            }

        # Build token → entry map
        entry_map: Dict[str, DCEEntry] = {e.token: e for e in pack.entries}

        # Compress with lifecycle weighting
        matched: List[str] = []
        unmatched: List[str] = []
        weights_out: Dict[str, float] = {}
        lifecycle_info: Dict[str, str] = {}

        for token in tokens:
            if token in entry_map:
                entry = entry_map[token]
                lifecycle_multiplier = lifecycle_weights.get(entry.lifecycle_state, 1.0)
                adjusted_weight = entry.weight * lifecycle_multiplier

                matched.append(token)
                weights_out[token] = adjusted_weight
                lifecycle_info[token] = entry.lifecycle_state.value
            else:
                unmatched.append(token)

        # Provenance
        inputs_hash = sha256_hex(
            canonical_json(
                {
                    "domain": domain,
                    "version": pack.version,
                    "tokens": tokens,
                    "lifecycle_weights": {k.value: v for k, v in lifecycle_weights.items()},
                }
            )
        )
        config_hash = sha256_hex(
            canonical_json(
                {
                    "engine": "DomainCompressionEngine.v2",
                }
            )
        )

        prov = Provenance(
            run_id=run_id,
            started_at_utc=Provenance.now_iso_z(),
            inputs_hash=inputs_hash,
            config_hash=config_hash,
            git_sha=git_sha,
            host=None,
        )

        return DCECompressionResult(
            domain=domain,
            version=pack.version,
            tokens_in=tuple(tokens),
            weights_out=weights_out,
            matched=tuple(matched),
            unmatched=tuple(unmatched),
            lifecycle_info=lifecycle_info,
            provenance=prov,
        )

    def evolve(
        self,
        domain: str,
        from_version: str,
        to_version: str,
        changes: Dict[str, DCEEntry],  # token → new/updated entry
        removals: List[str],
        reason: EvolutionReason,
        run_id: str,
    ) -> DCEPack:
        """
        Evolve a lexicon to a new version.

        Args:
            domain: Domain to evolve
            from_version: Parent version
            to_version: New version identifier
            changes: Token → new/updated DCEEntry
            removals: Tokens to remove
            reason: Why this evolution happened
            run_id: Run identifier for provenance

        Returns:
            New DCEPack
        """
        parent_pack = self._registry.get(domain, from_version)
        if parent_pack is None:
            raise KeyError(f"Parent version not found: domain={domain} version={from_version}")

        # Build new entry list
        existing_map = {e.token: e for e in parent_pack.entries}
        new_entries: List[DCEEntry] = []

        # Apply changes
        for token, entry in changes.items():
            new_entries.append(entry)
            existing_map.pop(token, None)  # Remove if updating

        # Keep existing entries not removed
        for token, entry in existing_map.items():
            if token not in removals:
                new_entries.append(entry)

        # Create lineage
        lineage = LexiconLineage(
            version=to_version,
            parent_version=from_version,
            created_at_utc=_utc_now_iso(),
            evolution_reason=reason,
        )

        # Create new pack
        new_pack = DCEPack(
            domain=domain,
            version=to_version,
            entries=tuple(new_entries),
            lineage=lineage,
            created_at_utc=_utc_now_iso(),
        )

        # Build evolution event
        change_types: Dict[str, str] = {}
        for token in changes:
            if token in existing_map:
                change_types[token] = "modified"
            else:
                change_types[token] = "added"
        for token in removals:
            change_types[token] = "removed"

        evolution_event = EvolutionEvent(
            from_version=from_version,
            to_version=to_version,
            reason=reason,
            changes=change_types,
            created_at_utc=_utc_now_iso(),
        )

        # Register
        self._registry.register(new_pack, evolution_event)

        return new_pack


@dataclass(frozen=True)
class DCECompressionResult:
    """Result of DCE compression with lifecycle information."""

    domain: str
    version: str
    tokens_in: Tuple[str, ...]
    weights_out: Dict[str, float]
    matched: Tuple[str, ...]
    unmatched: Tuple[str, ...]
    lifecycle_info: Dict[str, str]  # token → lifecycle_state
    provenance: Provenance


def _utc_now_iso() -> str:
    """Generate ISO8601 timestamp with Zulu timezone (no microseconds)."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
