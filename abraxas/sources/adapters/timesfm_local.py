"""TimesFM 2.5 local Shadow adapter. Inference is optional and non-authoritative."""

from __future__ import annotations

from typing import Any, Dict

from abraxas.sources.adapters.http_snapshot import HTTPSnapshotAdapter
from abraxas.sources.timesfm_shadow.constants import ADAPTER_ID, HF_REVISION
from abraxas.sources.timesfm_shadow.energy_charts import parse_energy_charts_price
from abraxas.sources.timesfm_shadow.infer import InferFn, resolve_infer_fn
from abraxas.sources.timesfm_shadow.packets import HistoryBlock, TimesFMShadowForecastV0, build_shadow_packet


class TimesFMLocalAdapter(HTTPSnapshotAdapter):
    """HTTP snapshot reuse plus Shadow-only TimesFM 2.5 predict()."""

    adapter_name = ADAPTER_ID
    version = "0.1"

    def parse(self, raw: bytes, run_ctx: Dict[str, Any]) -> Dict[str, Any]:
        parsed = super().parse(raw, run_ctx)
        if not _looks_like_energy_charts(parsed):
            return parsed
        window_n = _window_n(run_ctx)
        history = parse_energy_charts_price(parsed, window_n=window_n)
        return {"raw": parsed, "history": history.model_dump()}

    def predict(
        self,
        history: HistoryBlock,
        horizon: int,
        seed: int,
        hf_revision: str = HF_REVISION,
        infer_fn: InferFn | None = None,
    ) -> TimesFMShadowForecastV0:
        infer = resolve_infer_fn(infer_fn)
        mean, quantiles = infer(history.values, horizon, seed, hf_revision)
        return build_shadow_packet(
            history=history,
            mean=mean,
            quantiles=quantiles,
            horizon=horizon,
            seed=seed,
            hf_revision=hf_revision,
        )


def _looks_like_energy_charts(parsed: Dict[str, Any]) -> bool:
    return isinstance(parsed.get("unix_seconds"), list) and isinstance(parsed.get("price"), list)


def _window_n(run_ctx: Dict[str, Any]) -> int:
    raw = run_ctx.get("window_n")
    try:
        return int(raw)
    except (TypeError, ValueError):
        from abraxas.sources.timesfm_shadow.constants import DEFAULT_WINDOW_N

        return DEFAULT_WINDOW_N
