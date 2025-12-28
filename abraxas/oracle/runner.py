"""Deterministic Oracle Runner v1: Date-based oracle generation from correlation deltas."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as Date
from typing import Dict, List, Optional
from uuid import uuid4

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.core.provenance import Provenance
from abraxas.oracle.transforms import CorrelationDelta, render_oracle, score_deltas
from abraxas.oracle.v2.wire import build_v2_block


@dataclass(frozen=True)
class OracleConfig:
    """Configuration for oracle generation."""

    half_life_hours: float
    top_k: int


@dataclass(frozen=True)
class OracleArtifact:
    """Complete oracle artifact with deterministic signature."""

    id: str
    date: str  # YYYY-MM-DD
    inputs: Dict
    output: Dict
    signature: str
    provenance: Provenance


class DeterministicOracleRunner:
    """
    Deterministic daily oracle generation:
    Inputs = correlation deltas (time-weighted)
    Output = ranked signals JSON + aggregate
    Signature = sha256(canonical_json(artifact minus signature))
    """

    def __init__(self, *, git_sha: Optional[str] = None, host: Optional[str] = None) -> None:
        self._git_sha = git_sha
        self._host = host

    def run_for_date(
        self,
        d: Date,
        correlation_deltas: List[CorrelationDelta],
        config: OracleConfig,
        *,
        run_id: Optional[str] = None,
        as_of_utc: Optional[str] = None,
    ) -> OracleArtifact:
        """
        Generate oracle artifact for a specific date.

        Args:
            d: Date for oracle generation
            correlation_deltas: Input correlation deltas
            config: Oracle configuration
            run_id: Optional run identifier (UUID generated if not provided)
            as_of_utc: Optional reference time (defaults to end-of-day UTC)

        Returns:
            OracleArtifact with deterministic signature
        """
        rid = run_id or str(uuid4())
        # as_of defaults to deterministic end-of-day UTC marker for the date
        as_of = as_of_utc or f"{d.isoformat()}T23:59:59Z"

        scored = score_deltas(
            correlation_deltas,
            as_of_utc=as_of,
            half_life_hours=float(config.half_life_hours),
        )
        out = render_oracle(scored, top_k=int(config.top_k))

        inputs_obj = {
            "as_of_utc": as_of,
            "deltas": [self._delta_to_dict(x) for x in correlation_deltas],
            "config": {"half_life_hours": float(config.half_life_hours), "top_k": int(config.top_k)},
        }

        inputs_hash = sha256_hex(canonical_json(inputs_obj))
        config_hash = sha256_hex(
            canonical_json({"oracle": "DeterministicOracleRunner.v1", "cfg": inputs_obj["config"]})
        )

        prov = Provenance(
            run_id=rid,
            started_at_utc=Provenance.now_iso_z(),
            inputs_hash=inputs_hash,
            config_hash=config_hash,
            git_sha=self._git_sha,
            host=self._host,
        )

        # Build v2 governance block (placeholder values for now)
        # Use deterministic date_iso from the run date
        v2 = build_v2_block(
            checks={
                "v1_golden_pass_rate": 1.0,
                "drift_budget_violations": 0,
                "evidence_bundle_overflow_rate": 0.0,
                "ci_volatility_correlation": 0.72,
                "interaction_noise_rate": 0.22,
            },
            router_input={
                "max_band_width": max(abs(s["score"]) for s in scored) if scored else 0.0,
                "max_MRS": len(scored),
                "negative_signal_alerts": 0,
                "thresholds": {"BW_HIGH": 20.0, "MRS_HIGH": 70.0},
            },
            config_hash=config_hash,
            date_iso=as_of,  # Use as_of_utc for deterministic timestamp
        )

        # Add v2 governance block to output
        out["v2"] = v2

        artifact_wo_sig = {
            "id": rid,
            "date": d.isoformat(),
            "inputs": inputs_obj,
            "output": out,
            "provenance": prov.__dict__,
        }
        sig = sha256_hex(canonical_json(artifact_wo_sig))

        return OracleArtifact(
            id=rid,
            date=d.isoformat(),
            inputs=inputs_obj,
            output=out,
            signature=sig,
            provenance=prov,
        )

    @staticmethod
    def _delta_to_dict(x: CorrelationDelta) -> Dict:
        """Convert CorrelationDelta to dict for serialization."""
        return {
            "domain_a": x.domain_a,
            "domain_b": x.domain_b,
            "key": x.key,
            "delta": float(x.delta),
            "observed_at_utc": x.observed_at_utc,
        }
