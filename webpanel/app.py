from __future__ import annotations

from typing import Optional

from fastapi import FastAPI

from .familiar_adapter import FamiliarAdapter
from .ledger import LedgerChain
from .panel_context import adapter as _adapter
from .panel_context import ledger as _ledger
from .panel_context import store as _store
from .routes import (
    register_compare,
    register_export,
    register_governance,
    register_index,
    register_runs,
)
from .routes.governance_routes import (
    ack,
    defer_start,
    defer_step,
    defer_stop,
    get_ledger,
    get_run,
    ingest,
    list_runs,
    ui_policy,
)
from .routes.index_routes import ui_ledger_json, ui_packet_json, ui_sample_packet
from .routes.runs_routes import ui_oracle_json, ui_run, ui_stability, ui_stability_json
from .routes.shared import (
    _emit_and_ingest_payload,
    _end_session,
    _ingest_packet,
    _record_ack,
    _record_policy_ack,
    _select_action,
    _start_deferral,
    _start_session,
    _step_deferral,
    _stop_deferral,
)
from .store import InMemoryStore


def create_app() -> FastAPI:
    app = FastAPI(title="ABX-Familiar Web Panel (MVP)", version="0.1.0")
    register_index(app)
    register_runs(app)
    register_compare(app)
    register_export(app)
    register_governance(app)
    return app


app = create_app()

store = _store
ledger = _ledger
adapter = _adapter


def reset_state(
    *,
    store: Optional[InMemoryStore] = None,
    ledger: Optional[LedgerChain] = None,
    adapter: Optional[FamiliarAdapter] = None,
) -> None:
    if store is not None:
        globals()["store"] = store
        from . import panel_context

        panel_context.store = store
    if ledger is not None:
        globals()["ledger"] = ledger
        from . import panel_context

        panel_context.ledger = ledger
    if adapter is not None:
        globals()["adapter"] = adapter
        from . import panel_context

        panel_context.adapter = adapter
