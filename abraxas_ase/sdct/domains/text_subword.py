from __future__ import annotations

from collections import Counter
from typing import List

from ...lexicon import Lexicon
from ...normalize import extract_tokens, filter_token, is_stopish, normalize_token, split_hyphenated
from ...scoring import letter_entropy, token_anagram_potential
from ...types import TokenRec
from ..types import DomainDescriptor, EvidenceRow, Motif, motif_id_from_text


def _letters_sorted(tok: str) -> str:
    bare = tok.replace("-", "").replace("'", "")
    return "".join(sorted(bare))


def _can_spell(parent_letters: Counter, sub: str) -> bool:
    need = Counter(sub)
    for ch, n in need.items():
        if parent_letters.get(ch, 0) < n:
            return False
    return True


def _token_records_for_item(item: dict, lex: Lexicon, min_len: int = 4) -> List[TokenRec]:
    out: List[TokenRec] = []
    item_id = str(item.get("id", ""))
    source = str(item.get("source", ""))
    blob = f"{item.get('title', '')}\n{item.get('text', '')}"
    raw_tokens = extract_tokens(blob)
    for raw in raw_tokens:
        nt = normalize_token(raw)
        if not nt:
            continue
        if is_stopish(nt, set(lex.stopwords)):
            continue
        cand = [nt]
        if "-" in nt:
            cand.extend(split_hyphenated(nt))
        for t in cand:
            if not filter_token(t, min_len=min_len):
                continue
            ls = _letters_sorted(t)
            if not ls:
                continue
            ent = letter_entropy(ls)
            ul = len(set(ls))
            tap = token_anagram_potential(len(ls), ul)
            out.append(TokenRec(
                token=t,
                norm=t,
                letters_sorted=ls,
                length=len(ls),
                unique_letters=ul,
                letter_entropy=float(ent),
                tap=float(tap),
                item_id=item_id,
                source=source,
            ))
    return sorted(out, key=lambda r: (r.letters_sorted, r.norm, r.source, r.item_id))


class TextSubwordCartridge:
    domain_id = "sdct.text_subword.v1"

    def __init__(
        self,
        *,
        lexicon: Lexicon,
        min_token_len: int = 4,
        min_sub_len: int = 3,
    ) -> None:
        self._lexicon = lexicon
        self._min_token_len = min_token_len
        self._min_sub_len = min_sub_len
        self._subs_all = sorted([w for w in lexicon.subwords if len(w) >= min_sub_len])

    def descriptor(self) -> DomainDescriptor:
        return DomainDescriptor(
            domain_id=self.domain_id,
            domain_name="Text Subword Motifs",
            domain_version="1.0.0",
            motif_kind="subword",
            alphabet="a-z",
            constraints=["alpha_only", "min_len>=3"],
            params_schema_id="sdct.domain_params.v0",
        )

    def encode(self, item: dict) -> List[TokenRec]:
        return _token_records_for_item(item, lex=self._lexicon, min_len=self._min_token_len)

    def extract_motifs(self, sym: List[TokenRec]) -> List[Motif]:
        motifs: List[Motif] = []
        for rec in sym:
            parent = Counter(rec.letters_sorted)
            for sub in self._subs_all:
                if _can_spell(parent, sub):
                    motif_id = motif_id_from_text(self.domain_id, "subword", sub)
                    motifs.append(Motif(
                        domain_id=self.domain_id,
                        motif_id=motif_id,
                        motif_text=sub,
                        motif_len=len(sub),
                        motif_complexity=1.0,
                        lane_hint="core",
                    ))
        return motifs

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
