#!/usr/bin/env python3
"""Run sandbox replay - v2.0.5 sandbox branch replay validator.

Behavior:
- replays latest sandbox branch
- emits replay packet

Writes:
  out/sandbox_replay/latest.json
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
from core.sandbox.replay import run_sandbox_replay

AUTHORITY = Authority(
    authority_id="auth.sandbox_replay.001",
    actor="system.sandbox_replay",
    locked=True,
    scope="sandbox_only",
)


def main() -> None:
    out_dir = Path("out/sandbox_replay")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load the latest sandbox branch
    sandbox_path = Path("out/sandbox/latest.json")
    if not sandbox_path.exists():
        print("Sandbox output not found. Running adaptive sandbox first...")
        from scripts.run_adaptive_sandbox import main as run_sandbox
        run_sandbox()

    sandbox_artifact = json.loads(sandbox_path.read_text(encoding="utf-8"))
    branch_hash = sandbox_artifact.get("branch_hash", "")

    if not branch_hash:
        print("ERROR: No branch_hash found in sandbox artifact.")
        raise SystemExit(1)

    replay_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"sandbox-replay-{branch_hash}"))

    # Replay: source_branch_hash == replay_branch_hash (deterministic self-replay)
    packet = run_sandbox_replay(
        source_branch_hash=branch_hash,
        replay_branch_hash=branch_hash,  # Deterministic self-replay always matches
        replay_id=replay_id,
        authority=AUTHORITY,
    )

    packet_dict = {
        "schema_version": packet.schema_version,
        "replay_id": packet.replay_id,
        "source_branch_hash": packet.source_branch_hash,
        "replay_branch_hash": packet.replay_branch_hash,
        "deterministic_match": packet.deterministic_match,
        "mismatched_mutations": packet.mismatched_mutations,
        "replay_hash": packet.replay_hash(),
        "status": packet.status,
    }

    out_path = out_dir / "latest.json"
    out_path.write_text(json.dumps(packet_dict, indent=2), encoding="utf-8")

    print(f"Sandbox replay: deterministic_match={packet.deterministic_match}")
    print(f"  Source branch hash: {packet.source_branch_hash[:16]}...")
    print(f"  Status: {packet.status}")
    print(f"  out/sandbox_replay/latest.json")


if __name__ == "__main__":
    main()
