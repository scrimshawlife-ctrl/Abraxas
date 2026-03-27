from __future__ import annotations

import importlib
from typing import Any, Callable, Dict, Optional, Tuple


KERNEL_REGISTRY: Dict[str, str] = {
    "v2": "abraxas.kernel.v2.engine:run_oracle_v2",
}
_DEFAULT_KERNEL_VERSION = "v2"


def _load_runner(path: str) -> Tuple[Optional[Callable[[Any], Dict[str, Any]]], Optional[str]]:
    try:
        module_path, func_name = path.split(":", 1)
    except ValueError:
        return None, f"Invalid kernel entrypoint: {path}"
    try:
        mod = importlib.import_module(module_path)
        fn = getattr(mod, func_name, None)
        if not callable(fn):
            return None, f"Kernel entrypoint not callable: {path}"
        return fn, None
    except ModuleNotFoundError as err:
        return None, f"Kernel module not installed: {err}"
    except Exception as err:
        return None, f"Kernel import error: {err}"


def _error_engine_adapter(
    inputs: Any,
    *,
    requested_version: str,
    entrypoint: str,
    load_error: str,
) -> Dict[str, Any]:
    day = getattr(inputs, "day", "unknown")
    user = getattr(inputs, "user", {}) or {}
    location = user.get("location_label", "Unknown")

    return {
        "header": {
            "date": day,
            "location": location,
            "headline": "Kernel entrypoint unavailable.",
        },
        "vector_mix": {
            "ritual_density": 0.0,
            "meme_velocity": 0.0,
            "nostalgia": 0.0,
            "symbolic_modulator": "Kernel load gate",
            "signal_noise": 1.0,
            "drift_charge": 1.0,
            "coherence": 0.0,
            "notes": "Runtime fell back to deterministic error envelope.",
        },
        "runic_weather": {
            "active": ["GATE"],
            "interpretations": [
                {"rune": "GATE", "short": "Kernel runner not loadable; execution blocked."},
            ],
        },
        "gate_and_trial": [
            f"Requested kernel version: {requested_version}",
            f"Entrypoint: {entrypoint}",
            f"Load error: {load_error}",
        ],
        "not_computable": {
            "reason": "kernel_runner_unavailable",
            "details": load_error,
            "entrypoint": entrypoint,
            "version": requested_version,
        },
        "financials": {
            "macro": ["Kernel unavailable; no forecast path executed."],
            "tickers": [],
            "crypto": [],
            "risk_note": "Deterministic blocked state.",
        },
        "overlays": {
            "enabled": getattr(inputs, "overlays_enabled", {}),
            "tier_ctx": getattr(inputs, "tier_ctx", {}),
        },
    }


def get_kernel_runner(version: str = _DEFAULT_KERNEL_VERSION) -> Callable[[Any], Dict[str, Any]]:
    requested_version = version
    path = KERNEL_REGISTRY.get(version)
    if not path:
        requested_version = _DEFAULT_KERNEL_VERSION
        path = KERNEL_REGISTRY.get(_DEFAULT_KERNEL_VERSION, "")

    runner, err = _load_runner(path)
    if runner is not None:
        return runner

    return lambda inputs: _error_engine_adapter(
        inputs,
        requested_version=requested_version,
        entrypoint=path,
        load_error=err or "unknown_error",
    )
