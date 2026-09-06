"""Optional TimesFM 2.5 CPU inference. Weights are never required by CI."""

from __future__ import annotations

from typing import Callable, Sequence

from abx.optional_dependencies import require_optional_dependency
from abraxas.sources.timesfm_shadow.constants import (
    HF_REVISION,
    MAX_CONTEXT_LEN,
    MODEL_ID,
    Q10,
    Q50,
    Q90,
    STANDARD_QUANTILES,
)

InferFn = Callable[[Sequence[float], int, int, str], tuple[list[float], dict[str, list[float]]]]


def nearest_quantile_index(levels: Sequence[float], target: float) -> int:
    if not levels:
        raise ValueError("quantile levels are empty")
    scored = [(abs(float(level) - target), idx) for idx, level in enumerate(levels)]
    scored.sort()
    return scored[0][1]


def extract_quantiles(
    full_predictions: Sequence[Sequence[float]],
    *,
    horizon: int,
    levels: Sequence[float] = STANDARD_QUANTILES,
) -> dict[str, list[float]]:
    if horizon < 1:
        raise ValueError("horizon must be >= 1")
    rows = [list(row) for row in full_predictions[:horizon]]
    if len(rows) < horizon:
        raise ValueError("full_predictions shorter than horizon")
    q10_i = nearest_quantile_index(levels, Q10)
    q50_i = nearest_quantile_index(levels, Q50)
    q90_i = nearest_quantile_index(levels, Q90)
    return {
        "q10": [_cell(row, q10_i) for row in rows],
        "q50": [_cell(row, q50_i) for row in rows],
        "q90": [_cell(row, q90_i) for row in rows],
    }


def run_timesfm_2_5_cpu(
    values: Sequence[float],
    horizon: int,
    seed: int,
    hf_revision: str,
) -> tuple[list[float], dict[str, list[float]]]:
    if hf_revision != HF_REVISION:
        raise ValueError(f"hf_revision must equal pinned {HF_REVISION}")
    if horizon < 1:
        raise ValueError("horizon must be >= 1")
    if len(values) < 1:
        raise ValueError("history values are empty")
    torch, model = _load_timesfm_2_5(hf_revision, seed)
    context = list(values)[-MAX_CONTEXT_LEN:]
    tensor = torch.tensor(context, dtype=torch.float32)
    context_len = min(len(context), MAX_CONTEXT_LEN)
    with torch.no_grad():
        outputs = model(past_values=[tensor], forecast_context_len=context_len)
    mean = _as_1d(outputs.mean_predictions)[:horizon]
    if len(mean) < horizon:
        raise RuntimeError("TimesFM mean_predictions shorter than horizon")
    quantiles = extract_quantiles(
        _as_2d(outputs.full_predictions),
        horizon=horizon,
        levels=_quantile_levels(model),
    )
    return [float(item) for item in mean], quantiles


def _load_timesfm_2_5(hf_revision: str, seed: int) -> tuple[object, object]:
    torch = require_optional_dependency("torch", "timesfm_shadow_lab")
    transformers = require_optional_dependency("transformers", "timesfm_shadow_lab")
    model_cls = getattr(transformers, "TimesFm2_5ModelForPrediction", None)
    if model_cls is None:
        raise RuntimeError(
            "transformers is missing TimesFm2_5ModelForPrediction; "
            "install a build that ships TimesFM 2.5"
        )
    torch.set_num_threads(1)
    torch.manual_seed(int(seed))
    model = model_cls.from_pretrained(MODEL_ID, revision=hf_revision)
    return torch, model.to(torch.float32).eval()


def _quantile_levels(model: object) -> Sequence[float]:
    config = getattr(model, "config", None)
    raw = getattr(config, "quantiles", None) if config is not None else None
    if isinstance(raw, (list, tuple)) and raw:
        return [float(item) for item in raw]
    return STANDARD_QUANTILES


def _cell(row: Sequence[float], index: int) -> float:
    if index < 0 or index >= len(row):
        raise ValueError("quantile index out of range")
    return float(row[index])


def _as_1d(raw: object) -> list[float]:
    values = _tolist(raw)
    if values and isinstance(values[0], list):
        values = values[0]
    return [float(item) for item in values]


def _as_2d(raw: object) -> list[list[float]]:
    values = _tolist(raw)
    if values and isinstance(values[0], list) and values[0] and isinstance(values[0][0], list):
        values = values[0]
    rows: list[list[float]] = []
    for row in values:
        if not isinstance(row, list):
            raise ValueError("full_predictions must be rank-2")
        rows.append([float(item) for item in row])
    return rows


def _tolist(raw: object) -> list[object]:
    if hasattr(raw, "detach"):
        raw = raw.detach().cpu().tolist()
    elif hasattr(raw, "tolist"):
        raw = raw.tolist()
    if not isinstance(raw, list):
        raise ValueError("prediction tensor must convert to a list")
    return raw


def resolve_infer_fn(infer_fn: InferFn | None) -> InferFn:
    return infer_fn if infer_fn is not None else run_timesfm_2_5_cpu
