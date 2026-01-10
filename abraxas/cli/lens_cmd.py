from __future__ import annotations

from pathlib import Path
import importlib

import typer

app = typer.Typer(help="LENS: Local Evaluation & Notation Studio (admin training mode).")


@app.command("serve")
def serve(
    db: Path = typer.Option(Path(".aal/aalmanac/ars.db"), "--db", help="ARS sqlite db"),
    candidates: Path = typer.Option(
        Path(".aal/aalmanac/candidates.jsonl"), "--candidates", help="candidate jsonl"
    ),
    out: Path = typer.Option(
        Path(".aal/aalmanac/proposals_approved.jsonl"),
        "--out",
        help="approved export jsonl",
    ),
    host: str = typer.Option(
        "127.0.0.1", "--host", help="bind host (default local-only)"
    ),
    port: int = typer.Option(8787, "--port", help="bind port"),
):
    deps = ["fastapi", "uvicorn", "jinja2", "multipart"]
    missing = [name for name in deps if importlib.util.find_spec(name) is None]
    if missing:
        missing_list = ", ".join(missing)
        raise typer.BadParameter(
            f"LENS deps missing: {missing_list}. Install with: pip install -e \".[lens]\""
        )

    lens_server = importlib.import_module("abraxas.lens.server")
    uvicorn = importlib.import_module("uvicorn")
    cfg = lens_server.LensConfig(
        db_path=db,
        candidates_jsonl=candidates,
        proposals_out=out,
        bind_host=host,
        bind_port=port,
    )

    app_ = lens_server.create_app(cfg)
    uvicorn.run(app_, host=cfg.bind_host, port=cfg.bind_port, log_level="info")
