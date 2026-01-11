from typing import Dict, List


def prisoners_dilemma_default() -> Dict[str, List[List[float]]]:
    return {
        "P1": [[3.0, 0.0], [5.0, 1.0]],
        "P2": [[3.0, 5.0], [0.0, 1.0]],
    }


def matching_pennies_default() -> Dict[str, List[List[float]]]:
    return {
        "P1": [[1.0, -1.0], [-1.0, 1.0]],
        "P2": [[-1.0, 1.0], [1.0, -1.0]],
    }
