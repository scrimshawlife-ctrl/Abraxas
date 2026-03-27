from __future__ import annotations

from abx.security.types import SecurityIntegrityScorecard
from abx.util.jsonutil import dumps_stable


def serialize_security_integrity_scorecard(scorecard: SecurityIntegrityScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
