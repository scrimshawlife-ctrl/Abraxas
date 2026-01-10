"""Linguistic feature extractor for V1–V6 metrics."""

from __future__ import annotations

from collections import Counter
from typing import Dict, List

from abraxas.linguistics.normalize import shingle, tokenize
from abraxas.metric_extractors.base import MetricExtractor, MetricPoint, packet_hash

OUTRAGE_LEXEMES = {"outrage", "disgust", "scandal", "rage"}
MORAL_TERMS = {"good", "evil", "virtue", "sin"}
BUZZWORDS = {"ai", "blockchain", "metaverse", "quantum"}
CALL_TO_ACTION = {"must", "now", "join", "act"}
STORY_ARC = {"then", "but", "therefore"}


class LinguisticsExtractor(MetricExtractor):
    extractor_name = "linguistics"
    version = "0.1"

    def accepts(self, source_id: str) -> bool:
        return source_id.startswith("LINGUISTIC_")

    def extract(self, packets: List[Dict[str, any]], run_ctx: Dict[str, any]) -> List[MetricPoint]:
        points: List[MetricPoint] = []
        for packet in packets:
            payload = packet.get("payload") or {}
            items = payload.get("items") or []
            tokens = []
            for item in items:
                tokens.extend(tokenize(item.get("text", "")))

            total_tokens = len(tokens)
            unique_ratio = len(set(tokens)) / total_tokens if total_tokens else None
            item_count = len(items)
            shingles = shingle(tokens, 3)
            dup_rate = 1 - (len(set(shingles)) / len(shingles)) if shingles else None

            def rate(term_set: set[str]) -> float | None:
                if not total_tokens:
                    return None
                return sum(1 for t in tokens if t in term_set) / total_tokens

            ts = packet.get("observed_at_utc") or packet.get("window_end_utc") or "1970-01-01T00:00:00Z"
            window_start = packet.get("window_start_utc")
            window_end = packet.get("window_end_utc")
            base_prov = {
                "packet_hash": packet_hash(packet),
                "extractor_version": self.extractor_version(),
            }

            points.extend(
                [
                    MetricPoint(
                        metric_id="linguistics.token_count_total",
                        value=float(total_tokens) if total_tokens else None,
                        ts_utc=ts,
                        window_start_utc=window_start,
                        window_end_utc=window_end,
                        source_id=packet.get("source_id"),
                        computability="computed" if total_tokens else "not_computable",
                        provenance={**base_prov, "notes": "token count"},
                    ),
                    MetricPoint(
                        metric_id="linguistics.unique_token_ratio",
                        value=unique_ratio,
                        ts_utc=ts,
                        window_start_utc=window_start,
                        window_end_utc=window_end,
                        source_id=packet.get("source_id"),
                        computability="computed" if unique_ratio is not None else "not_computable",
                        provenance={**base_prov, "notes": "unique token ratio"},
                    ),
                    MetricPoint(
                        metric_id="linguistics.item_count",
                        value=float(item_count) if item_count else None,
                        ts_utc=ts,
                        window_start_utc=window_start,
                        window_end_utc=window_end,
                        source_id=packet.get("source_id"),
                        computability="computed" if item_count else "not_computable",
                        provenance={**base_prov, "notes": "item count"},
                    ),
                    MetricPoint(
                        metric_id="linguistics.duplication_rate",
                        value=dup_rate,
                        ts_utc=ts,
                        window_start_utc=window_start,
                        window_end_utc=window_end,
                        source_id=packet.get("source_id"),
                        computability="computed" if dup_rate is not None else "not_computable",
                        provenance={**base_prov, "notes": "duplication rate"},
                    ),
                    MetricPoint(
                        metric_id="linguistics.outrage_lexeme_rate",
                        value=rate(OUTRAGE_LEXEMES),
                        ts_utc=ts,
                        window_start_utc=window_start,
                        window_end_utc=window_end,
                        source_id=packet.get("source_id"),
                        computability="computed" if total_tokens else "not_computable",
                        provenance={**base_prov, "notes": "outrage lexeme rate"},
                    ),
                    MetricPoint(
                        metric_id="linguistics.moral_term_saturation",
                        value=rate(MORAL_TERMS),
                        ts_utc=ts,
                        window_start_utc=window_start,
                        window_end_utc=window_end,
                        source_id=packet.get("source_id"),
                        computability="computed" if total_tokens else "not_computable",
                        provenance={**base_prov, "notes": "moral term saturation"},
                    ),
                    MetricPoint(
                        metric_id="linguistics.buzzword_rate",
                        value=rate(BUZZWORDS),
                        ts_utc=ts,
                        window_start_utc=window_start,
                        window_end_utc=window_end,
                        source_id=packet.get("source_id"),
                        computability="computed" if total_tokens else "not_computable",
                        provenance={**base_prov, "notes": "buzzword rate"},
                    ),
                    MetricPoint(
                        metric_id="linguistics.call_to_action_rate",
                        value=rate(CALL_TO_ACTION),
                        ts_utc=ts,
                        window_start_utc=window_start,
                        window_end_utc=window_end,
                        source_id=packet.get("source_id"),
                        computability="computed" if total_tokens else "not_computable",
                        provenance={**base_prov, "notes": "call to action rate"},
                    ),
                    MetricPoint(
                        metric_id="linguistics.story_arc_marker_rate",
                        value=rate(STORY_ARC),
                        ts_utc=ts,
                        window_start_utc=window_start,
                        window_end_utc=window_end,
                        source_id=packet.get("source_id"),
                        computability="computed" if total_tokens else "not_computable",
                        provenance={**base_prov, "notes": "story arc marker rate"},
                    ),
                ]
            )
        return points
