from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from ..core.oracle_runner import run_oracle
from ..core.validate import SchemaRegistry, validate_payload
from ..io.config import (
    VALID_TIERS,
    load_overlays_config,
    load_user_config,
    save_overlays_config,
    save_user_config,
)
from ..io.storage import DEFAULT_ROOT, StoragePaths, today_iso, write_json, write_text
from ..render.oracle_markdown import render_oracle_markdown


app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


def _paths(root: Optional[str]) -> StoragePaths:
    return StoragePaths(root=Path(root).expanduser() if root else DEFAULT_ROOT)


@app.command("init")
def init_cmd(root: Optional[str] = typer.Option(None, help="Storage root (default ~/.abraxas)")):
    """Initialize local-only storage + default configs."""
    paths = _paths(root)
    _ = load_user_config(paths)
    _ = load_overlays_config(paths)
    console.print(Panel.fit(f"Initialized at: {paths.root}", title="ABRAXAS", subtitle="local-only"))


@app.command("config")
def config_cmd(
    tier: Optional[str] = typer.Option(None, help="psychonaut|academic|enterprise"),
    admin: Optional[bool] = typer.Option(None, help="Enable admin menu locally"),
    location: Optional[str] = typer.Option(None, help="Location label (display only)"),
    root: Optional[str] = typer.Option(None, help="Storage root"),
):
    """View or update local user config."""
    paths = _paths(root)
    uc = load_user_config(paths)

    if tier is not None:
        if tier not in VALID_TIERS:
            raise typer.BadParameter(f"Invalid tier: {tier}")
        uc.tier = tier
    if admin is not None:
        uc.admin = admin
    if location is not None:
        uc.location_label = location

    save_user_config(paths, uc)
    console.print(Panel.fit(json.dumps(uc.to_dict(), indent=2), title="user.v0"))


@app.command("overlays")
def overlays_cmd(
    enable: Optional[str] = typer.Option(None, help="Comma list to enable, e.g. aalmanac,neon_genie"),
    disable: Optional[str] = typer.Option(None, help="Comma list to disable"),
    root: Optional[str] = typer.Option(None, help="Storage root"),
):
    """Enable/disable overlays (controls what runs inside oracle)."""
    paths = _paths(root)
    oc = load_overlays_config(paths)

    if enable:
        for k in [x.strip() for x in enable.split(",") if x.strip()]:
            oc.enabled[k] = True
    if disable:
        for k in [x.strip() for x in disable.split(",") if x.strip()]:
            oc.enabled[k] = False

    save_overlays_config(paths, oc)
    console.print(Panel.fit(json.dumps(oc.to_dict(), indent=2), title="overlays.v0"))


@app.command("oracle-run")
def oracle_run_cmd(
    day: Optional[str] = typer.Option(None, help="YYYY-MM-DD (default today)"),
    root: Optional[str] = typer.Option(None, help="Storage root"),
):
    """
    Run oracle (offline-first):
    - produces oracle.readout.json (source of truth)
    - produces oracle.md (rendered view)
    """
    paths = _paths(root)
    uc = load_user_config(paths)
    oc = load_overlays_config(paths)
    day = day or today_iso()

    out = run_oracle(uc, oc, day)
    readout = out.readout
    provenance = out.provenance

    schemas = SchemaRegistry(Path(__file__).resolve().parents[1] / "schemas")
    vr = validate_payload(schemas, "oracle_readout.v0.json", readout)
    if not vr.ok:
        console.print(Panel.fit(str(vr.errors), title="schema invalid", subtitle="oracle_readout.v0.json"))
        raise typer.Exit(code=2)

    md = render_oracle_markdown(readout, uc.tier)

    write_json(paths.oracle_readout_path(day), readout)
    write_text(paths.oracle_md_path(day), md)
    write_json(paths.provenance_path(day), provenance)

    console.print(Panel.fit(f"Wrote run: {paths.run_dir(day)}", title="oracle-run"))
    console.print(Syntax(md, "markdown", word_wrap=True))


@app.command("oracle-show")
def oracle_show_cmd(
    day: Optional[str] = typer.Option(None, help="YYYY-MM-DD (default today)"),
    root: Optional[str] = typer.Option(None, help="Storage root"),
):
    """Show the rendered oracle.md for a given day."""
    paths = _paths(root)
    day = day or today_iso()
    p = paths.oracle_md_path(day)
    if not p.exists():
        console.print(f"No oracle.md found for {day}. Run: abx oracle-run")
        raise typer.Exit(code=1)
    console.print(Syntax(p.read_text(encoding="utf-8"), "markdown", word_wrap=True))


@app.command("admin")
def admin_menu_cmd(root: Optional[str] = typer.Option(None, help="Storage root")):
    """Admin-only menu (hidden unless admin=true)."""
    paths = _paths(root)
    uc = load_user_config(paths)
    if not uc.admin:
        console.print("Admin disabled in local config.")
        raise typer.Exit(code=1)

    console.print(Panel.fit("Admin Menu:\n- substack-export\n- catalog-review\n- training-ingest", title="ADMIN"))
    console.print("Stub: commands will be added in the next drop (KITE + Training Mode wiring).")


@app.command("kite-ingest")
def kite_ingest_cmd(
    kind: str = typer.Option(..., help="note|link|transcript|dataset|snippet"),
    domain: str = typer.Option(..., help="e.g. game_theory, meteorology, finance"),
    tags: str = typer.Option("", help="comma tags"),
    text: str = typer.Option(..., help="content"),
    source: Optional[str] = typer.Option(None, help="optional URL or citation pointer"),
    day: Optional[str] = typer.Option(None, help="YYYY-MM-DD (default today)"),
    root: Optional[str] = typer.Option(None, help="Storage root"),
):
    """ADMIN: ingest training material locally (KITE)."""
    paths = _paths(root)
    uc = load_user_config(paths)
    if not uc.admin:
        console.print("Admin disabled in local config.")
        raise typer.Exit(code=1)

    from ..kite.ingest import ensure_candidates, ingest_note

    day = day or today_iso()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    ingest_note(paths, day, kind, domain, tag_list, text, source)
    ensure_candidates(paths, day)
    console.print(Panel.fit(f"KITE ingest saved: {paths.kite_ingest_jsonl(day)}", title="KITE v0.2.0"))


@app.command("kite-paths")
def kite_paths_cmd(
    day: Optional[str] = typer.Option(None, help="YYYY-MM-DD (default today)"),
    root: Optional[str] = typer.Option(None, help="Storage root"),
):
    """Show KITE file locations for the day."""
    paths = _paths(root)
    day = day or today_iso()
    console.print(
        Panel.fit(
            f"{paths.kite_day_dir(day)}\n- ingest.jsonl\n- candidates.json",
            title="KITE paths",
        )
    )
