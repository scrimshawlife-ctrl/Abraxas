from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import json
import os

from .types import sha256_hex, stable_json_dumps


@dataclass(frozen=True)
class RunEntry:
    run_id: str
    input_hash: str
    dsp_hash: str
    fusion_hash: str

    def to_json(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "input_hash": self.input_hash,
            "dsp_hash": self.dsp_hash,
            "fusion_hash": self.fusion_hash,
        }


@dataclass(frozen=True)
class SessionLedger:
    """
    Minimal session ledger for the MDA practice rig.

    Write-once semantics: the test suite treats the serialized form as an
    immutable artifact and pins its stable hash in a golden file.
    """

    env: str
    mode: str
    seed: int
    repeat: int
    runs: List[RunEntry]

    def to_json(self) -> Dict[str, Any]:
        return {
            "env": self.env,
            "mode": self.mode,
            "seed": self.seed,
            "repeat": self.repeat,
            "runs": [r.to_json() for r in self.runs],
        }

    def stable_hash(self) -> str:
        # Important: hash the canonical body (no embedded hash field).
        return sha256_hex(stable_json_dumps(self.to_json()))


def build_run_entry(*, canon: Dict[str, Any], run_idx: int) -> RunEntry:
    """
    Deterministic run entry builder.
    """
    input_hash = sha256_hex(stable_json_dumps(canon))
    dsp_hash = sha256_hex(stable_json_dumps({"kind": "dsp", "canon": canon}))
    fusion_hash = sha256_hex(stable_json_dumps({"kind": "fusion", "canon": canon}))
    return RunEntry(
        run_id=f"run_{run_idx:02d}",
        input_hash=input_hash,
        dsp_hash=dsp_hash,
        fusion_hash=fusion_hash,
    )


def write_session_ledger(session: SessionLedger, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        obj = session.to_json()
        # Additive: embed the stable hash for easy pinning.
        obj["session_ledger_hash"] = session.stable_hash()
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)

