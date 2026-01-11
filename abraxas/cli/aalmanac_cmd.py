from __future__ import annotations

from pathlib import Path
import json
import typer

from abraxas.aalmanac.ingest_kite import ingest_kite_export

app = typer.Typer(help="AALmanac ops (shadow-only unless explicitly promoted).")


@app.command("ingest-kite")
def ingest_kite(
    in_dir: Path = typer.Option(
        ...,
        "--in",
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="KITE export directory",
    ),
    out: Path = typer.Option(
        Path(".aal/aalmanac/candidates.jsonl"),
        "--out",
        help="Append-only candidate log (jsonl). Local-only.",
    ),
):
    """
    Consume a KITE export bundle and emit AALmanac candidate terms (single + compound).
    LOCAL ONLY. SHADOW ONLY.
    """
    report = ingest_kite_export(in_dir, out)
    typer.echo(json.dumps(report, sort_keys=True, indent=2))


@app.command("review")
def review_stub(
    candidates: Path = typer.Option(
        Path(".aal/aalmanac/candidates.jsonl"),
        "--candidates",
        help="Candidate jsonl to inspect",
    ),
    head: int = typer.Option(30, "--head", help="Show first N candidates"),
):
    """
    Minimal review stub (prints a deterministic slice). Admin UI comes next.
    """
    if not candidates.exists():
        raise typer.BadParameter(f"Missing candidate file: {candidates}")

    shown = 0
    with candidates.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            typer.echo(
                f"{obj.get('kind','?'):8} | {obj.get('score','?')} | {obj.get('term','?')} | tags={obj.get('tags', [])}"
            )
            shown += 1
            if shown >= head:
                break
