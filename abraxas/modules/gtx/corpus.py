from typing import Dict, List


def corpus_spec() -> Dict[str, List[str]]:
    return {
        "strategic_form": [
            "nash_equilibrium",
            "dominant_strategies",
            "mixed_strategies",
        ],
        "repeated_games": [
            "cooperation_emergence",
            "punishment_forgiveness_noise",
        ],
        "signaling_info": [
            "cheap_talk",
            "costly_signals",
            "screening",
        ],
        "mechanism_design": [
            "incentive_compatibility",
            "auctions",
            "principal_agent",
        ],
        "network_games": [
            "cascades_contagion",
            "coordination_on_graphs",
        ],
    }
