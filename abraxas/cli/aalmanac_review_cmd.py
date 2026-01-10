from __future__ import annotations

from pathlib import Path
import json
import sqlite3
from typing import Any, Dict, Optional

import typer

from abraxas.aalmanac.ars_store import (
    export_approved_proposals,
    latest_decision,
    list_candidates,
    open_store,
    set_decision,
    upsert_candidates_from_jsonl,
)

app = typer.Typer(help="AALmanac Review System (ARS) admin CLI.")


def _emit(obj: Dict[str, Any]) -> None:
    typer.echo(json.dumps(obj, sort_keys=True, indent=2))


def _serialize_decision(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    return {
        "decision": row["decision"],
        "note": row["note"],
        "merge_into_id": row["merge_into_id"],
        "reviewer": row["reviewer"],
        "created_at_utc": row["created_at_utc"],
    }


@app.command("load")
def load_candidates(
    candidates: Path = typer.Option(
        Path(".aal/aalmanac/candidates.jsonl"),
        "--candidates",
        help="Candidate jsonl (append-only).",
    ),
    db: Path = typer.Option(
        Path(".aal/aalmanac/ars.db"),
        "--db",
        help="ARS sqlite database path.",
    ),
) -> None:
    """Load candidate jsonl into the ARS store."""
    conn = open_store(db)
    try:
        report = upsert_candidates_from_jsonl(conn, candidates)
    finally:
        conn.close()
    _emit(report)


@app.command("list")
def list_review_candidates(
    db: Path = typer.Option(
        Path(".aal/aalmanac/ars.db"),
        "--db",
        help="ARS sqlite database path.",
    ),
    limit: int = typer.Option(50, "--limit", help="Maximum candidates to return."),
    min_score: float = typer.Option(0.0, "--min-score", help="Minimum score filter."),
    include_payload: bool = typer.Option(
        False, "--include-payload", help="Include payload JSON in output."
    ),
) -> None:
    """List candidate terms and latest review decision."""
    conn = open_store(db)
    try:
        results = []
        for row in list_candidates(conn, limit=limit, min_score=min_score):
            dec = latest_decision(conn, row["id"])
            payload = json.loads(row["payload_json"]) if include_payload else None
            entry = {
                "id": row["id"],
                "kind": row["kind"],
                "term": row["term"],
                "score": row["score"],
                "created_at_utc": row["created_at_utc"],
                "latest_decision": _serialize_decision(dec),
            }
            if include_payload:
                entry["payload"] = payload
            results.append(entry)
    finally:
        conn.close()

    _emit({"count": len(results), "candidates": results})


@app.command("decide")
def decide_candidate(
    candidate_id: str = typer.Argument(..., help="Candidate id to review."),
    decision: str = typer.Option(
        ..., "--decision", help="Decision: approve | deny | merge"
    ),
    note: str = typer.Option("", "--note", help="Optional review note."),
    merge_into_id: Optional[str] = typer.Option(
        None, "--merge-into-id", help="Target id for merge decision."
    ),
    reviewer: str = typer.Option("admin", "--reviewer", help="Reviewer label."),
    db: Path = typer.Option(
        Path(".aal/aalmanac/ars.db"),
        "--db",
        help="ARS sqlite database path.",
    ),
) -> None:
    """Record a review decision."""
    conn = open_store(db)
    try:
        result = set_decision(
            conn,
            candidate_id=candidate_id,
            decision=decision,
            note=note,
            merge_into_id=merge_into_id,
            reviewer=reviewer,
        )
    finally:
        conn.close()
    _emit(result)


@app.command("export-approved")
def export_approved(
    out: Path = typer.Option(
        Path(".aal/aalmanac/approved.jsonl"),
        "--out",
        help="Output jsonl for approved candidates.",
    ),
    db: Path = typer.Option(
        Path(".aal/aalmanac/ars.db"),
        "--db",
        help="ARS sqlite database path.",
    ),
) -> None:
    """Export approved candidates to jsonl."""
    conn = open_store(db)
    try:
        report = export_approved_proposals(conn, out)
    finally:
        conn.close()
    _emit(report)
