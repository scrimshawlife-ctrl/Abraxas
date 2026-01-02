from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple
import hashlib
import json


def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def stable_json_dumps(obj: Any) -> str:
    """
    Canonical JSON for hashing: sorted keys, compact separators, UTF-8.
    """
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class MDARunEnvelope:
    env: str
    run_at_iso: str
    seed: int
    promotion_enabled: bool
    enabled_domains: Tuple[str, ...]
    enabled_subdomains: Tuple[str, ...]
    inputs: Dict[str, Any]

    def input_hash(self) -> str:
        return sha256_hex(stable_json_dumps(self.inputs or {}))

    def to_json(self) -> Dict[str, Any]:
        return {
            "env": self.env,
            "run_at_iso": self.run_at_iso,
            "seed": self.seed,
            "promotion_enabled": self.promotion_enabled,
            "enabled_domains": list(self.enabled_domains),
            "enabled_subdomains": list(self.enabled_subdomains),
            "inputs": self.inputs or {},
            "input_hash": self.input_hash(),
        }


FusionGraph = Dict[str, Any]

