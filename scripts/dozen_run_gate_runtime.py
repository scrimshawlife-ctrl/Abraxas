"""Backward-compatible shim for the canonical N-run gate module."""

from scripts.n_run_gate_runtime import _gate_note, main

__all__ = ["main", "_gate_note"]


if __name__ == "__main__":
    raise SystemExit(main())
