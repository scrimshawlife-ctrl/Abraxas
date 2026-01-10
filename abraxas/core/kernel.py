from __future__ import annotations
from typing import Dict, Any, Optional, List
from .context import UserContext, AdminContext
from .state import OracleState
from .tiers import tier_rules, enforce_overlay_allowed
from .logging import log_event, stable_hash
from ..overlays.registry import OverlayRegistry


class AbraxasKernel:
    """
    Abraxas Kernel = governed oracle execution engine.
    Overlays are optional augmentations, never authoritative.
    Admin-only projection is a separate step.
    """

    def __init__(self, overlay_registry: Optional[OverlayRegistry] = None):
        self.overlays = overlay_registry or OverlayRegistry.default()

    def run_oracle(
        self,
        user: UserContext,
        input_signals: Dict[str, Any],
        overlays_requested: Optional[List[str]] = None,
        admin_ctx: Optional[AdminContext] = None,
        admin_projection: bool = False,
    ) -> Dict[str, Any]:
        # 0) init
        state = OracleState()
        log_event(state, "oracle.init", {"tier": user.tier, "overlays_requested": overlays_requested or []})

        # 1) signal intake (deterministic transform only)
        state.signal_layer = self._signal_intake(input_signals)
        log_event(state, "oracle.signal", {"hash": stable_hash(state.signal_layer)})

        # 2) symbolic compression (deterministic mapping)
        state.symbolic_layer = self._symbolic_compress(state.signal_layer)
        log_event(state, "oracle.symbolic", {"hash": stable_hash(state.symbolic_layer)})

        # 3) metric evaluation (deterministic, tier-aware later)
        state.metric_layer = self._metric_eval(state.symbolic_layer)
        log_event(state, "oracle.metrics", {"hash": stable_hash(state.metric_layer)})

        # 4) runic layer (deterministic selection)
        state.runic_layer = self._runic_weather(state.symbolic_layer, state.metric_layer)
        log_event(state, "oracle.runic", {"hash": stable_hash(state.runic_layer)})

        # 5) overlays (tier-gated)
        overlays_requested = overlays_requested or []
        for name in overlays_requested:
            enforce_overlay_allowed(user.tier, name)
            overlay = self.overlays.get(name)
            out = overlay.run(oracle_state=state, user=user)
            state.overlay_outputs[name] = out
            log_event(state, "oracle.overlay", {"name": name, "hash": stable_hash(out)})

        # 6) assemble + tier filter
        emitted = self._assemble_emitted(user, state)

        # 6a) schema-level tier redaction inside overlays (if they emit tier_visibility fields)
        from pathlib import Path
        from .validate import SchemaRegistry, validate_payload, redact_by_tier

        schemas = SchemaRegistry(Path(__file__).resolve().parents[1] / "schemas")

        # Redact overlay outputs deterministically BEFORE validating envelope
        if "overlay_outputs" in emitted and isinstance(emitted["overlay_outputs"], dict):
            emitted["overlay_outputs"] = redact_by_tier(user.tier, emitted["overlay_outputs"])

        # Validate overlay payloads individually (hard gate)
        # Uses overlay.meta.output_schema filenames
        for name, out in (state.overlay_outputs or {}).items():
            overlay = self.overlays.get(name)
            schema_path = overlay.meta.output_schema.split("/")[-1]
            vr = validate_payload(schemas, schema_path, out)
            if not vr.ok:
                raise ValueError(f"Overlay schema validation failed: {name} :: {vr.errors}")

        log_event(state, "oracle.emit", {"hash": stable_hash(emitted)})

        # Build envelope
        result = {
            "run_id": stable_hash({"tier": user.tier, "signal": state.signal_layer, "t": "v0"}),
            "tier": user.tier,
            "oracle": emitted,
            "overlays": list(state.overlay_outputs.keys()),
            "provenance": {
                "signal_hash": stable_hash(state.signal_layer),
                "symbolic_hash": stable_hash(state.symbolic_layer),
                "metric_hash": stable_hash(state.metric_layer),
                "runic_hash": stable_hash(state.runic_layer),
                "overlay_hashes": {k: stable_hash(v) for k, v in state.overlay_outputs.items()},
            },
            "logs": state.logs,
        }

        # Validate envelope (hard gate)
        vr_env = validate_payload(schemas, "oracle_run.v0.json", result)
        if not vr_env.ok:
            raise ValueError(f"Oracle envelope schema validation failed :: {vr_env.errors}")

        # 7) admin projection (never on by default)
        if admin_projection:
            if not (admin_ctx and admin_ctx.is_admin):
                raise PermissionError("Admin projection requested without admin context.")
            from ..admin.projection import apply_admin_projection
            state.projection_buffer = apply_admin_projection(state)
            log_event(state, "oracle.projection", {"hash": stable_hash(state.projection_buffer)})

        # 8) return emitted (projection buffer not included unless admin consumes it explicitly)
        return result

    # --- Internal deterministic stages (stubs you can deepen later) ---

    def _signal_intake(self, input_signals: Dict[str, Any]) -> Dict[str, Any]:
        # Deterministic normalization: sort keys, coerce known fields.
        return {k: input_signals[k] for k in sorted(input_signals.keys())}

    def _symbolic_compress(self, signal_layer: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder transform; keep deterministic.
        return {"motifs": signal_layer.get("motifs", []), "pressure": signal_layer.get("pressure", 0)}

    def _metric_eval(self, symbolic_layer: Dict[str, Any]) -> Dict[str, Any]:
        # Deterministic derived metrics (no randomness).
        pressure = float(symbolic_layer.get("pressure", 0) or 0)
        return {"pressure_index": pressure, "coherence": max(0.0, 1.0 - (pressure / 10.0))}

    def _runic_weather(self, symbolic_layer: Dict[str, Any], metric_layer: Dict[str, Any]) -> Dict[str, Any]:
        # Deterministic rune picks: choose by threshold rules.
        pressure = metric_layer.get("pressure_index", 0)
        if pressure >= 7:
            runes = ["Kairos Window", "Nonlinear Kick"]
        elif pressure >= 4:
            runes = ["Oscillation Loop", "Trajectory Selection"]
        else:
            runes = ["Slow Manifold", "Hidden Order"]
        return {"active_runes": runes[:3], "count": len(runes[:3])}

    def _assemble_emitted(self, user: UserContext, state: OracleState) -> Dict[str, Any]:
        rules = tier_rules(user.tier)
        # Tier-filter: emit only what tier supports (expand later with strict schema).
        base = {
            "vector_mix": {
                "pressure_index": state.metric_layer.get("pressure_index"),
                "coherence": state.metric_layer.get("coherence"),
                "quantification": rules["quantification"],
            },
            "runic_weather": state.runic_layer,
            "notes": {
                "sources": rules["sources"],
                "simulation": rules["simulation"],
            },
        }
        # overlays included only if requested + allowed
        if state.overlay_outputs:
            base["overlay_outputs"] = state.overlay_outputs
        return base
