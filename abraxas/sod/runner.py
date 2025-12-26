"""
SOD Bundle Runner

Non-breaking adapter that calls NCP/CNF/EFTE modules if available.
Uses try/except import guards to remain operational when modules are incomplete.
"""

from __future__ import annotations

from typing import Any, Dict


def run_sod_bundle(context: Dict[str, Any], sim_priors: Dict[str, float]) -> Dict[str, Any]:
    """
    Execute SOD bundle (NCP + CNF + EFTE) with simulation priors.

    Attempts to import and run each module. If module is unavailable or
    execution fails, returns empty but well-formed structure for that component.

    Args:
        context: Context dictionary (weather, D/M snapshot, etc.)
        sim_priors: Simulation priors (MRI, IRI, tau_memory, tau_latency)

    Returns:
        Dictionary with ncp, cnf, efte outputs (may be empty if modules unavailable)
    """

    result = {
        "ncp": {"paths": []},
        "cnf": {"counters": []},
        "efte": {"thresholds": []},
    }

    # Try NCP (Narrative Cascade Predictor)
    try:
        from abraxas.sod.ncp import NarrativeCascadePredictor

        ncp = NarrativeCascadePredictor()
        # NCP may need SODInput; for now pass priors in context
        ncp_context = {**context, "sim_priors": sim_priors}
        ncp_output = ncp.predict(ncp_context)
        result["ncp"] = ncp_output if ncp_output else {"paths": []}
    except (ImportError, AttributeError, Exception):
        # Module not available or incomplete
        pass

    # Try CNF (Counter-Narrative Forecaster)
    try:
        from abraxas.sod.cnf import CounterNarrativeForecaster

        cnf = CounterNarrativeForecaster()
        cnf_context = {**context, "sim_priors": sim_priors}
        cnf_output = cnf.forecast(cnf_context)
        result["cnf"] = cnf_output if cnf_output else {"counters": []}
    except (ImportError, AttributeError, Exception):
        pass

    # Try EFTE (Epistemic Fatigue Threshold Engine)
    try:
        from abraxas.sod.efte import EpistemicFatigueThresholdEngine

        efte = EpistemicFatigueThresholdEngine()
        efte_context = {**context, "sim_priors": sim_priors}
        efte_output = efte.compute(efte_context)
        result["efte"] = efte_output if efte_output else {"thresholds": []}
    except (ImportError, AttributeError, Exception):
        pass

    return result
