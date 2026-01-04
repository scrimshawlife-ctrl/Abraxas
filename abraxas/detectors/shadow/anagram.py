from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple
import re
import unicodedata

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.lexicon.anagram_lexicon_v0 import DEFAULT_LEXICON_V0, AnagramLexiconV0
from abraxas.detectors.shadow.util import ok, not_computable
from abraxas.detectors.shadow.types import ShadowResult


_ALNUM_RE = re.compile(r"[a-z0-9]+")


def _norm_ascii_lower(s: str) -> str:
    # Deterministic unicode normalization: NFKD then drop non-ascii
    s2 = unicodedata.normalize("NFKD", s)
    s2 = s2.encode("ascii", "ignore").decode("ascii")
    s2 = s2.lower()
    return s2


def _norm_token_letters(s: str) -> str:
    s2 = _norm_ascii_lower(s)
    parts = _ALNUM_RE.findall(s2)
    return "".join(parts)


def _letter_counts(s: str) -> Tuple[int, ...]:
    # 26 letters + 10 digits (optional). Here: letters+digits; stable vector length 36.
    # a-z => 0-25, 0-9 => 26-35
    v = [0] * 36
    for ch in s:
        o = ord(ch)
        if 97 <= o <= 122:
            v[o - 97] += 1
        elif 48 <= o <= 57:
            v[26 + (o - 48)] += 1
    return tuple(v)


def _counts_sub(a: Tuple[int, ...], b: Tuple[int, ...]) -> Optional[Tuple[int, ...]]:
    # return a-b if possible else None
    out = []
    for i in range(len(a)):
        x = a[i] - b[i]
        if x < 0:
            return None
        out.append(x)
    return tuple(out)


def _counts_is_zero(c: Tuple[int, ...]) -> bool:
    for x in c:
        if x != 0:
            return False
    return True


def _counts_sum(c: Tuple[int, ...]) -> int:
    return sum(c)


@dataclass(frozen=True)
class AnagramBudgets:
    max_token_len: int = 24
    max_candidates_per_token: int = 25
    max_states: int = 50_000  # DP state expansions cap
    max_words_per_phrase: int = 3


@dataclass(frozen=True)
class AnagramConfig:
    budgets: AnagramBudgets = AnagramBudgets()
    lexicon: AnagramLexiconV0 = DEFAULT_LEXICON_V0
    # If true, allow digits in matching. (Counts vector includes digits always; this toggles lexicon normalization.)
    allow_digits: bool = True


def _prep_lexicon(cfg: AnagramConfig) -> Tuple[List[Tuple[str, Tuple[int, ...]]], List[Tuple[str, Tuple[int, ...]]]]:
    # Return (words, phrases) as (text, counts) pairs with deterministic ordering
    words = []
    for w in sorted(cfg.lexicon.words):
        nw = _norm_token_letters(w)
        if not cfg.allow_digits:
            nw = "".join(ch for ch in nw if "a" <= ch <= "z")
        if nw:
            words.append((w, _letter_counts(nw)))
    phrases = []
    for p in sorted(cfg.lexicon.phrases):
        np = _norm_token_letters(p)
        if not cfg.allow_digits:
            np = "".join(ch for ch in np if "a" <= ch <= "z")
        if np:
            phrases.append((p, _letter_counts(np)))
    return words, phrases


def _score_candidate(
    *,
    src_norm: str,
    dst_text: str,
    dst_norm: str,
    lexicon_hit: float,
    context: Optional[Dict[str, Any]],
) -> Dict[str, float]:
    # Deterministic heuristic scoring only; no external data.
    # rarity: longer normalized strings are rarer; cap at 1
    rarity = min(1.0, max(0.0, (len(dst_norm) - 6) / 12.0))
    # collision risk: very short outputs collide more
    collision_risk = 1.0 - min(1.0, max(0.0, (len(dst_norm) - 3) / 10.0))

    # context_fit: simple domain/subdomain prior
    dom = str((context or {}).get("domain", ""))
    sub = str((context or {}).get("subdomain", ""))
    fit = 0.5
    if "memes" in dom or "culture" in dom:
        fit += 0.1
    if "slang" in sub or "drift" in sub:
        fit += 0.1
    fit = max(0.0, min(1.0, fit))

    # entropy_drop: identical multiset implies same letter mass; measure compressibility by removing spaces/punct
    entropy_drop = 1.0 if (len(dst_norm) == len(src_norm)) else max(0.0, 1.0 - abs(len(dst_norm) - len(src_norm)) / 10.0)

    # overall: weighted sum (shadow-only)
    overall = (
        0.35 * lexicon_hit +
        0.20 * rarity +
        0.20 * fit +
        0.15 * entropy_drop +
        0.10 * (1.0 - collision_risk)
    )
    overall = max(0.0, min(1.0, overall))
    return {
        "lexicon_hit": float(lexicon_hit),
        "rarity": float(rarity),
        "context_fit": float(fit),
        "collision_risk": float(collision_risk),
        "entropy_drop": float(entropy_drop),
        "overall": float(overall),
    }


def _dp_word_splits(
    target_counts: Tuple[int, ...],
    word_items: List[Tuple[str, Tuple[int, ...]]],
    *,
    budgets: AnagramBudgets,
) -> List[List[str]]:
    """
    Bounded DP over letter-count remainders to assemble up to N words.
    Returns list of word sequences (as original lexicon strings).
    Deterministic ordering: BFS with lexicon order.
    """
    # State is remainder counts; store first-seen sequences only (bounded)
    from collections import deque

    q = deque()
    q.append((target_counts, []))
    seen = set([target_counts])
    out: List[List[str]] = []
    expansions = 0

    while q:
        rem, seq = q.popleft()
        if _counts_is_zero(rem):
            out.append(seq)
            continue
        if len(seq) >= budgets.max_words_per_phrase:
            continue

        for word_text, wc in word_items:
            nxt = _counts_sub(rem, wc)
            if nxt is None:
                continue
            expansions += 1
            if expansions > budgets.max_states:
                return out
            if nxt not in seen:
                seen.add(nxt)
                q.append((nxt, seq + [word_text]))
    return out


def detect_shadow_anagrams(
    tokens: Iterable[str],
    *,
    context: Optional[Dict[str, Any]] = None,
    config: Optional[AnagramConfig] = None,
    evidence_refs: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Shadow Anagram Detector v1
    - Deterministic
    - Budgeted
    - Lexicon-guided (targets + DP word splits)
    - Evidence gating: emits evidence refs only if provided
    """
    cfg = config or AnagramConfig()
    budgets = cfg.budgets

    tok_list = [str(t) for t in tokens if str(t).strip()]
    tok_list = sorted(set(tok_list))  # deterministic + dedupe

    lex_words, lex_phrases = _prep_lexicon(cfg)
    ev = [str(x) for x in (evidence_refs or []) if str(x).strip()]
    has_evidence = len(ev) > 0

    candidates_all: List[Dict[str, Any]] = []

    for t in tok_list:
        src_norm = _norm_token_letters(t)
        if not src_norm:
            continue
        if len(src_norm) > budgets.max_token_len:
            continue
        src_counts = _letter_counts(src_norm)

        # 1) Direct phrase hits
        for phrase_text, pc in lex_phrases:
            if pc == src_counts:
                dst_norm = _norm_token_letters(phrase_text)
                scores = _score_candidate(
                    src_norm=src_norm,
                    dst_text=phrase_text,
                    dst_norm=dst_norm,
                    lexicon_hit=1.0,
                    context=context,
                )
                item = {
                    "src": t,
                    "dst": phrase_text,
                    "ops": ["normalize:nfkd_ascii_lower", "strip_non_alnum", "counts_match"],
                    "scores": scores,
                    "notes": ["lexicon_phrase_exact_multiset_match"],
                }
                if has_evidence:
                    item["evidence_refs"] = ev
                candidates_all.append(item)

        # 2) Single-word hits
        for word_text, wc in lex_words:
            if wc == src_counts:
                dst_norm = _norm_token_letters(word_text)
                scores = _score_candidate(
                    src_norm=src_norm,
                    dst_text=word_text,
                    dst_norm=dst_norm,
                    lexicon_hit=1.0,
                    context=context,
                )
                item = {
                    "src": t,
                    "dst": word_text,
                    "ops": ["normalize:nfkd_ascii_lower", "strip_non_alnum", "counts_match"],
                    "scores": scores,
                    "notes": ["lexicon_word_exact_multiset_match"],
                }
                if has_evidence:
                    item["evidence_refs"] = ev
                candidates_all.append(item)

        # 3) DP word split candidates (up to N words)
        splits = _dp_word_splits(src_counts, lex_words, budgets=budgets)
        for seq in splits:
            if not seq:
                continue
            dst_text = " ".join(seq)
            dst_norm = _norm_token_letters(dst_text)
            # lexicon_hit here is strong but not absolute; split can be trivial
            scores = _score_candidate(
                src_norm=src_norm,
                dst_text=dst_text,
                dst_norm=dst_norm,
                lexicon_hit=0.8,
                context=context,
            )
            item = {
                "src": t,
                "dst": dst_text,
                "ops": ["normalize:nfkd_ascii_lower", "strip_non_alnum", "dp_word_split"],
                "scores": scores,
                "notes": ["lexicon_dp_split"],
            }
            if has_evidence:
                item["evidence_refs"] = ev
            candidates_all.append(item)

    # Deterministic ranking + cap
    candidates_all.sort(key=lambda c: (-float(c["scores"]["overall"]), str(c["dst"]), str(c["src"])))
    candidates_all = candidates_all[: budgets.max_candidates_per_token * max(1, len(tok_list))]

    payload = {
        "shadow_anagram_v1": {
            "candidates": candidates_all,
            "not_computable": False,
        }
    }
    # Provenance hash (deterministic)
    payload_hash = sha256_hex(canonical_json(payload))
    payload["shadow_anagram_v1"]["artifact_hash"] = payload_hash
    payload["shadow_anagram_v1"]["provenance"] = {
        "module": "shadow_anagram_v1",
        "budgets": {
            "max_token_len": budgets.max_token_len,
            "max_candidates_per_token": budgets.max_candidates_per_token,
            "max_states": budgets.max_states,
            "max_words_per_phrase": budgets.max_words_per_phrase,
        },
        "has_evidence": has_evidence,
    }
    if has_evidence:
        payload["shadow_anagram_v1"]["evidence_refs"] = ev

    return payload


def run_shadow_anagrams(ctx: Dict[str, Any]) -> ShadowResult:
    """
    Shadow Anagram Detector — context-based adapter using canonical helpers.

    Wraps detect_shadow_anagrams() with ok() / not_computable() semantics.

    Args:
        ctx: Context dict with:
            - tokens: List[str] (required) - tokens to analyze for anagrams
            - context: Optional[Dict] - domain/subdomain context
            - config: Optional[AnagramConfig] - detector configuration
            - evidence_refs: Optional[List[str]] - evidence references

    Returns:
        ShadowResult with canonical status/value/missing/error structure
    """
    tokens = ctx.get("tokens")
    if tokens is None:
        return not_computable(["tokens"])

    # Validate tokens is iterable of strings
    if not hasattr(tokens, "__iter__"):
        return not_computable(["tokens"], provenance={"reason": "tokens_not_iterable"})

    # Convert to list and filter empty
    tok_list = [str(t) for t in tokens if str(t).strip()]
    if not tok_list:
        return not_computable(["tokens"], provenance={"reason": "no_valid_tokens"})

    # Extract optional parameters from context
    inner_context = ctx.get("context")
    config = ctx.get("config")
    evidence_refs = ctx.get("evidence_refs")

    # Call the core detector
    payload = detect_shadow_anagrams(
        tokens=tok_list,
        context=inner_context,
        config=config,
        evidence_refs=evidence_refs,
    )

    # Extract provenance from payload for ShadowResult
    inner = payload.get("shadow_anagram_v1", {})
    provenance = {
        "module": "shadow_anagram_v1",
        "artifact_hash": inner.get("artifact_hash"),
        "has_evidence": inner.get("provenance", {}).get("has_evidence", False),
    }

    return ok(payload, provenance=provenance)
