from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class DomainRegistration:
    domain_id: str
    domain_version: str
    rune_id: str
    enabled: bool


def get_enabled_domains() -> List[DomainRegistration]:
    domains = [
        DomainRegistration(
            domain_id="sdct.text_subword.v1",
            domain_version="1.0.0",
            rune_id="sdct.text_subword.v1",
            enabled=True,
        ),
        DomainRegistration(
            domain_id="sdct.digit_motif.v1",
            domain_version="1.0.0",
            rune_id="sdct.digit_motif.v1",
            enabled=True,
        ),
        DomainRegistration(
            domain_id="sdct.numogram_motif.v1",
            domain_version="1.0.0",
            rune_id="sdct.numogram_motif.v1",
            enabled=True,
        ),
        DomainRegistration(
            domain_id="sdct.square_constraints.v1",
            domain_version="1.0.0",
            rune_id="sdct.square_constraints.v1",
            enabled=True,
        ),
    ]
    return sorted([d for d in domains if d.enabled], key=lambda d: d.domain_id)
