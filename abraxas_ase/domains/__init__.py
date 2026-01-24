"""
SDCT v0.1 (Symbolic Domain Cartridge Template)

Domain-agnostic cartridge system for symbolic analysis.

Design Laws:
1. Chassis invariant: tiers, keyed determinism, lanes, hysteresis,
   chronoscope, leakage linting are NOT domain code. Domains may not bypass.
2. Cartridge purity: domains only implement encoding, motif extraction,
   evidence emission, and optional shadow-only metrics.
3. Normalization: all domains emit NormalizedEvidence for chassis scoring.
4. Namespacing: all motifs/metrics namespaced by domain_id.
5. Determinism: sorted outputs, stable hashes, no randomness.

Usage:
    from abraxas_ase.domains import (
        get_default_registry,
        RawItem,
        NormalizedEvidence,
    )

    # Get all enabled cartridges
    registry = get_default_registry()
    cartridges = registry.load_enabled()

    # Process an item through all domains
    item = RawItem(id="1", source="test", ...)
    for cartridge in cartridges:
        evidence = cartridge.process_item(item, event_key="...")

Built-in Cartridges:
    - text.subword.v1 (TextSubwordCartridge): Text subword motifs
    - digit.v1 (DigitMotifCartridge): Digit n-gram motifs
"""

__version__ = "0.1.0"

# Core types
from .types import (
    AggregatedMotifStats,
    DomainDescriptor,
    LANE_NAMES,
    LANE_ORDER,
    Motif,
    NormalizedEvidence,
    RawItem,
    lane_index,
    lane_name,
)

# Cartridge protocol
from .cartridge import (
    BaseCartridge,
    CartridgeList,
    SymbolicDomainCartridge,
)

# Registry
from .registry import (
    CartridgeEntry,
    DomainRegistry,
    get_default_registry,
    reset_default_registry,
)

# Built-in cartridges
from .text_subword import (
    TextSubwordCartridge,
    TextSymbol,
    TokenInfo,
    create_text_subword_cartridge,
)

from .digit_motif import (
    DEFAULT_SIGNIFICANT_PATTERNS,
    DigitMotifCartridge,
    DigitSequence,
    DigitSymbol,
    create_digit_cartridge,
)


__all__ = [
    # Version
    "__version__",
    # Types
    "AggregatedMotifStats",
    "DomainDescriptor",
    "LANE_NAMES",
    "LANE_ORDER",
    "Motif",
    "NormalizedEvidence",
    "RawItem",
    "lane_index",
    "lane_name",
    # Protocol
    "BaseCartridge",
    "CartridgeList",
    "SymbolicDomainCartridge",
    # Registry
    "CartridgeEntry",
    "DomainRegistry",
    "get_default_registry",
    "reset_default_registry",
    # Text Subword
    "TextSubwordCartridge",
    "TextSymbol",
    "TokenInfo",
    "create_text_subword_cartridge",
    # Digit
    "DEFAULT_SIGNIFICANT_PATTERNS",
    "DigitMotifCartridge",
    "DigitSequence",
    "DigitSymbol",
    "create_digit_cartridge",
]
