from __future__ import annotations

AUTHORITY_FLAGS = {
    "rollback_observation_ledger_write": True,
    "rollback_execution": False,
    "production_activation": False,
    "baseline_mutation": False,
    "runtime_config_write": False,
    "promotion": False,
    "execution": False,
    "scheduler": False,
}
