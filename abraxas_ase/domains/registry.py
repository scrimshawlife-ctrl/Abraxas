"""
SDCT v0.1 (Symbolic Domain Cartridge Template) - Domain Registry

Manages registration and loading of domain cartridges.
Cartridges are loaded deterministically in a fixed order.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from ..provenance import sha256_hex, stable_json_dumps
from .cartridge import BaseCartridge, SymbolicDomainCartridge
from .types import DomainDescriptor


@dataclass
class CartridgeEntry:
    """Registry entry for a cartridge."""

    domain_id: str
    cartridge_class: Type[BaseCartridge[Any]]
    enabled: bool = True
    priority: int = 0  # Lower = earlier in pipeline

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "cartridge_class": self.cartridge_class.__name__,
            "enabled": self.enabled,
            "priority": self.priority,
        }


class DomainRegistry:
    """
    Registry for symbolic domain cartridges.

    Usage:
        registry = DomainRegistry()
        registry.register(TextSubwordCartridge)
        registry.register(DigitMotifCartridge)

        # Get enabled cartridges in priority order
        cartridges = registry.load_enabled()

        # Process items through all domains
        for cartridge in cartridges:
            evidence = cartridge.process_item(item, event_key)
    """

    def __init__(self) -> None:
        self._entries: Dict[str, CartridgeEntry] = {}
        self._instances: Dict[str, BaseCartridge[Any]] = {}

    def register(
        self,
        cartridge_class: Type[BaseCartridge[Any]],
        *,
        enabled: bool = True,
        priority: int = 0,
    ) -> None:
        """
        Register a cartridge class.

        Args:
            cartridge_class: The cartridge class to register
            enabled: Whether the cartridge is enabled by default
            priority: Processing priority (lower = earlier)
        """
        # Instantiate to get descriptor
        instance = cartridge_class()
        desc = instance.descriptor()
        domain_id = desc.domain_id

        if domain_id in self._entries:
            raise ValueError(f"Domain '{domain_id}' already registered")

        self._entries[domain_id] = CartridgeEntry(
            domain_id=domain_id,
            cartridge_class=cartridge_class,
            enabled=enabled,
            priority=priority,
        )
        self._instances[domain_id] = instance

    def unregister(self, domain_id: str) -> None:
        """Unregister a cartridge by domain_id."""
        self._entries.pop(domain_id, None)
        self._instances.pop(domain_id, None)

    def get(self, domain_id: str) -> Optional[BaseCartridge[Any]]:
        """Get a cartridge instance by domain_id."""
        return self._instances.get(domain_id)

    def get_descriptor(self, domain_id: str) -> Optional[DomainDescriptor]:
        """Get descriptor for a domain."""
        instance = self._instances.get(domain_id)
        return instance.descriptor() if instance else None

    def enable(self, domain_id: str) -> None:
        """Enable a cartridge."""
        if domain_id in self._entries:
            entry = self._entries[domain_id]
            self._entries[domain_id] = CartridgeEntry(
                domain_id=entry.domain_id,
                cartridge_class=entry.cartridge_class,
                enabled=True,
                priority=entry.priority,
            )

    def disable(self, domain_id: str) -> None:
        """Disable a cartridge."""
        if domain_id in self._entries:
            entry = self._entries[domain_id]
            self._entries[domain_id] = CartridgeEntry(
                domain_id=entry.domain_id,
                cartridge_class=entry.cartridge_class,
                enabled=False,
                priority=entry.priority,
            )

    def is_enabled(self, domain_id: str) -> bool:
        """Check if a cartridge is enabled."""
        entry = self._entries.get(domain_id)
        return entry.enabled if entry else False

    def list_all(self) -> List[str]:
        """List all registered domain_ids in priority order."""
        return sorted(
            self._entries.keys(),
            key=lambda d: (self._entries[d].priority, d),
        )

    def list_enabled(self) -> List[str]:
        """List enabled domain_ids in priority order."""
        return sorted(
            [d for d, e in self._entries.items() if e.enabled],
            key=lambda d: (self._entries[d].priority, d),
        )

    def load_enabled(self) -> List[BaseCartridge[Any]]:
        """
        Load all enabled cartridges in priority order.

        Returns:
            List of cartridge instances, deterministically ordered
        """
        enabled_ids = self.list_enabled()
        return [self._instances[d] for d in enabled_ids]

    def descriptors(self) -> List[DomainDescriptor]:
        """Get descriptors for all enabled domains in priority order."""
        return [self._instances[d].descriptor() for d in self.list_enabled()]

    def registry_hash(self) -> str:
        """
        Compute deterministic hash of registry state.

        Useful for provenance tracking.
        """
        state = {
            "domains": [
                {
                    "domain_id": d,
                    "enabled": self._entries[d].enabled,
                    "priority": self._entries[d].priority,
                    "descriptor_hash": self._instances[d].descriptor().content_hash(),
                }
                for d in sorted(self._entries.keys())
            ]
        }
        return sha256_hex(stable_json_dumps(state).encode("utf-8"))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize registry state for reporting."""
        return {
            "domains": [
                {
                    **self._entries[d].to_dict(),
                    "descriptor": self._instances[d].descriptor().to_dict(),
                }
                for d in self.list_all()
            ],
            "enabled_count": len(self.list_enabled()),
            "total_count": len(self._entries),
            "registry_hash": self.registry_hash(),
        }


# -----------------------------------------------------------------------------
# Default registry factory
# -----------------------------------------------------------------------------

_default_registry: Optional[DomainRegistry] = None


def get_default_registry() -> DomainRegistry:
    """
    Get the default domain registry.

    Lazily initializes and registers built-in cartridges.
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = _build_default_registry()
    return _default_registry


def _build_default_registry() -> DomainRegistry:
    """
    Build the default registry with built-in cartridges.

    Currently includes:
    - text.subword.v1 (Cartridge #0)
    - digit.v1 (proof cartridge)
    """
    registry = DomainRegistry()

    # Import cartridges here to avoid circular imports
    try:
        from .text_subword import TextSubwordCartridge

        registry.register(TextSubwordCartridge, priority=0)
    except ImportError:
        pass  # Cartridge not yet available

    try:
        from .digit_motif import DigitMotifCartridge

        registry.register(DigitMotifCartridge, priority=10)
    except ImportError:
        pass  # Cartridge not yet available

    return registry


def reset_default_registry() -> None:
    """Reset the default registry (mainly for testing)."""
    global _default_registry
    _default_registry = None
