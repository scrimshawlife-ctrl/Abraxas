from __future__ import annotations

from abx.deployment.types import DeploymentGovernanceScorecard
from abx.util.jsonutil import dumps_stable



def serialize_deployment_scorecard(scorecard: DeploymentGovernanceScorecard) -> str:
    return dumps_stable(scorecard.__dict__)
