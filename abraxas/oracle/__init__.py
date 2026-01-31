"""Oracle Pipeline v1: Deterministic oracle generation from correlation deltas."""

from .runner import DeterministicOracleRunner, OracleArtifact, OracleConfig
from .transforms import CorrelationDelta, decay, render_oracle, score_deltas

# PostgresOracleStore is optional (requires psycopg)
try:
    from .pg_store import PostgresOracleStore

    __all__ = [
        "DeterministicOracleRunner",
        "OracleConfig",
        "OracleArtifact",
        "CorrelationDelta",
        "decay",
        "score_deltas",
        "render_oracle",
        "PostgresOracleStore",
    ]
except ImportError:
    __all__ = [
        "DeterministicOracleRunner",
        "OracleConfig",
        "OracleArtifact",
        "CorrelationDelta",
        "decay",
        "score_deltas",
        "render_oracle",
    ]
