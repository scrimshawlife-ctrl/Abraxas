"""Overlay Runner

Main entry point for running overlay operations.
"""

from typing import Any, Dict, Optional
from .adapter import OverlayAdapter
from .phases import Phase, PhaseManager
from .schema import OverlaySchema


class OverlayRunner:
    """Orchestrates overlay operations through phases."""

    def __init__(self, schema: Optional[OverlaySchema] = None):
        """Initialize the overlay runner.

        Args:
            schema: Optional schema for validation
        """
        self.schema = schema
        self.adapter = OverlayAdapter()
        self.phase_manager = PhaseManager()
        self._setup_default_handlers()

    def _setup_default_handlers(self):
        """Set up default phase handlers."""
        self.phase_manager.register_handler(Phase.INIT, self._init_handler)
        self.phase_manager.register_handler(Phase.PROCESS, self._process_handler)
        self.phase_manager.register_handler(Phase.TRANSFORM, self._transform_handler)
        self.phase_manager.register_handler(Phase.FINALIZE, self._finalize_handler)

    def _init_handler(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize the overlay operation.

        Args:
            data: Input data

        Returns:
            Initialized data
        """
        if self.schema:
            if not self.schema.validate(data):
                raise ValueError("Data validation failed")
        return data

    def _process_handler(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the data.

        Args:
            data: Data to process

        Returns:
            Processed data
        """
        return data

    def _transform_handler(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform the data.

        Args:
            data: Data to transform

        Returns:
            Transformed data
        """
        return data

    def _finalize_handler(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize the overlay operation.

        Args:
            data: Data to finalize

        Returns:
            Finalized data
        """
        return data

    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the complete overlay operation.

        Args:
            data: Input data

        Returns:
            Result of the overlay operation
        """
        result = self.phase_manager.execute(Phase.INIT, data)
        result = self.phase_manager.execute(Phase.PROCESS, result)
        result = self.phase_manager.execute(Phase.TRANSFORM, result)
        result = self.phase_manager.execute(Phase.FINALIZE, result)
        return result


def main():
    """Main entry point for CLI usage."""
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python -m abraxas.overlay.run <data.json>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        data = json.load(f)

    runner = OverlayRunner()
    result = runner.run(data)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
