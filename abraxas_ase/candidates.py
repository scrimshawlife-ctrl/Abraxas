from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Tuple

from .provenance import stable_json_dumps
from .hysteresis import default_state, state_from_dict, state_to_dict


@dataclass(frozen=True)
class CandidateRec:
    candidate: str                 # token or subword
    kind: str                      # "token" | "subword"
    date_first_seen: str           # YYYY-MM-DD
    date_last_seen: str            # YYYY-MM-DD
    days_seen: int
    sources: List[str]             # sorted unique
    events: List[str]              # sorted unique
    tap_max: float                 # for tokens; 0 for subwords
    sas_sum: float                 # summed salience contributions
    pfdi_max: float                # max pfdi seen on any event/sub match
    mentions_total: int            # total mentions across days
    lane: str                      # "candidate"|"shadow"|"canary"|"core"
    hysteresis: Dict[str, Any] = field(default_factory=lambda: state_to_dict(default_state()))
    cycles_alive: int = 0
    cycles_stable: int = 0

    def to_json(self) -> str:
        return stable_json_dumps(asdict(self))


def load_candidates_jsonl(path: str) -> Dict[Tuple[str, str], CandidateRec]:
    """
    Returns dict keyed by (kind, candidate). Deterministic (last write wins if dup).
    """
    out: Dict[Tuple[str, str], CandidateRec] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                obj = json.loads(s)
                key = (obj["kind"], obj["candidate"])
                out[key] = CandidateRec(
                    candidate=obj["candidate"],
                    kind=obj["kind"],
                    date_first_seen=obj["date_first_seen"],
                    date_last_seen=obj["date_last_seen"],
                    days_seen=int(obj["days_seen"]),
                    sources=list(obj["sources"]),
                    events=list(obj["events"]),
                    tap_max=float(obj["tap_max"]),
                    sas_sum=float(obj["sas_sum"]),
                    pfdi_max=float(obj["pfdi_max"]),
                    mentions_total=int(obj["mentions_total"]),
                    lane=obj["lane"],
                    hysteresis=state_to_dict(state_from_dict(obj.get("hysteresis"))),
                    cycles_alive=int(obj.get("cycles_alive", 0)),
                    cycles_stable=int(obj.get("cycles_stable", 0)),
                )
    except FileNotFoundError:
        return {}
    return out


def write_candidates_jsonl(path: str, recs: List[CandidateRec]) -> None:
    """
    Writes full ledger snapshot deterministically (sorted by kind, candidate).
    Snapshot style > append-only for CI stability. (You can also store append separately.)
    """
    recs_sorted = sorted(recs, key=lambda r: (r.kind, r.candidate))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for r in recs_sorted:
            f.write(r.to_json() + "\n")
