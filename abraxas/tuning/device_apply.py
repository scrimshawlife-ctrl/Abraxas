"""Apply device profile selection to ACTIVE portfolio pointer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from abraxas.core.canonical import canonical_json
from abraxas.runtime.device_fingerprint import get_device_fingerprint
from abraxas.tuning.device_registry import load_device_profiles
from abraxas.tuning.device_resolver import match_profiles, resolve_device_profile
from abraxas.policy.utp import find_portfolio_by_hash, load_active_utp


ACTIVE_POINTER_PATH = Path("data/utp/ACTIVE")
LEDGER_PATH = Path("out/tuning_ledgers/device_profile_switch.jsonl")
PORTFOLIO_DIR = Path("data/utp")


def select_and_apply_portfolio(
    run_ctx: Dict[str, object],
    *,
    dry_run: bool = False,
    pointer_path: Path | None = None,
    portfolio_dir: Path | None = None,
    ledger_path: Path | None = None,
) -> Dict[str, object]:
    fingerprint = get_device_fingerprint(run_ctx)
    profiles = load_device_profiles()
    matched_profiles = match_profiles(fingerprint, profiles)
    selected = matched_profiles[0] if matched_profiles else None
    current = load_active_utp()
    portfolio_dir = portfolio_dir or PORTFOLIO_DIR

    selected_hash = selected.portfolio_ref.portfolio_ir_hash if selected else current.hash()
    current_hash = current.hash()
    changed = selected_hash != current_hash

    result = {
        "fingerprint": fingerprint,
        "selected_profile": selected.model_dump() if selected else None,
        "matched_profiles": [profile.profile_id for profile in matched_profiles],
        "match_count": len(matched_profiles),
        "selected_portfolio_hash": selected_hash,
        "current_portfolio_hash": current_hash,
        "changed": changed,
    }

    if dry_run:
        return result

    if selected and changed:
        pointer_path = pointer_path or ACTIVE_POINTER_PATH
        ledger_path = ledger_path or LEDGER_PATH
        portfolio_path = find_portfolio_by_hash(portfolio_dir, selected_hash)
        if not portfolio_path:
            raise ValueError(f"Portfolio hash not found in {portfolio_dir}: {selected_hash}")
        _switch_active_portfolio(portfolio_path.name, pointer_path)
        _record_switch(result, ledger_path)

    return result


def _switch_active_portfolio(portfolio_name: str, pointer_path: Path) -> None:
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = pointer_path.with_suffix(".tmp")
    tmp_path.write_text(portfolio_name + "\n", encoding="utf-8")
    tmp_path.replace(pointer_path)


def _record_switch(payload: Dict[str, object], ledger_path: Path) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as f:
        f.write(canonical_json(payload) + "\n")
