from __future__ import annotations



def build_config_inventory() -> list[dict[str, object]]:
    return [
        {"config_key": "runtime.max_concurrency", "owner": "runtime", "secret": False, "affects": ["scheduler", "runtime"]},
        {"config_key": "observability.sample_rate", "owner": "observability", "secret": False, "affects": ["trace", "observability"]},
        {"config_key": "federation.contract_mode", "owner": "federation", "secret": False, "affects": ["federation"]},
        {"config_key": "secrets.runtime_token", "owner": "operator", "secret": True, "affects": ["runtime"]},
        {"config_key": "env.override.policy_bypass", "owner": "operator", "secret": False, "affects": ["decision", "boundary"]},
    ]
