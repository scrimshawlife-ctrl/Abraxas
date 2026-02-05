from __future__ import annotations

from .compare_routes import register as register_compare
from .export_routes import register as register_export
from .governance_routes import register as register_governance
from .index_routes import register as register_index
from .runs_routes import register as register_runs

__all__ = [
    "register_compare",
    "register_export",
    "register_governance",
    "register_index",
    "register_runs",
]
