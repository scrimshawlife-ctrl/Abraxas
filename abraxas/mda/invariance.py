from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import json
import os

from .types import DomainSignalPack, FusionGraph, MDARunEnvelope, sha256_hex, stable_json_dumps


@dataclass(frozen=True)
class InvarianceReport:
    input_hash: str
    repeat: int
    dsp_hashes: List[str]
    fusion_hashes: List[str]
    canon_invariant: bool
    drift_class: str

    def to_dict(self) -> dict:
        return {
            "input_hash": self.input_hash,
            "repeat": self.repeat,
            "dsp_hashes": self.dsp_hashes,
            "fusion_hashes": self.fusion_hashes,
            "canon_invariant": self.canon_invariant,
            "drift_class": self.drift_class,
        }


def compute_report(
    envelope: MDARunEnvelope,
    dsp_runs: List[Tuple[DomainSignalPack, ...]],
    fusion_runs: List[FusionGraph],
) -> InvarianceReport:
    input_hash = envelope.input_hash()

    dsp_hashes: List[str] = []
    fusion_hashes: List[str] = []

    for dsps in dsp_runs:
        # Canonical DSP set hash: hash the sorted per-pack stable hashes.
        h = sha256_hex(stable_json_dumps(sorted([d.stable_hash() for d in dsps])))
        dsp_hashes.append(h)

    for fg in fusion_runs:
        # Full fusion graph hash (nodes + edges) via FusionGraph.stable_hash().
        fusion_hashes.append(fg.stable_hash())

    canon_invariant = (len(set(dsp_hashes)) == 1) and (len(set(fusion_hashes)) == 1)
    drift_class = "none" if canon_invariant else "canon"

    return InvarianceReport(
        input_hash=input_hash,
        repeat=len(dsp_runs),
        dsp_hashes=dsp_hashes,
        fusion_hashes=fusion_hashes,
        canon_invariant=canon_invariant,
        drift_class=drift_class,
    )


def write_report(report: InvarianceReport, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2, sort_keys=True)
        f.write("\n")

