"""
Abraxas Governance Module

Enforces "complexity must pay rent" via:
- Rent manifests (what/cost/proof declarations)
- Rent checks (validation gates)
- Rent reports (compliance tracking)
"""

from .rent_manifest_loader import load_all_manifests, validate_manifest
from .rent_checks import (
    check_tests_exist,
    check_golden_files_declared,
    check_ledgers_declared,
    check_cost_model_present,
    check_operator_edges_declared,
    check_expected_cost_bounds,
    run_all_rent_checks,
    RentCheckReport,
)

__all__ = [
    "load_all_manifests",
    "validate_manifest",
    "check_tests_exist",
    "check_golden_files_declared",
    "check_ledgers_declared",
    "check_cost_model_present",
    "check_operator_edges_declared",
    "check_expected_cost_bounds",
    "run_all_rent_checks",
    "RentCheckReport",
]
