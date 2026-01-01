"""Confidence Decay Analyzer — trust calibration from runtime stability.

Reads runtime_events.log and computes confidence scores based on error rates.
Enables trust downgrading for unstable runes - not a decision engine, just metrics.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from abx.telemetry_reader import iter_events

OUT = Path(__file__).resolve().parents[1] / "data" / "telemetry"


def main() -> None:
    """Generate confidence decay metrics from runtime events."""
    OUT.mkdir(parents=True, exist_ok=True)

    # Count successes and failures per rune
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"ok": 0, "err": 0, "reject": 0})

    for ev in iter_events():
        rid = ev.get("rune_id")
        phase = ev.get("phase")

        if phase == "invoke_end":
            counts[rid]["ok"] += 1
        elif phase == "invoke_error":
            counts[rid]["err"] += 1
        elif phase == "reject":
            counts[rid]["reject"] += 1

    # Compute confidence scores
    confidence: dict[str, dict[str, Any]] = {}
    for rid, c in counts.items():
        total = c["ok"] + c["err"] + c["reject"]
        if total == 0:
            continue

        error_rate = (c["err"] + c["reject"]) / total
        # Simple heuristic: confidence = 1 - error_rate
        # This is a starting point - can be refined with more sophisticated models
        confidence_score = max(0.0, 1.0 - error_rate)

        confidence[rid] = {
            "invocations": total,
            "successes": c["ok"],
            "errors": c["err"],
            "rejections": c["reject"],
            "error_rate": round(error_rate, 4),
            "confidence_score": round(confidence_score, 4),
            "stability": _classify_stability(confidence_score),
        }

    # Write output
    path = OUT / "confidence_decay.json"
    path.write_text(
        json.dumps(confidence, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(f"Confidence decay analysis written to: {path}")
    print(f"Analyzed {len(confidence)} runes")

    # Print confidence summary to console
    if confidence:
        print("\nConfidence scores:")
        for rid in sorted(confidence.keys(), key=lambda r: confidence[r]["confidence_score"]):
            c = confidence[rid]
            print(f"  {rid}: {c['confidence_score']:.3f} ({c['stability']}) - {c['invocations']} invocations, {c['errors'] + c['rejections']} failures")


def _classify_stability(score: float) -> str:
    """Classify stability based on confidence score."""
    if score >= 0.95:
        return "excellent"
    elif score >= 0.85:
        return "good"
    elif score >= 0.70:
        return "fair"
    elif score >= 0.50:
        return "poor"
    else:
        return "critical"


if __name__ == "__main__":
    main()
