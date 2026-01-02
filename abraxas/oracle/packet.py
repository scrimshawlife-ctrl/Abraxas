from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple
import json

from abraxas.mda.types import sha256_hex, stable_json_dumps


@dataclass(frozen=True)
class OraclePacketRun:
    run_id: str
    payload_path: str
    mode: str
    domains: Tuple[str, ...]
    subdomains: Tuple[str, ...]
    signal_slice_hash: str
    artifacts: Tuple[str, ...]

    def to_json(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "payload_path": self.payload_path,
            "mode": self.mode,
            "domains": list(self.domains),
            "subdomains": list(self.subdomains),
            "signal_slice_hash": self.signal_slice_hash,
            "artifacts": list(self.artifacts),
        }


@dataclass(frozen=True)
class OraclePacket:
    version: str
    env: str
    run_at: str
    seed: int
    runs: Tuple[OraclePacketRun, ...]

    def to_json(self) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "oracle_packet_v0_1": {
                "meta": {
                    "version": self.version,
                    "env": self.env,
                    "run_at": self.run_at,
                    "seed": self.seed,
                },
                "runs": [r.to_json() for r in self.runs],
            }
        }
        # Hash excludes itself; deterministic via stable_json_dumps.
        body["oracle_packet_hash"] = sha256_hex(stable_json_dumps(body))
        return body


def write_packet(packet: OraclePacket, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(packet.to_json(), f, ensure_ascii=False, indent=2, sort_keys=True)

