"""
Active Learning Loops v0.1

Closed-loop learning system that turns backtest failures into deterministic improvements.

Components:
- failure_analyzer: Generate failure artifacts from MISS/ABSTAIN backtests
- proposal_generator: Create bounded proposals from failure analyses
- sandbox_runner: Execute proposals against historical data
- promotion_gate: Validate promotion criteria

No ML. No vibes. Just disciplined iteration.
"""

from abraxas.learning.schema import (
    FailureAnalysis,
    Proposal,
    ProposalType,
    SandboxReport,
    PromotionEntry,
)
from abraxas.learning.failure_analyzer import (
    FailureAnalyzer,
    analyze_backtest_failure,
)
from abraxas.learning.proposal_generator import (
    ProposalGenerator,
    generate_proposal,
)
from abraxas.learning.sandbox_runner import (
    SandboxRunner,
    run_sandbox,
)
from abraxas.learning.promotion_gate import (
    PromotionGate,
    promote_proposal,
)

__all__ = [
    # Schema
    "FailureAnalysis",
    "Proposal",
    "ProposalType",
    "SandboxReport",
    "PromotionEntry",
    # Failure Analyzer
    "FailureAnalyzer",
    "analyze_backtest_failure",
    # Proposal Generator
    "ProposalGenerator",
    "generate_proposal",
    # Sandbox Runner
    "SandboxRunner",
    "run_sandbox",
    # Promotion Gate
    "PromotionGate",
    "promote_proposal",
]
