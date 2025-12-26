from __future__ import annotations

import json
from pathlib import Path

from abraxas.evolve.rim_builder import build_rim_from_osh_ledger


def test_build_rim_from_osh_ledger(tmp_path: Path):
    ledger = tmp_path / "fetch_artifacts.jsonl"
    ledger.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "status": "ok",
                        "artifact": {
                            "artifact_id": "a1",
                            "url": "https://example.com/a",
                            "body_sha256": "abc",
                            "content_type": "text/html",
                            "status_code": 200,
                            "fetched_ts": "2025-01-01T00:00:00+00:00",
                        },
                    }
                ),
                json.dumps({"status": "offline_required", "job_id": "j2"}),
            ]
        ),
        encoding="utf-8",
    )

    out_root = tmp_path / "replay_inputs"
    rim_path, meta = build_rim_from_osh_ledger(
        run_id="r1",
        out_root=str(out_root),
        osh_ledger_path=str(ledger),
        max_items=10,
    )
    data = json.loads(Path(rim_path).read_text(encoding="utf-8"))
    assert data["version"] == "rim.v0.1"
    assert data["totals"]["items"] == 1
    assert meta["items"] == 1
