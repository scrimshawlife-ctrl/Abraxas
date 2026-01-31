"""FastAPI routes for lexicon registration and oracle execution."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from abraxas.lexicon.engine import InMemoryLexiconRegistry, LexiconEngine, LexiconEntry, LexiconPack
from abraxas.oracle.runner import DeterministicOracleRunner, OracleConfig
from abraxas.oracle.transforms import CorrelationDelta

router = APIRouter()


def _lexicon_engine() -> LexiconEngine:
    """Get lexicon engine with Postgres registry if available, else in-memory."""
    try:
        from abraxas.lexicon.pg_registry import PostgresLexiconRegistry

        reg = PostgresLexiconRegistry()
        return LexiconEngine(reg)
    except Exception:
        # Fall back to in-memory if Postgres not available
        return LexiconEngine(InMemoryLexiconRegistry())


@router.post("/lexicons/register")
def register_lexicon(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Register a lexicon pack.

    Request payload:
        domain: str - Domain identifier
        version: str - Version string
        created_at_utc: str (optional) - ISO8601 timestamp
        entries: list[{token, weight, meta}] - Lexicon entries

    Returns:
        Success status with domain, version, and entry count
    """
    try:
        domain = str(payload["domain"])
        version = str(payload["version"])
        created_at = str(payload.get("created_at_utc") or LexiconPack.now_iso_z())
        entries = tuple(
            LexiconEntry(
                token=str(e["token"]),
                weight=float(e["weight"]),
                meta=dict(e.get("meta", {})),
            )
            for e in payload["entries"]
        )
        pack = LexiconPack(domain=domain, version=version, entries=entries, created_at_utc=created_at)
        eng = _lexicon_engine()
        eng.register(pack)
        return {"ok": True, "domain": domain, "version": version, "count": len(entries)}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"missing field: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/oracle/run")
def run_oracle(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run oracle for a specific date with correlation deltas.

    Request payload:
        date: str - YYYY-MM-DD
        deltas: list[{domain_a, domain_b, key, delta, observed_at_utc}]
        config: {half_life_hours, top_k} (optional)
        run_id: str (optional) - Run identifier
        as_of_utc: str (optional) - ISO8601 timestamp
        store: bool (optional) - Persist to Postgres if true

    Returns:
        Oracle artifact with id, date, inputs, output, signature, and provenance
    """
    try:
        d = date.fromisoformat(str(payload["date"]))
        cfg_obj = payload.get("config") or {}
        cfg = OracleConfig(
            half_life_hours=float(cfg_obj.get("half_life_hours", 24.0)),
            top_k=int(cfg_obj.get("top_k", 12)),
        )
        deltas = [
            CorrelationDelta(
                domain_a=str(x["domain_a"]),
                domain_b=str(x["domain_b"]),
                key=str(x["key"]),
                delta=float(x["delta"]),
                observed_at_utc=str(x["observed_at_utc"]),
            )
            for x in payload["deltas"]
        ]

        runner = DeterministicOracleRunner()
        art = runner.run_for_date(
            d,
            deltas,
            cfg,
            run_id=payload.get("run_id"),
            as_of_utc=payload.get("as_of_utc"),
        )

        if bool(payload.get("store", False)):
            from abraxas.oracle.pg_store import PostgresOracleStore

            PostgresOracleStore().upsert(art)

        return {
            "id": art.id,
            "date": art.date,
            "inputs": art.inputs,
            "output": art.output,
            "signature": art.signature,
            "provenance": asdict(art.provenance),
        }
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"missing field: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/oracle/{artifact_id}")
def get_oracle(artifact_id: str) -> Dict[str, Any]:
    """
    Fetch oracle artifact by ID from Postgres store.

    Args:
        artifact_id: Oracle artifact ID

    Returns:
        Oracle artifact with id, date, inputs, output, signature, and provenance
    """
    try:
        from abraxas.oracle.pg_store import PostgresOracleStore

        store = PostgresOracleStore()
        art = store.get(artifact_id)
        if art is None:
            raise HTTPException(status_code=404, detail=f"Oracle artifact not found: {artifact_id}")

        return {
            "id": art.id,
            "date": art.date,
            "inputs": art.inputs,
            "output": art.output,
            "signature": art.signature,
            "provenance": asdict(art.provenance),
        }
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except ImportError:
        raise HTTPException(status_code=503, detail="Postgres support not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
