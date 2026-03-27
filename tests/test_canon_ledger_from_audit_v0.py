from __future__ import annotations

from pathlib import Path

from tools.canon_ledger_from_audit import build_ledger_from_audit


def test_canon_ledger_from_audit_markdown(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    audit_path.write_text(
        "\n".join(
            [
                '{"base_ref":"base1","head_ref":"head1","commit_sha":"c1","timestamp_utc":"2026-02-01T00:00:00Z","files":[{"path":"schemas/a.json","blob_hash":"h1","classification":"schema"}]}',
                '{"commit_sha":"c2","timestamp_utc":"2026-02-02T00:00:00Z","files":[{"path":"webpanel/gates.py","blob_hash":"h2","classification":"code"},{"path":"tests/test_sample.py","blob_hash":"h3","classification":"test"}]}',
                '{"commit":{"sha":"c3","time":{"iso_utc":"2026-02-03T00:00:00Z"}},"range":{"base":"base1","head":"head1"},"files":[{"path":"schema/b.json","status":"M","class":"schema","blob":"h4"}]}',
            ]
        ),
        encoding="utf-8",
    )

    output = build_ledger_from_audit(audit_jsonl=audit_path, include_governance=True)

    assert "# Canon Ledger Append (Diff Audit)" in output
    assert "Date Range (UTC): 2026-02-01T00:00:00Z -> 2026-02-02T00:00:00Z" in output
    assert "Base: base1" in output
    assert "Head: head1" in output
    first_idx = output.find("path: schemas/a.json")
    second_idx = output.find("path: webpanel/gates.py")
    third_idx = output.find("path: schema/b.json")
    assert 0 <= first_idx < second_idx < third_idx
    assert "status: PENDING_REVIEW" in output
    assert "status: NON_CANON_EVIDENCE" not in output
