from __future__ import annotations

import json
from pathlib import Path

import pytest

from webpanel.oracle_signal_artifact import load_oracle_signal_artifact, resolve_oracle_signal_artifact_path


def test_resolve_oracle_signal_artifact_path_accepts_in_scope() -> None:
    root = Path("out/oracle_signal_layer_v2")
    root.mkdir(parents=True, exist_ok=True)
    artifact = root / "artifact_test.json"
    artifact.write_text(json.dumps({"ok": True}), encoding="utf-8")
    resolved = resolve_oracle_signal_artifact_path(str(artifact))
    assert resolved == artifact.resolve()


def test_resolve_oracle_signal_artifact_path_rejects_out_of_scope(tmp_path: Path) -> None:
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        resolve_oracle_signal_artifact_path(str(outside))


def test_load_oracle_signal_artifact_splits_authority_and_advisory() -> None:
    root = Path("out/oracle_signal_layer_v2")
    root.mkdir(parents=True, exist_ok=True)
    artifact = root / "artifact_payload.json"
    payload = {"authority": {"authority_scope": "interpretation_only"}, "advisory_attachments": [{"attachment_id": "mircl"}]}
    artifact.write_text(json.dumps(payload), encoding="utf-8")
    loaded = load_oracle_signal_artifact(str(artifact))
    assert loaded["authority"]["authority_scope"] == "interpretation_only"
    assert loaded["advisory_attachments"][0]["attachment_id"] == "mircl"
