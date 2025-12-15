"""Overlay Adapter

Handles adaptation logic for overlay operations.
"""


class OverlayAdapter:
    """Adapter for overlay transformations and mappings."""

    def __init__(self):
        """Initialize the overlay adapter."""
        self.adapters = {}

    def register(self, name: str, adapter_fn):
        """Register an adapter function.

        Args:
            name: Name of the adapter
            adapter_fn: Function to perform adaptation
        """
        self.adapters[name] = adapter_fn

    def adapt(self, name: str, data):
        """Apply an adapter to data.

        Args:
            name: Name of the adapter to use
            data: Data to adapt

        Returns:
            Adapted data
        """
        if name not in self.adapters:
            raise ValueError(f"Adapter '{name}' not found")
        return self.adapters[name](data)
