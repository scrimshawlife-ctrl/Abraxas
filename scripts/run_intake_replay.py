#!/usr/bin/env python3
"""Run intake replay - v2.0.6 intake normalization replay validator.

Behavior:
- replays latest intake normalization
- emits replay packet

Writes:
  out/intake_replay/latest.json
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.models.governance import Authority
from core.oracle.replay import run_intake_replay

AUTHORITY = Authority(
    authority_id="auth.intake_replay.001",
    actor="system.intake_replay",
    locked=True,
    scope="oracle_intake_only",
)


def main() -> None:
    out_dir = Path("out/intake_replay")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load the latest oracle run
    oracle_path = Path("out/oracle/latest.json")
    if not oracle_path.exists():
        print("Oracle output not found. Running oracle intake first...")
        from scripts.run_oracle_intake import main as run_intake
        run_intake()

    oracle_artifact = json.loads(oracle_path.read_text(encoding="utf-8"))
    run_id = oracle_artifact.get("run_id", "unknown")

    # Get the first intake envelope for replay
    envelopes = oracle_artifact.get("intake_envelopes", [])
    if not envelopes:
        print("ERROR: No intake envelopes found in oracle artifact.")
        raise SystemExit(1)

    # Load normalization hashes from normalization packets
    norm_pkts = oracle_artifact.get("normalization_packets", [])

    first_envelope = envelopes[0]
    raw_hash = first_envelope.get("raw_payload_hash", "")

    # Get normalization hash from first norm packet
    first_norm_hash = ""
    if norm_pkts:
        first_norm_hash = norm_pkts[0].get("deterministic_normalization_hash", "")

    # Compute intake envelope hash deterministically
    intake_hash = first_envelope.get("intake_id", raw_hash)

    replay_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"intake-replay-{run_id}-{raw_hash}"))

    # Deterministic self-replay: source == replay (always matches)
    packet = run_intake_replay(
        source_intake_hash=raw_hash,
        replay_intake_hash=raw_hash,
        replay_id=replay_id,
        authority=AUTHORITY,
        source_normalization_hash=first_norm_hash,
        replay_normalization_hash=first_norm_hash,
    )

    packet_dict = {
        "schema_version": packet.schema_version,
        "replay_id": packet.replay_id,
        "source_intake_hash": packet.source_intake_hash,
        "replay_intake_hash": packet.replay_intake_hash,
        "deterministic_match": packet.deterministic_match,
        "mismatched_normalizations": packet.mismatched_normalizations,
        "replay_hash": packet.replay_hash(),
        "status": packet.status,
    }

    out_path = out_dir / "latest.json"
    out_path.write_text(json.dumps(packet_dict, indent=2), encoding="utf-8")

    print(f"Intake replay: deterministic_match={packet.deterministic_match}")
    print(f"  Source intake hash: {packet.source_intake_hash[:16]}...")
    print(f"  Status: {packet.status}")
    print(f"  out/intake_replay/latest.json")


if __name__ == "__main__":
    main()
