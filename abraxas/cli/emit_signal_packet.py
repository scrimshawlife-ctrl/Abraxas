"""Emit AbraxasSignalPacket.v0 JSON from payload input.

Usage:
  python -m abraxas.cli.emit_signal_packet --input payload.json --tier academic --lane canon > packet.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from abraxas.signal.exporter import emit_signal_packet


def _load_payload(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Input payload not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Input payload must be a JSON object.")
    return data


def _parse_json_arg(raw: Optional[str], default: Any) -> Any:
    if raw is None:
        return default
    return json.loads(raw)


def _dump_packet(packet: Dict[str, Any]) -> str:
    return json.dumps(
        packet,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit AbraxasSignalPacket JSON.")
    parser.add_argument("--input", help="Path to JSON payload input")
    parser.add_argument("--tier", required=True, choices=["psychonaut", "academic", "enterprise"])
    parser.add_argument("--lane", required=True, choices=["canon", "shadow", "sandbox"])
    parser.add_argument("--out", help="Output path (default: stdout)")
    parser.add_argument(
        "--confidence",
        help='JSON object for confidence (default: "{}")',
    )
    parser.add_argument(
        "--provenance-status",
        choices=["complete", "partial", "missing"],
        help="Override provenance status",
    )
    parser.add_argument(
        "--invariance-status",
        choices=["pass", "fail", "not_evaluated"],
        help="Override invariance status",
    )
    parser.add_argument(
        "--drift-flags",
        help="Comma-separated drift flags (default: none)",
    )
    parser.add_argument(
        "--rent-status",
        choices=["paid", "unpaid", "not_applicable"],
        help="Override rent status",
    )
    parser.add_argument(
        "--not-computable-regions",
        help="JSON array for not_computable_regions (default: [])",
    )
    parser.add_argument("--run-id", help="Optional run_id for deterministic signal_id")
    parser.add_argument("--timestamp-utc", help="Optional timestamp override (ISO-8601)")

    args = parser.parse_args()

    if not args.input:
        print("error: --input is required (no internal payload generator available).")
        return 2

    payload = _load_payload(Path(args.input))

    drift_flags: List[str] = []
    if args.drift_flags:
        drift_flags = [flag.strip() for flag in args.drift_flags.split(",") if flag.strip()]

    confidence = _parse_json_arg(args.confidence, {})
    if confidence is None:
        confidence = {}
    if not isinstance(confidence, dict):
        raise ValueError("--confidence must be a JSON object")

    not_computable_regions = _parse_json_arg(args.not_computable_regions, [])
    if not isinstance(not_computable_regions, list):
        raise ValueError("--not-computable-regions must be a JSON array")

    packet = emit_signal_packet(
        payload=payload,
        tier=args.tier,
        lane=args.lane,
        confidence=confidence,
        provenance_status=args.provenance_status,
        invariance_status=args.invariance_status,
        drift_flags=drift_flags,
        rent_status=args.rent_status,
        not_computable_regions=not_computable_regions,
        run_id=args.run_id,
        timestamp_utc=args.timestamp_utc,
    )

    rendered = _dump_packet(packet)
    if args.out:
        out_path = Path(args.out)
        out_path.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
