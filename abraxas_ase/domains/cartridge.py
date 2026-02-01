"""
SDCT v0.1 (Symbolic Domain Cartridge Template) - Cartridge Protocol

Defines the SymbolicDomainCartridge protocol that all domain cartridges must implement.

DESIGN LAWS:
1. Chassis invariant: tiers, keyed determinism, lanes, hysteresis, chronoscope,
   leakage linting are NOT domain code. Domains may not bypass them.
2. Cartridge purity: a domain cartridge may only implement:
   - encoding
   - motif extraction
   - evidence emission
   - optional domain-specific metrics (shadow-only unless promoted)
3. Normalization: every domain must emit the same NormalizedEvidence fields,
   so the chassis can score/promote without knowing the domain.
4. Namespacing: all motifs and metrics are namespaced by domain_id.
5. Deterministic everything: sorted outputs, stable hashes, no randomness.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Protocol, TypeVar, runtime_checkable

from .types import DomainDescriptor, Motif, NormalizedEvidence, RawItem


# SymbolObject is domain-specific, opaque to chassis
# Each cartridge defines its own SymbolObject type
SymbolObjectT = TypeVar("SymbolObjectT")


@runtime_checkable
class SymbolicDomainCartridge(Protocol[SymbolObjectT]):
    """
    Protocol for symbolic domain cartridges.

    A cartridge encapsulates all domain-specific logic:
    - How to encode raw items into symbols
    - How to extract motifs from those symbols
    - How to emit normalized evidence for the chassis

    The chassis pipeline calls these methods in order:
    1. encode(item) -> SymbolObject
    2. extract_motifs(symbol) -> List[Motif]
    3. emit_evidence(item, motifs, event_key) -> List[NormalizedEvidence]

    Cartridges MUST be deterministic: same inputs -> same outputs, always.
    """

    def descriptor(self) -> DomainDescriptor:
        """
        Return the domain descriptor for this cartridge.

        Must be stable and deterministic.
        """
        ...

    def encode(self, item: RawItem) -> SymbolObjectT:
        """
        Encode a raw item into a domain-specific symbol object.

        The SymbolObject is opaque to the chassis; only the cartridge knows its structure.

        Args:
            item: Raw input item

        Returns:
            Domain-specific symbol representation
        """
        ...

    def extract_motifs(self, symbol: SymbolObjectT) -> List[Motif]:
        """
        Extract motifs from a symbol object.

        Must return deterministically sorted list of Motif objects.
        Each Motif must have a namespaced motif_id: "{domain_id}:{motif_text}"

        Args:
            symbol: Domain-specific symbol object from encode()

        Returns:
            Sorted list of extracted motifs
        """
        ...

    def emit_evidence(
        self,
        item: RawItem,
        motifs: List[Motif],
        event_key: str,
    ) -> List[NormalizedEvidence]:
        """
        Emit normalized evidence for chassis consumption.

        This is the spine contract: must emit NormalizedEvidence rows that the
        chassis can aggregate and score without domain knowledge.

        Args:
            item: Original raw item
            motifs: Extracted motifs from extract_motifs()
            event_key: Cluster key for event grouping (keyed in Academic/Enterprise)

        Returns:
            Sorted list of NormalizedEvidence rows
        """
        ...


class BaseCartridge(ABC, Generic[SymbolObjectT]):
    """
    Abstract base class for cartridge implementations.

    Provides common utilities and enforces the cartridge protocol.
    Subclasses must implement all abstract methods.
    """

    @abstractmethod
    def descriptor(self) -> DomainDescriptor:
        """Return the domain descriptor."""
        raise NotImplementedError

    @abstractmethod
    def encode(self, item: RawItem) -> SymbolObjectT:
        """Encode item into domain symbol."""
        raise NotImplementedError

    @abstractmethod
    def extract_motifs(self, symbol: SymbolObjectT) -> List[Motif]:
        """Extract motifs from symbol."""
        raise NotImplementedError

    @abstractmethod
    def emit_evidence(
        self,
        item: RawItem,
        motifs: List[Motif],
        event_key: str,
    ) -> List[NormalizedEvidence]:
        """Emit normalized evidence."""
        raise NotImplementedError

    def process_item(
        self,
        item: RawItem,
        event_key: str,
    ) -> List[NormalizedEvidence]:
        """
        Convenience method: full pipeline from item to evidence.

        Calls encode -> extract_motifs -> emit_evidence in sequence.
        """
        symbol = self.encode(item)
        motifs = self.extract_motifs(symbol)
        return self.emit_evidence(item, motifs, event_key)

    def domain_id(self) -> str:
        """Shortcut to get domain_id from descriptor."""
        return self.descriptor().domain_id

    def make_motif_id(self, motif_text: str) -> str:
        """
        Create a namespaced motif_id.

        Format: "{domain_id}:{motif_text}"
        """
        return f"{self.domain_id()}:{motif_text}"


# Type alias for cartridge collections
CartridgeList = List[SymbolicDomainCartridge[Any]]
