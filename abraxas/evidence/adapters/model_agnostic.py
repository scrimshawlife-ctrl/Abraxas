"""Model-agnostic inference adapter.

Where an engine needs an inference callable, we do not require a bespoke custom
model. This adapter talks to any OpenAI-compatible chat-completions endpoint, so
the same callable works against a local model, a hosted provider, or a gateway.
Custom, engine-specific inference is a future capability (surfaced as
"custom inference coming soon" in the UI).

Contract
--------
The callable returned by :func:`create_model_agnostic_inference` has the shape the
evidence adapters expect::

    infer(claim: str, context: dict) -> {
        "candidates": [...],
        "model_identity": str,
        "relations": [...],
        "reasoning_steps": [...],
        "provenance": {...},
    }

Determinism
-----------
With no endpoint configured (the default in CI and for offline runs) the adapter
returns a **deterministic** offline result derived from the claim. It is honest
about what it is: ``provenance["inference"] == "offline-deterministic"`` and
``model_identity`` names it as such. It never pretends to be a model output.

This is deliberately not called a mock. A mock implies "substitute for something
that exists"; this is the real, shipped path for teams without a model wired yet,
and the provenance says which path ran.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, List, Optional

DEFAULT_BASE_URL_ENV = "ABX_INFERENCE_BASE_URL"
DEFAULT_MODEL_ENV = "ABX_INFERENCE_MODEL"
DEFAULT_API_KEY_ENV = "ABX_INFERENCE_API_KEY"
DEFAULT_TIMEOUT_ENV = "ABX_INFERENCE_TIMEOUT_SECONDS"

OFFLINE_IDENTITY = "model-agnostic/offline-deterministic"
MAX_RESPONSE_BYTES = 1_000_000

_SYSTEM_PROMPT = (
    "You are an evidence engine. Given a claim, return a JSON object with keys: "
    "candidates (list of strings, each a candidate reading of the claim), "
    "relations (list of short relation labels between claim and candidate), "
    "reasoning_steps (list of short strings). Respond with JSON only."
)


class InferenceUnavailable(RuntimeError):
    """Raised when a configured endpoint cannot be reached."""


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def _stable_digest(claim: str, salt: str = "") -> str:
    return hashlib.sha256(f"{salt}|{claim}".encode("utf-8")).hexdigest()


def _offline_result(claim: str, context: Dict[str, Any], model_identity: str) -> Dict[str, Any]:
    """Deterministic, non-networked result. Stable for identical input."""
    digest = _stable_digest(claim, "offline")
    # Deterministic pseudo-selection: the digest decides which readings apply.
    readings = [
        "literal",
        "conditional",
        "causal",
        "correlational",
    ]
    picked = [readings[int(digest[i * 2: i * 2 + 2], 16) % len(readings)] for i in range(2)]
    candidates: List[str] = [f"{reading} reading of: {claim[:120]}" for reading in picked]
    relations = [f"claim->{reading}" for reading in picked]
    steps = [
        "Tokenised claim deterministically.",
        "Derived candidate readings from a stable digest of the input.",
        "No model endpoint configured; reporting offline provenance.",
    ]
    return {
        "candidates": candidates,
        "model_identity": model_identity,
        "relations": relations,
        "reasoning_steps": steps,
        "provenance": {
            "inference": "offline-deterministic",
            "input_sha256": _stable_digest(claim),
            "configured": False,
            "context_keys": sorted(context.keys()) if isinstance(context, dict) else [],
        },
    }


def _http_result(
    claim: str,
    context: Dict[str, Any],
    *,
    base_url: str,
    model: str,
    api_key: str,
    timeout: float,
) -> Dict[str, Any]:
    """Call an OpenAI-compatible /chat/completions endpoint."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps({"claim": claim, "context": context}, default=str),
            },
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0,
    }
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    url = base_url.rstrip("/") + "/chat/completions"
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise InferenceUnavailable(f"{type(error).__name__}: {error}") from None

    if len(raw) > MAX_RESPONSE_BYTES:
        raise InferenceUnavailable("response_too_large")

    try:
        envelope = json.loads(raw)
        content = envelope["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, TypeError, ValueError, UnicodeDecodeError) as error:
        raise InferenceUnavailable(f"malformed reply: {type(error).__name__}") from None

    candidates = parsed.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise InferenceUnavailable("reply contained no candidates")

    return {
        "candidates": [str(c) for c in candidates],
        "model_identity": f"model-agnostic/{model}",
        "relations": [str(r) for r in (parsed.get("relations") or [])],
        "reasoning_steps": [str(s) for s in (parsed.get("reasoning_steps") or [])],
        "provenance": {
            "inference": "model-agnostic-http",
            "model": model,
            "base_url": base_url,
            "input_sha256": _stable_digest(claim),
            "configured": True,
            "context_keys": sorted(context.keys()) if isinstance(context, dict) else [],
        },
    }


def is_configured() -> bool:
    """True when an inference endpoint is configured via the environment."""
    return bool(_env(DEFAULT_BASE_URL_ENV) and _env(DEFAULT_MODEL_ENV))


def to_candidate_outputs(
    raw_candidates: Any,
    *,
    confidence: float = 0.0,
) -> List[Any]:
    """Convert an inference result's candidates into the canonical `CandidateOutput` objects.

    The two sides of this boundary speak differently: the adapter yields plain readings (`list[str]`, because
    a deterministic offline path has no model opinion to score), while the evidence contract requires
    `CandidateOutput`. Engines used to do this conversion inline, each in its own way, which is how one shape
    drifts from another. It lives here once.

    **The default confidence is 0.0, deliberately.** A reading produced without a model has no model's
    confidence behind it, and inventing one is the defect this whole module exists to remove. An envelope
    built from this path therefore reports a zero-confidence candidate alongside
    `provenance["inference"] == "offline-deterministic"` -- the pair is the honest statement: here is a reading,
    and nothing was scored.

    Anything already shaped like a `CandidateOutput` is passed through untouched, so an engine that injects a
    real model's output keeps its own confidences.
    """
    from abraxas.evidence.contract import CandidateOutput

    if raw_candidates is None:
        return []

    items = raw_candidates if isinstance(raw_candidates, (list, tuple)) else [raw_candidates]

    converted: List[Any] = []
    for item in items:
        if isinstance(item, CandidateOutput):
            converted.append(item)
        elif isinstance(item, str):
            converted.append(
                CandidateOutput(
                    answer=item,
                    confidence=confidence,
                    reasoning_trace="model-agnostic adapter (no model scored this reading)",
                    relation_steps=[],
                )
            )
        elif isinstance(item, dict):
            converted.append(
                CandidateOutput(
                    answer=str(item.get("answer") or item.get("text") or item),
                    confidence=float(item.get("confidence", confidence)),
                    reasoning_trace=str(item.get("reasoning_trace", "")),
                    relation_steps=[],
                )
            )
    return converted


def identity_of(inference: Callable[..., Any]) -> str:
    """The model identity an engine should REPORT for a given inference callable.

    Every evidence envelope carries a `model_identity`, and the honest value is the one belonging to the
    inference path that actually ran. A callable built by :func:`create_model_agnostic_inference` carries its
    own (`model-agnostic/<model>`, or the offline marker); an injected bespoke callable has no identity of its
    own, and is reported as an unlabelled custom callable rather than borrowing a name it has not earned.

    Why this exists: engines used to hand-write this string -- `"oracle-model-v1"`,
    `"lora-out-transfer-001-t1/checkpoint-48"` -- which named a model that was not loaded, was not present,
    and in one case had never been trained. A provenance field that names something imaginary is worse than
    an empty one, because it reads as evidence of which model produced the reading.
    """
    ident = getattr(inference, "model_identity", None)
    if isinstance(ident, str) and ident:
        return ident
    return "custom/unlabelled"


def create_model_agnostic_inference(
    model: Optional[str] = None,
    *,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    timeout: Optional[float] = None,
    transport: Optional[Callable[..., Dict[str, Any]]] = None,
) -> Callable[[str, Dict[str, Any]], Dict[str, Any]]:
    """Build the inference callable.

    Reads ``ABX_INFERENCE_BASE_URL`` / ``ABX_INFERENCE_MODEL`` /
    ``ABX_INFERENCE_API_KEY`` / ``ABX_INFERENCE_TIMEOUT_SECONDS`` unless overridden
    per argument. With no endpoint configured the deterministic offline path runs.

    ``transport`` is a test seam: it replaces the HTTP call entirely.
    """
    resolved_base = (base_url or _env(DEFAULT_BASE_URL_ENV)).rstrip("/")
    resolved_model = model or _env(DEFAULT_MODEL_ENV) or "unspecified"
    resolved_key = api_key if api_key is not None else _env(DEFAULT_API_KEY_ENV)
    try:
        resolved_timeout = float(
            timeout if timeout is not None else _env(DEFAULT_TIMEOUT_ENV) or 30.0
        )
    except ValueError:
        resolved_timeout = 30.0

    configured = bool(resolved_base and resolved_model != "unspecified")

    def infer(claim: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ctx = context if isinstance(context, dict) else {}
        if not isinstance(claim, str) or not claim.strip():
            raise ValueError("claim must be a non-empty string")
        if not configured:
            return _offline_result(claim, ctx, OFFLINE_IDENTITY)
        if transport is not None:
            return transport(
                claim,
                ctx,
                base_url=resolved_base,
                model=resolved_model,
                api_key=resolved_key,
                timeout=resolved_timeout,
            )
        return _http_result(
            claim,
            ctx,
            base_url=resolved_base,
            model=resolved_model,
            api_key=resolved_key,
            timeout=resolved_timeout,
        )

    # The callable's declared identity must agree with the path it will actually take. Before this, an
    # unconfigured adapter announced `model-agnostic/unspecified` while returning results stamped
    # `model-agnostic/offline-deterministic` -- one state, two names, so an engine reporting its identity and
    # an engine reading its own envelope's provenance would disagree about which path ran.
    infer.model_identity = (  # type: ignore[attr-defined]
        f"model-agnostic/{resolved_model}" if configured else OFFLINE_IDENTITY
    )
    infer.is_configured = configured  # type: ignore[attr-defined]
    return infer


__all__ = [
    "InferenceUnavailable",
    "OFFLINE_IDENTITY",
    "create_model_agnostic_inference",
    "identity_of",
    "is_configured",
    "to_candidate_outputs",
]
