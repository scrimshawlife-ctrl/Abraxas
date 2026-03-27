"""Abraxas message bus runtime with deterministic module execution."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Callable, Dict, List


@dataclass(frozen=True)
class Registry:
    """Built-in module registry for bus processing."""

    modules: List[str]

    def list(self) -> List[str]:
        """Return deterministic module listing."""
        return sorted(self.modules)


def build_registry() -> Registry:
    """Build deterministic module registry."""
    return Registry(
        modules=[
            "oracle",
            "rack",
            "semiotic",
            "slang_hist_seed_loader",
            "slang_seed_metrics_scorer",
            "weather",
        ]
    )


def _stable_payload(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _frame_id(payload: Dict[str, Any]) -> str:
    digest = hashlib.sha256(_stable_payload(payload).encode("utf-8")).hexdigest()
    return f"frame_{digest[:16]}"


def _oracle_module(payload: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    user_text = str(payload.get("user_text", "")).strip()
    intent = str(payload.get("intent", "unknown"))
    signal_hash = hashlib.sha256(f"{intent}|{user_text}".encode("utf-8")).hexdigest()[:12]
    signal = "low" if not user_text else "medium" if len(user_text) < 80 else "high"
    return {
        "intent": intent,
        "signal": signal,
        "signal_hash": signal_hash,
    }


def _rack_module(payload: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    selected = payload.get("selected_modules") or []
    rack_mode = "directed" if selected else "default"
    return {
        "mode": rack_mode,
        "selected_count": len(selected),
    }


def _semiotic_module(payload: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    user_text = str(payload.get("user_text", "")).lower()
    tokens = [t for t in user_text.replace("\n", " ").split(" ") if t]
    motifs = tokens[:3]
    return {
        "motifs": motifs,
        "token_count": len(tokens),
    }


def _seed_loader_module(payload: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    base = _stable_payload(payload)
    seed = int(hashlib.sha256(base.encode("utf-8")).hexdigest()[:8], 16)
    return {"seed": seed}


def _seed_scorer_module(payload: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    seed = int(state.get("slang_hist_seed_loader", {}).get("seed", 0))
    score = round((seed % 1000) / 1000.0, 3)
    return {"score": score}


def _weather_module(payload: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    score = float(state.get("slang_seed_metrics_scorer", {}).get("score", 0.0))
    if score >= 0.66:
        weather = "charged"
    elif score >= 0.33:
        weather = "stable"
    else:
        weather = "quiet"
    return {"class": weather, "score": score}


_MODULE_HANDLERS: Dict[str, Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]] = {
    "oracle": _oracle_module,
    "rack": _rack_module,
    "semiotic": _semiotic_module,
    "slang_hist_seed_loader": _seed_loader_module,
    "slang_seed_metrics_scorer": _seed_scorer_module,
    "weather": _weather_module,
}


def process(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Process payload through deterministic module execution pipeline."""
    registry = build_registry()
    available = set(registry.list())

    selected = payload.get("selected_modules")
    if isinstance(selected, list) and selected:
        modules = [m for m in selected if isinstance(m, str) and m in available]
    else:
        modules = registry.list()

    module_state: Dict[str, Any] = {}
    for module_name in modules:
        handler = _MODULE_HANDLERS[module_name]
        module_state[module_name] = handler(payload, module_state)

    oracle = module_state.get("oracle", {})
    weather = module_state.get("weather", {})
    message = (
        f"Processed intent={oracle.get('intent', payload.get('intent', 'unknown'))} "
        f"signal={oracle.get('signal', 'low')} weather={weather.get('class', 'quiet')}"
    )

    frame_id = _frame_id(payload)
    logical_ts = int(hashlib.sha256(frame_id.encode("utf-8")).hexdigest()[:8], 16)

    return {
        "meta": {
            "frame_id": frame_id,
            "ts": logical_ts,
            "intent": payload.get("intent", "unknown"),
            "modules_executed": modules,
        },
        "input": payload,
        "output": {
            "status": "ok",
            "message": message,
            "module_state": module_state,
        },
    }
