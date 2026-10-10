"""Run each live engine twice on identical input and report per-criterion verdicts.

Why this exists
---------------
The settlement survey (`scripts/survey_engine_settlements.py`) evaluates every
engine against six technical-settlement criteria from the doctrine.  Four of
them require actually RUNNING the engine -- determinism, replay, provenance,
and canonical artifacts -- and the survey could only report ``?`` (unmeasured)
for those.  This module makes three of the four measurable.

Trap handled
------------
The envelope carries ``timestamp`` (wall clock at construction), ``evidence_id``
(a ``uuid4()``), and ``schema_version`` (a format descriptor).  These are
METADATA, not content.  A harness that compares or hashes whole envelopes will
label every engine non-deterministic for reasons that have nothing to do with
its reasoning.  The correct fix is to EXCLUDE them from the identity comparison
and name them explicitly -- see ``NON_CONTENT_FIELDS``.  The WRONG fix is to
delete them from the envelope, which is exactly the mistake Phase 1 of the
single-home plan made with ``schema_version``: it was removed to resolve a
divergence and silently broke ``EvidenceSchemaMigrator`` idempotence.

Usage
-----
    from abraxas.engines.execution_harness import measure
    verdict = measure("athanor")
    # {'determinism': 'yes', 'provenance': 'yes', 'canonical_artifacts': 'yes',
    #  'replay': '?', 'reason': ''}
"""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.engines.manifest import ENGINES, LIVE, EngineSpec

# ---------------------------------------------------------------------------
# Non-content fields -- excluded from the identity comparison because they
# are metadata, not content.  Named explicitly so the exclusion is reviewable.
# ---------------------------------------------------------------------------

NON_CONTENT_FIELDS: Tuple[str, ...] = (
    "timestamp",
    # ^ wall clock at envelope construction; varies every call
    "evidence_id",
    # ^ uuid4(); unique per envelope instance by design
    "schema_version",
    # ^ format descriptor on the artifact -- read by EvidenceSchemaMigrator
    #   to decide whether migration is needed, but it describes the FORMAT,
    #   not the reasoning output.  Included on the artifact, excluded from
    #   content hashes (same identity-versus-metadata rule applied to the
    #   lexicon content fingerprint).
)

# ---------------------------------------------------------------------------
# Engine construction -- reusable pattern from the agreement guard
# ---------------------------------------------------------------------------

_STUB_INFERENCE = lambda claim, context: {  # noqa: E731
    "candidates": [],
    "model_identity": "harness-stub",
    "relations": [],
    "reasoning_steps": [],
    "provenance": {"source": "harness-stub"},
}


def _construct_engine(spec: EngineSpec):
    """Resolve and construct a provider from an EngineSpec.

    Reuses exactly the pattern from
    ``tests/test_engine_manifest_agreement.py``: classes are no-arg
    constructed, factories receive a deterministic stand-in inference
    callable when their signature requires one.
    """
    module_path, attribute = spec.implementation.split(":", 1)
    module = importlib.import_module(module_path)
    target = getattr(module, attribute)

    if isinstance(target, type):
        return target()

    # Factory function -- supply a deterministic stub when the signature
    # declares ``inference_engine``.
    params = inspect.signature(target).parameters
    kwargs: Dict[str, Any] = {}
    if "inference_engine" in params:
        kwargs["inference_engine"] = _STUB_INFERENCE
    return target(**kwargs)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _content_dict(envelope_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of *envelope_dict* with non-content fields removed."""
    return {k: v for k, v in envelope_dict.items() if k not in NON_CONTENT_FIELDS}


def run_once(
    engine, request_id: str, claim: str, context: Dict[str, Any]
) -> Dict[str, Any]:
    """Return one evidence envelope as a plain mapping."""
    return engine.produce_evidence(request_id, claim, context).to_dict()


# ---------------------------------------------------------------------------
# Replay -- persist an artifact, reload it, and reproduce the run
# ---------------------------------------------------------------------------
#
# This mirrors the replay contract this repository already uses for runes: a
# source hash, a replay hash, and an ``identical_output`` verdict, emitted as a
# ``RuneReplayPacket`` by ``core/execution/replay_runner.py`` and written to
# ``out/replay/latest.json``.  That implementation operates on a
# ``ShadowExecutionRun``, which an engine envelope is not, so this mirrors the
# CONTRACT rather than forcing a type that does not fit it.
#
# Replay is NOT determinism repeated.  Determinism compares two in-process runs.
# Replay additionally requires the result to survive PERSISTENCE: the artifact is
# written out, read back, and must match a fresh run.  An envelope that cannot
# round-trip through canonical JSON fails replay while passing determinism, and
# that difference is the measurement.

REPLAY_YES = "yes"
REPLAY_NO = "no"
REPLAY_UNMEASURED = "?"


def replay_probe(
    engine,
    request_id: str,
    claim: str,
    context: Dict[str, Any],
    *,
    artifact_dir: Optional[str] = None,
) -> Tuple[str, str]:
    """Persist one envelope, reload it, reproduce the run, and compare.

    Returns ``(status, reason)`` where status is ``yes``, ``no``, or ``?``.

    The two failure kinds are deliberately separated, because blaming the engine
    for the harness would be wrong and so would the reverse:

    ``no``  -- the envelope cannot be replayed: it is not canonically
               serializable, or the stored artifact does not reproduce.  That is
               a property of the engine's output.
    ``?``   -- the artifact could not be persisted at all (a filesystem or
               environment limitation).  Nothing was learned about the engine.
    """
    import json
    import shutil
    import tempfile

    first = run_once(engine, request_id, claim, context)
    source_content = _content_dict(first)

    try:
        serialized = canonical_json(source_content)
        source_hash = sha256_hex(serialized)
    except Exception as exc:
        return REPLAY_NO, (
            f"the envelope is not canonically serializable, so it cannot be replayed: {exc}"
        )

    scratch = artifact_dir or tempfile.mkdtemp(prefix="abx-replay-")
    try:
        artifact = Path(scratch) / "envelope.json"
        artifact.write_text(serialized, encoding="utf-8")

        # Reload -- the artifact must survive the round trip.
        reloaded = json.loads(artifact.read_text(encoding="utf-8"))

        # Reproduce the run and compare against the RELOADED artifact, not the
        # in-memory one; comparing against the original would test nothing new.
        reproduced = _content_dict(run_once(engine, request_id, claim, context))
    except OSError as exc:
        return REPLAY_UNMEASURED, f"could not persist a replay artifact: {exc}"
    except Exception as exc:
        return REPLAY_NO, f"replay could not be completed: {exc}"
    finally:
        if artifact_dir is None:
            shutil.rmtree(scratch, ignore_errors=True)

    replay_hash = sha256_hex(canonical_json(reproduced))
    if reloaded != reproduced:
        return REPLAY_NO, (
            "replay mismatch: the stored artifact does not reproduce "
            f"(stored {source_hash[:12]}..., reproduced {replay_hash[:12]}...)"
        )
    return REPLAY_YES, ""


def measure(engine_name: str) -> Dict[str, str]:
    """Run one engine twice on identical input and return a verdict per criterion.

    Returns a dict with keys ``determinism``, ``provenance``,
    ``canonical_artifacts``, ``replay`` (each ``'yes'``, ``'no'``, or
    ``'?'``), plus ``reason`` -- populated when a criterion fails.

    ``replay`` is always ``'?'`` because this harness cannot establish it
    honestly: replay requires loading a stored artifact and reproducing the
    result, which needs artifact persistence infrastructure this module does
    not own.
    """
    spec = _resolve_spec(engine_name)
    if spec is None:
        return {
            "determinism": "no",
            "provenance": "no",
            "canonical_artifacts": "no",
            "replay": "?",
            "reason": f"engine '{engine_name}' not found in manifest",
        }

    if spec.status != LIVE:
        return {
            "determinism": "?",
            "provenance": "?",
            "canonical_artifacts": "?",
            "replay": "?",
            "reason": f"engine '{engine_name}' is {spec.status}, not live",
        }

    reason_parts: list[str] = []

    # ---- Construct the engine -------------------------------------------------
    try:
        provider = _construct_engine(spec)
    except Exception as exc:
        return {
            "determinism": "no",
            "provenance": "no",
            "canonical_artifacts": "no",
            "replay": "?",
            "reason": f"construction failed: {exc}",
        }

    # ---- Run twice on identical input -----------------------------------------
    request_id = "harness-determinism-001"
    claim = "Does this engine produce identical output on identical input?"
    context: Dict[str, Any] = {}

    try:
        d1 = run_once(provider, request_id, claim, context)
    except Exception as exc:
        return {
            "determinism": "no",
            "provenance": "no",
            "canonical_artifacts": "no",
            "replay": "?",
            "reason": f"first run raised: {exc}",
        }

    try:
        d2 = run_once(provider, request_id, claim, context)
    except Exception as exc:
        return {
            "determinism": "no",
            "provenance": "no",
            "canonical_artifacts": "no",
            "replay": "?",
            "reason": f"second run raised: {exc}",
        }

    # ---- Determinism: content dicts are identical -----------------------------
    c1 = _content_dict(d1)
    c2 = _content_dict(d2)
    determinism = "yes" if c1 == c2 else "no"
    if determinism == "no":
        reason_parts.append(
            "non-deterministic: content differed between runs"
        )

    # ---- Provenance: present and non-empty ------------------------------------
    prov1 = d1.get("provenance", {})
    prov2 = d2.get("provenance", {})
    provenance_ok = bool(prov1) and bool(prov2)
    provenance = "yes" if provenance_ok else "no"
    if provenance == "no":
        reason_parts.append("provenance is empty or missing")

    # ---- Canonical artifacts: content hashes stably ---------------------------
    canonical = "yes"
    try:
        h1 = sha256_hex(canonical_json(c1))
        h2 = sha256_hex(canonical_json(c2))
    except Exception as exc:
        canonical = "no"
        reason_parts.append(f"canonical serialization failed: {exc}")
    else:
        if h1 != h2:
            canonical = "no"
            reason_parts.append(
                "canonical hashes differ between runs "
                f"(h1={h1[:12]}..., h2={h2[:12]}...)"
            )
        elif not h1:
            canonical = "no"
            reason_parts.append("canonical hash is empty")

    # ---- Replay: persist the artifact, reload it, reproduce the run ------------
    #
    # Distinct from determinism above: that compares two in-process runs; this
    # requires the result to survive being written, read back, and reproduced.
    try:
        replay, replay_reason = replay_probe(provider, request_id, claim, context)
    except Exception as exc:  # the probe handles its own failures; belt and braces
        replay, replay_reason = REPLAY_UNMEASURED, f"replay probe raised: {exc}"
    if replay_reason:
        reason_parts.append(replay_reason)

    return {
        "determinism": determinism,
        "provenance": provenance,
        "canonical_artifacts": canonical,
        "replay": replay,
        "reason": "; ".join(reason_parts) if reason_parts else "",
    }


def _resolve_spec(engine_name: str) -> EngineSpec | None:
    """Look up an EngineSpec by name from the manifest."""
    for spec in ENGINES:
        if spec.name == engine_name:
            return spec
    return None


def get_synthesis_label(state: str, blocker: str | None = None) -> str:
    """Tighten synthesis label for exact-match (P1 snapshot refinement).
    Bound + EXACT_MATCH -> NON_DEGRADED with explicit blocker precedence.
    """
    if state == "EXACT_MATCH" and not blocker:
        return "NON_DEGRADED"
    if blocker:
        return "DEGRADED"
    return "DEGRADED" if state != "EXACT_MATCH" else "NON_DEGRADED"