from __future__ import annotations



def build_environment_inventory() -> list[dict[str, str]]:
    return [
        {"environment": "local", "class": "local", "lifecycle": "ephemeral", "owner": "developer"},
        {"environment": "dev", "class": "dev", "lifecycle": "iterative", "owner": "engineering"},
        {"environment": "test", "class": "test", "lifecycle": "validation", "owner": "qa"},
        {"environment": "staging", "class": "staging-like", "lifecycle": "promotion", "owner": "operator"},
        {"environment": "prod", "class": "production-like", "lifecycle": "steady", "owner": "operator"},
        {"environment": "drill", "class": "training/drill", "lifecycle": "scheduled", "owner": "resilience"},
    ]
