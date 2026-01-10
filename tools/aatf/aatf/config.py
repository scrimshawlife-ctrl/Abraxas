from __future__ import annotations

from pathlib import Path

AATF_ROOT = Path(__file__).resolve().parents[1]
LOCAL_STORE = AATF_ROOT / ".aatf" / "local_store"
LEDGER_ROOT = AATF_ROOT / ".aatf" / "ledger"
