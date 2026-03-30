from __future__ import annotations

import json
from pathlib import Path

from abx.operator_views import build_release_view


def test_build_release_view_uses_release_artifact(tmp_path: Path) -> None:
    run_id = "RUN-REL-1"
    path = tmp_path / "out" / "release" / f"release-readiness-{run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "status": "READY",
                "blocking_failures": [],
                "known_non_blocking": ["sample-non-blocking"],
                "checks": [{"name": "governance_lint", "ok": True, "outcome": "PASS", "notes": "ok"}],
            }
        ),
        encoding="utf-8",
    )

    view = build_release_view(run_id, base_dir=tmp_path)
    assert view.status == "READY"
    assert view.non_blocking_issues == ["sample-non-blocking"]
    assert view.checklist[0]["name"] == "governance_lint"
