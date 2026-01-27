from __future__ import annotations

from typing import Dict, List

from ..squares.grid import (
    extract_invariants_digit,
    extract_readings_letter,
    fill_grid,
    normalize_digits,
    normalize_letters,
)
from ..types import DomainDescriptor, EvidenceRow, Motif


def _compact_signature(invariants: Dict[str, List[int]]) -> str:
    parts = []
    for key in ("row_sums", "col_sums", "diag_sums", "row_mod9", "col_mod9", "diag_mod9"):
        vals = ",".join(str(v) for v in invariants.get(key, []))
        parts.append(f"{key}:{vals}")
    return "|".join(parts)


def _motif_complexity(length: int) -> float:
    return min(2.0, 1.0 + (length / 10.0))


class SquareConstraintCartridge:
    domain_id = "sdct.square_constraints.v1"

    def __init__(
        self,
        *,
        letter_size: int = 5,
        digit_size: int = 3,
        include_diagonals: bool = True,
        max_motifs: int = 150,
    ) -> None:
        self._letter_size = letter_size
        self._digit_size = digit_size
        self._include_diagonals = include_diagonals
        self._max_motifs = max_motifs

    def descriptor(self) -> DomainDescriptor:
        return DomainDescriptor(
            domain_id=self.domain_id,
            domain_name="Square Constraints",
            domain_version="1.0.0",
            motif_kind="square",
            alphabet="a-z/0-9",
            constraints=["letter_grid=5x5", "digit_grid=3x3"],
            params_schema_id="sdct.domain_params.v0",
        )

    def encode(self, item: dict) -> Dict[str, List[List[str]]]:
        blob = f"{item.get('title', '')}\n{item.get('text', '')}"
        letters = normalize_letters(blob)
        digits = normalize_digits(blob)
        letter_grid = fill_grid(letters, self._letter_size)
        digit_grid = fill_grid(digits, self._digit_size)
        return {"letter_grid": letter_grid, "digit_grid": digit_grid}

    def extract_motifs(self, sym: Dict[str, List[List[str]]]) -> List[Motif]:
        motifs: List[Motif] = []
        readings = extract_readings_letter(sym["letter_grid"], self._include_diagonals)
        for reading in readings:
            motifs.append(Motif(
                domain_id=self.domain_id,
                motif_id=f"sq.let:{reading}",
                motif_text=reading,
                motif_len=len(reading),
                motif_complexity=_motif_complexity(len(reading)),
                lane_hint="canary",
            ))
        invariants = extract_invariants_digit(sym["digit_grid"])
        signature = _compact_signature(invariants)
        motifs.append(Motif(
            domain_id=self.domain_id,
            motif_id=f"sq.inv:{signature}",
            motif_text=signature,
            motif_len=1,
            motif_complexity=2.0,
            lane_hint="canary",
        ))
        motifs = sorted(motifs, key=lambda m: (m.motif_id, m.motif_text))
        return motifs[: self._max_motifs]

    def emit_evidence(
        self,
        item: dict,
        motifs: List[Motif],
        event_key: str,
    ) -> List[EvidenceRow]:
        item_id = str(item.get("id", ""))
        source = str(item.get("source", ""))
        evidence: List[EvidenceRow] = []
        for motif in motifs:
            evidence.append(EvidenceRow(
                domain_id=motif.domain_id,
                motif_id=motif.motif_id,
                item_id=item_id,
                source=source,
                event_key=event_key,
                mentions=1,
                signals={"tap": 0.0, "sas": 0.0, "pfdi": 0.0},
                tags={"lane": motif.lane_hint, "tier": 2},
                provenance={},
            ))
        return evidence
