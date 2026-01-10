import json
from pathlib import Path

from .sim.engine import run_2p_matrix_game
from .sim.games import matching_pennies_default, prisoners_dilemma_default
from .sim.metrics import cooperation_rate, defection_streaks

VEC_DIR = Path(__file__).resolve().parent / "vectors"

GAME_DEFAULTS = {
    "prisoners_dilemma": prisoners_dilemma_default,
    "matching_pennies": matching_pennies_default,
}


def register(subparsers) -> None:
    parser = subparsers.add_parser("gtx")
    sub = parser.add_subparsers(dest="gtx_cmd")
    run_cmd = sub.add_parser("run-vectors")
    run_cmd.set_defaults(func=run_vectors)


def run_vectors(_args) -> None:
    pack = json.loads((VEC_DIR / "vector_pack.v0.1.json").read_text(encoding="utf-8"))
    out = []

    for vector in pack["vectors"]:
        game = vector["game"]
        payoff = GAME_DEFAULTS[game]()
        result = run_2p_matrix_game(
            payoff_matrix=payoff,
            strat1=vector["strategy_p1"],
            strat2=vector["strategy_p2"],
            rounds=vector["rounds"],
            seed=vector["seed"],
            params1=vector["params_p1"],
            params2=vector["params_p2"],
        )

        metrics = {
            "cooperation_rate": cooperation_rate(result["history"]),
            "defection_streaks": defection_streaks(result["history"]),
        }
        out.append({"id": vector["id"], "result": result, "metrics": metrics})

    print(json.dumps({"gtx_version": "0.1.0", "runs": out}, indent=2))
