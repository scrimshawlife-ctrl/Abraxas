import json
from pathlib import Path

from abraxas.modules.gtx.sim.engine import run_2p_matrix_game
from abraxas.modules.gtx.sim.games import matching_pennies_default, prisoners_dilemma_default

VEC_DIR = Path(__file__).resolve().parents[1] / "abraxas" / "modules" / "gtx" / "vectors"

GAME_DEFAULTS = {
    "prisoners_dilemma": prisoners_dilemma_default,
    "matching_pennies": matching_pennies_default,
}


def test_gtx_vectors_deterministic() -> None:
    pack = json.loads((VEC_DIR / "vector_pack.v0.1.json").read_text(encoding="utf-8"))
    histories = []
    for _ in range(2):
        run = []
        for vector in pack["vectors"]:
            payoff = GAME_DEFAULTS[vector["game"]]()
            result = run_2p_matrix_game(
                payoff_matrix=payoff,
                strat1=vector["strategy_p1"],
                strat2=vector["strategy_p2"],
                rounds=vector["rounds"],
                seed=vector["seed"],
                params1=vector["params_p1"],
                params2=vector["params_p2"],
            )
            run.append((vector["id"], result["history"]))
        histories.append(run)

    assert histories[0] == histories[1]


def test_gtx_expected_outputs() -> None:
    pack = json.loads((VEC_DIR / "vector_pack.v0.1.json").read_text(encoding="utf-8"))
    expectations = json.loads((VEC_DIR / "expected_outputs.v0.1.json").read_text(encoding="utf-8"))
    expectation_map = {item["id"]: item for item in expectations["expectations"]}

    for vector in pack["vectors"]:
        payoff = GAME_DEFAULTS[vector["game"]]()
        result = run_2p_matrix_game(
            payoff_matrix=payoff,
            strat1=vector["strategy_p1"],
            strat2=vector["strategy_p2"],
            rounds=vector["rounds"],
            seed=vector["seed"],
            params1=vector["params_p1"],
            params2=vector["params_p2"],
        )
        expect = expectation_map[vector["id"]]
        assertions = expect["assertions"]

        if "p2_avg_min" in assertions:
            assert result["p2_avg"] >= assertions["p2_avg_min"]
        if "p1_avg_max" in assertions:
            assert result["p1_avg"] <= assertions["p1_avg_max"]
        if "p1_avg_min" in assertions:
            assert result["p1_avg"] >= assertions["p1_avg_min"]
        if "p2_avg_min" in assertions:
            assert result["p2_avg"] >= assertions["p2_avg_min"]
        if "abs_diff_avg_max" in assertions:
            assert abs(result["p1_avg"] - result["p2_avg"]) <= assertions["abs_diff_avg_max"]
