"""Overlay Runner

Reads an overlay request JSON object from stdin and writes a deterministic JSON
response to stdout.

Supports two modes:
1. JSON file input: python -m abraxas.overlay.run <data.json>
2. Stdin request: echo '<request>' | python -m abraxas.overlay.run
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, Optional

from .adapter import OverlayAdapter, parse_request, handle
from .phases import LegacyPhase, PhaseManager
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
        self.phase_manager.register_handler(LegacyPhase.INIT, self._init_handler)
        self.phase_manager.register_handler(LegacyPhase.PROCESS, self._process_handler)
        self.phase_manager.register_handler(LegacyPhase.TRANSFORM, self._transform_handler)
        self.phase_manager.register_handler(LegacyPhase.FINALIZE, self._finalize_handler)

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
        result = self.phase_manager.execute(LegacyPhase.INIT, data)
        result = self.phase_manager.execute(LegacyPhase.PROCESS, result)
        result = self.phase_manager.execute(LegacyPhase.TRANSFORM, result)
        result = self.phase_manager.execute(LegacyPhase.FINALIZE, result)
        return result


def main() -> int:
    """Main entry point for CLI usage.

    Supports two modes:
    1. JSON file input: python -m abraxas.overlay.run <data.json>
    2. Stdin request: echo '<request>' | python -m abraxas.overlay.run

    Returns:
        Exit code (0 for success, 1 for error)
    """
    if len(sys.argv) >= 2:
        # File mode - use OverlayRunner
        with open(sys.argv[1], 'r') as f:
            data = json.load(f)
        runner = OverlayRunner()
        result = runner.run(data)
        print(json.dumps(result, indent=2))
        return 0
    else:
        # Stdin mode - use request/response protocol
        raw = sys.stdin.read()
        try:
            req = parse_request(raw)
            resp = handle(req)
            sys.stdout.write(
                json.dumps(
                    {
                        "ok": resp.ok,
                        "overlay": resp.overlay,
                        "phase": resp.phase,
                        "request_id": resp.request_id,
                        "output": resp.output,
                        "error": resp.error,
                    },
                    sort_keys=True,
                )
            )
            return 0
        except Exception as e:
            sys.stdout.write(json.dumps({"ok": False, "error": str(e)}, sort_keys=True))
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
