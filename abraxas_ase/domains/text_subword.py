from __future__ import annotations

from collections import Counter, defaultdict
from typing import Iterable, List, Optional, Sequence

from ..lexicon import Lexicon
from ..normalize import extract_tokens, filter_token, is_stopish, normalize_token, split_hyphenated
from ..scoring import letter_entropy, stable_round, token_anagram_potential
from ..types import ExactCollision, SubAnagramHit, TokenRec
from .types import DomainDescriptor, Motif, NormalizedEvidence


def _letters_sorted(tok: str) -> str:
    # tok already normalized; strip hyphen/apostrophe for letter pool
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


def build_token_records(items: List[dict], lex: Lexicon, min_len: int = 4) -> List[TokenRec]:
    out: List[TokenRec] = []
    for it in items:
        out.extend(_token_records_for_item(it, lex=lex, min_len=min_len))
    return sorted(out, key=lambda r: (r.letters_sorted, r.norm, r.source, r.item_id))


def tier1_exact_collisions(recs: List[TokenRec], min_sources: int = 2) -> List[ExactCollision]:
    bucket: dict[str, List[TokenRec]] = defaultdict(list)
    for r in recs:
        bucket[r.letters_sorted].append(r)

    collisions: List[ExactCollision] = []
    for k, rs in bucket.items():
        toks = sorted({x.norm for x in rs})
        if len(toks) < 2:
            continue
        sources = sorted({x.source for x in rs})
        if len(sources) < min_sources:
            continue
        ids = sorted({x.item_id for x in rs})
        collisions.append(ExactCollision(letters_sorted=k, tokens=toks, sources=sources, item_ids=ids))

    return sorted(collisions, key=lambda c: (c.letters_sorted, c.tokens))


def tier2_subanagrams(
    recs: List[TokenRec],
    lex: Lexicon,
    min_sub_len: int = 3,
    canary_subwords: Optional[set[str]] = None,
) -> List[SubAnagramHit]:
    core = sorted([w for w in lex.subwords if len(w) >= min_sub_len])
    canary = sorted([w for w in (canary_subwords or set()) if len(w) >= min_sub_len and w not in lex.subwords])
    subs_all = core + canary
    hits: List[SubAnagramHit] = []
    for r in recs:
        parent = Counter(r.letters_sorted)
        for sub in subs_all:
            if _can_spell(parent, sub):
                lane = "core" if sub in lex.subwords else "canary"
                hits.append(SubAnagramHit(
                    token=r.norm,
                    sub=sub,
                    tier=2,
                    verified=True,
                    lane=lane,
                    item_id=r.item_id,
                    source=r.source,
                ))
    uniq = {}
    for h in hits:
        key = (h.token, h.sub, h.lane, h.item_id, h.source)
        uniq[key] = h
    out = list(uniq.values())
    return sorted(out, key=lambda h: (h.sub, h.token, h.source, h.item_id))


def high_tap_tokens(recs: List[TokenRec], top_k: int = 25) -> List[dict]:
    best: dict[str, TokenRec] = {}
    for r in recs:
        prev = best.get(r.norm)
        if prev is None or r.tap > prev.tap:
            best[r.norm] = r
    ranked = sorted(best.values(), key=lambda r: (-r.tap, -r.letter_entropy, r.norm))
    ranked = ranked[:top_k]
    out: List[dict] = []
    for r in ranked:
        out.append({
            "token": r.norm,
            "tap": stable_round(r.tap),
            "letter_entropy": stable_round(r.letter_entropy),
            "length": r.length,
            "unique_letters": r.unique_letters,
        })
    return out


class TextSubwordCartridge:
    """
    LEGACY CARTRIDGE: This class uses domain_id "text.subword.v1" for backward compatibility.
    The SDCT rune-based system uses "sdct.text_subword.v1" instead (see abraxas_ase/sdct/domains/text_subword.py).
    This legacy implementation is not used in the current rune-based engine (see abraxas_ase/engine.py).
    """
    domain_id = "text.subword.v1"

    def __init__(
        self,
        *,
        lexicon: Lexicon,
        canary_subwords: Optional[Iterable[str]] = None,
        min_token_len: int = 4,
        min_sub_len: int = 3,
    ) -> None:
        self._lexicon = lexicon
        self._canary_subwords = sorted(set(canary_subwords or []))
        self._min_token_len = min_token_len
        self._min_sub_len = min_sub_len

        core = sorted([w for w in lexicon.subwords if len(w) >= min_sub_len])
        canary = sorted([
            w for w in self._canary_subwords
            if len(w) >= min_sub_len and w not in lexicon.subwords
        ])
        self._subs_all: Sequence[str] = core + canary

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
                    lane = "core" if sub in self._lexicon.subwords else "canary"
                    motifs.append(Motif(
                        domain_id=self.domain_id,
                        motif_id=f"subword:{sub}",
                        motif_text=sub,
                        motif_len=len(sub),
                        motif_complexity=1.0,
                        lane_hint=lane,
                    ))
        return motifs

    def emit_evidence(
        self,
        item: dict,
        motifs: List[Motif],
        event_key: str,
    ) -> List[NormalizedEvidence]:
        item_id = str(item.get("id", ""))
        source = str(item.get("source", ""))
        evidence: List[NormalizedEvidence] = []
        for motif in motifs:
            evidence.append(NormalizedEvidence(
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
