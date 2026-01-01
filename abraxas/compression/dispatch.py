# Pure wrapper for compression detection (v0.1)
# Canon: detector-only (no network, no filesystem writes, no subprocess)

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List

from abraxas.linguistic.transparency import TransparencyLexicon
from abraxas.pipelines.sco_pipeline import SCOPipeline


def _collect_tokens(lexicon: List[Dict[str, Any]]) -> List[str]:
    tokens: List[str] = []
    for entry in lexicon:
        canonical = entry.get("canonical")
        if canonical:
            tokens.append(str(canonical))
        for variant in entry.get("variants", []):
            tokens.append(str(variant))
    return tokens


def detect_compression(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    payload expected:
      - text_event: str (optional if records provided)
      - records: list[dict] (optional)
      - lexicon: list[dict]
      - config: dict (optional; supports domain)
    returns:
      - compression_event: dict | None
      - metrics: dict
      - labels: list[str]
      - confidence: float
      - events: list[dict]
    """
    records = payload.get("records")
    if not records and payload.get("text_event"):
        records = [{"id": payload.get("id", "event"), "text": payload["text_event"]}]

    lexicon = payload.get("lexicon", [])
    if not records or not lexicon:
        return {
            "compression_event": None,
            "metrics": {"event_count": 0},
            "labels": ["no_input"],
            "confidence": 0.0,
            "events": [],
        }

    config = payload.get("config", {}) or {}
    domain = config.get("domain", "general")

    transparency = TransparencyLexicon.build(_collect_tokens(lexicon))
    pipeline = SCOPipeline(transparency)
    events = pipeline.run(records=records, lexicon=lexicon, domain=domain)
    event_dicts = [asdict(event) for event in events]

    return {
        "compression_event": event_dicts[0] if event_dicts else None,
        "metrics": {"event_count": len(event_dicts)},
        "labels": ["compression_detected"] if event_dicts else [],
        "confidence": 1.0 if event_dicts else 0.0,
        "events": event_dicts,
    }
