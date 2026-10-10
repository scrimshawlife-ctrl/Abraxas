from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

import abx.term_claims_run as term_claims_run


class _Metrics:
    def __init__(self, values: dict[str, Any]) -> None:
        self.values = values

    def to_dict(self) -> dict[str, Any]:
        return dict(self.values)


def _install_main_stubs(
    monkeypatch: pytest.MonkeyPatch,
    *,
    items: list[dict[str, Any]],
    assignments: dict[str, list[str]],
    clusters_by_term: dict[str, list[list[int]]] | None = None,
    metrics_by_term: dict[str, dict[str, Any]] | None = None,
    weights: dict[tuple[str, str], float] | None = None,
    cips: dict[tuple[str, str], float] | None = None,
) -> dict[str, Any]:
    calls: dict[str, Any] = {
        "load_sources": [],
        "extract": [],
        "evidence": [],
        "token_terms": [],
        "assign": [],
        "support": [],
        "csp": [],
        "cluster": [],
        "invoke": [],
    }
    clusters_by_term = clusters_by_term or {}
    metrics_by_term = metrics_by_term or {}
    weights = weights or {}
    cips = cips or {}

    def load_sources(path: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        calls["load_sources"].append(path)
        return [{"source_id": "source-1"}], {"signals": ["signal-1"]}

    def extract(
        sources: list[dict[str, Any]], *, run_id: str, max_per_source: int
    ) -> list[dict[str, Any]]:
        calls["extract"].append((sources, run_id, max_per_source))
        return json.loads(json.dumps(items))

    def evidence(path: str) -> dict[str, list[dict[str, Any]]]:
        calls["evidence"].append(path)
        return {"alpha": [{"bundle_id": "bundle-1"}]}

    def build_index(terms: list[str]) -> dict[str, list[str]]:
        calls["token_terms"].append(list(terms))
        return {term: [term] for term in terms}

    def assign(
        claim: str, token_index: dict[str, list[str]], *, min_overlap: int, max_terms: int
    ) -> list[str]:
        calls["assign"].append((claim, token_index, min_overlap, max_terms))
        return list(assignments.get(claim, []))

    def support(
        *, term: str, claim_text: str, evidence_by_term: dict[str, list[dict[str, Any]]]
    ) -> tuple[float, dict[str, Any]]:
        calls["support"].append((term, claim_text, evidence_by_term))
        return weights.get((term, claim_text), 0.0), {"claim": claim_text, "term": term}

    def compute_csp(
        *, claim_text: str, term_csp: dict[str, Any], evidence_support_weight: float
    ) -> dict[str, Any]:
        call_index = calls.setdefault("csp_count", {}).get(claim_text, 0)
        assigned_terms = assignments.get(claim_text, [])
        term = assigned_terms[call_index] if call_index < len(assigned_terms) else ""
        calls["csp_count"][claim_text] = call_index + 1
        calls["csp"].append((claim_text, term_csp, evidence_support_weight, term))
        return {
            "term": term,
            "CIP": cips.get((term, claim_text), 0.0),
            "COH": bool(term_csp.get("COH")),
            "EA": float(term_csp.get("EA") or 0.0),
        }

    def cluster(
        sub_items: list[dict[str, Any]], *, sim_threshold: float, max_pairs: int
    ) -> tuple[list[list[int]], _Metrics]:
        term = str(sub_items[0].get("claim_csp", {}).get("term") or "")
        calls["cluster"].append((term, list(sub_items), sim_threshold, max_pairs))
        return clusters_by_term.get(term, []), _Metrics(
            metrics_by_term.get(term, {"consensus_gap": 0.0, "n_items": len(sub_items)})
        )

    def invoke(
        capability: str, payload: dict[str, Any], *, ctx: Any, strict_execution: bool
    ) -> dict[str, Any]:
        calls["invoke"].append((capability, payload, ctx, strict_execution))
        return {"artifact": payload["artifact"]}

    monkeypatch.setattr(term_claims_run, "load_sources_from_osh", load_sources)
    monkeypatch.setattr(term_claims_run, "extract_claim_items_from_sources", extract)
    monkeypatch.setattr(term_claims_run, "evidence_by_term", evidence)
    monkeypatch.setattr(term_claims_run, "build_term_token_index", build_index)
    monkeypatch.setattr(term_claims_run, "assign_claim_to_terms", assign)
    monkeypatch.setattr(term_claims_run, "support_weight_for_claim", support)
    monkeypatch.setattr(term_claims_run, "compute_claim_csp", compute_csp)
    monkeypatch.setattr(term_claims_run, "cluster_claims", cluster)
    monkeypatch.setattr(term_claims_run, "invoke_capability", invoke)
    return calls


def _run_main(monkeypatch: pytest.MonkeyPatch, argv: list[str]) -> int:
    monkeypatch.setattr(sys, "argv", ["term_claims_run", *argv])
    return term_claims_run.main()


def test_load_terms_from_a2_deduplicates_case_insensitively_and_caps(tmp_path: Path) -> None:
    source = tmp_path / "a2.json"
    source.write_text(
        json.dumps(
            {
                "raw_full": {
                    "profiles": [
                        None,
                        {"term": "Alpha"},
                        {"term": "alpha"},
                        {"term": " "},
                        {"term": 42},
                        {"term": "Beta"},
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    assert term_claims_run._load_terms_from_a2(str(source)) == ["Alpha", "42", "Beta"]
    assert term_claims_run._load_terms_from_a2(str(source), max_terms=2) == ["Alpha"]


def test_load_terms_from_a2_uses_view_fallback_and_fails_closed(tmp_path: Path) -> None:
    source = tmp_path / "a2.json"
    source.write_text(
        json.dumps(
            {
                "raw_full": {"profiles": "not-a-list"},
                "views": {
                    "profiles_top": [
                        {"term": "Gamma"},
                        {"term": "gamma"},
                        {"term": ""},
                        "not-a-profile",
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    assert term_claims_run._load_terms_from_a2(str(source)) == ["Gamma"]

    source.write_text(json.dumps({"raw_full": {"profiles": {}}}), encoding="utf-8")
    assert term_claims_run._load_terms_from_a2(str(source)) == []
    assert term_claims_run._load_terms_from_a2(str(tmp_path / "missing.json")) == []

    source.write_text("{invalid", encoding="utf-8")
    assert term_claims_run._load_terms_from_a2(str(source)) == []


def test_main_builds_weighted_clusters_and_keeps_strongest_item_csp(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    report_dir = tmp_path / "out" / "reports"
    report_dir.mkdir(parents=True)
    a2_path = report_dir / "a2_phase_run-1.json"
    a2_path.write_text(
        json.dumps(
            {
                "raw_full": {
                    "profiles": [
                        None,
                        {
                            "term": "ALPHA",
                            "term_csp_summary": {"COH": True, "EA": 0.3, "CIP": 0.12},
                        },
                        {"term": " ", "term_csp_summary": {"CIP": 0.9}},
                        {"term": "ignored", "term_csp_summary": "bad"},
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    items = [
        {"claim": "claim-0"},
        {"claim": "claim-1", "claim_csp": {"CIP": 0.01, "COH": False}},
        {"claim": "claim-2", "claim_csp": {"CIP": 0.9, "COH": True}},
        {"claim": "claim-3", "evidence_support_weight": 0.5, "claim_csp": None},
        {"claim": "claim-4", "claim_csp": {}},
    ]
    weights = {("alpha", "claim-0"): 0.1, ("alpha", "claim-1"): 0.2, ("alpha", "claim-3"): 0.05}
    cips = {
        ("alpha", f"claim-{index}"): value for index, value in enumerate((0.1, 0.2, 0.3, 0.4, 0.5))
    }
    calls = _install_main_stubs(
        monkeypatch,
        items=items,
        assignments={f"claim-{index}": ["alpha"] for index in range(5)},
        clusters_by_term={"alpha": [[0, 1], [2, 3, 4]]},
        metrics_by_term={"alpha": {"consensus_gap": 0.25, "n_items": 5, "algorithm": "fixture"}},
        weights=weights,
        cips=cips,
    )

    assert _run_main(monkeypatch, ["--run-id", "run-1", "--osh-ledger", "ledger.jsonl"]) == 0

    result = json.loads((report_dir / "term_claims_run-1.json").read_text(encoding="utf-8"))
    invocation = calls["invoke"][0]
    payload = invocation[1]
    assert invocation[0] == "RUNE.EVOLVE.POLICY.ENFORCE_NON_TRUNCATION"
    assert invocation[3] is True
    assert invocation[2].run_id == "run-1"
    assert calls["load_sources"] == ["ledger.jsonl"]
    assert calls["extract"] == [([{"source_id": "source-1"}], "run-1", 5)]
    assert calls["evidence"] == ["out/evidence_bundles"]
    assert calls["token_terms"] == [["alpha", "ignored"]]
    assert result["version"] == "term_claims.v0.2"
    assert result["run_id"] == "run-1"
    assert result["provenance"]["a2_phase"] == "out/reports/a2_phase_run-1.json"
    assert result["metrics"]["n_terms"] == 1
    metric = result["metrics"]["term_consensus"]["alpha"]
    assert metric["consensus_gap_unweighted"] == 0.25
    assert metric["consensus_gap"] == pytest.approx(1.0 - 3.05 / 5.35)
    assert metric["evidence_weighted"] is True
    assert result["views"]["top_terms_by_gap"] == [
        {"term": "alpha", "consensus_gap": pytest.approx(1.0 - 3.05 / 5.35), "n_items": 5}
    ]
    assert payload["raw_full"]["term_clusters"] == {"alpha": [[0, 1], [2, 3, 4]]}
    saved_items = payload["raw_full"]["items"]
    assert saved_items[0]["claim_csp"]["CIP"] == 0.1
    assert saved_items[1]["claim_csp"]["CIP"] == 0.2
    assert saved_items[2]["claim_csp"]["CIP"] == 0.9
    assert saved_items[3]["evidence_support_weight"] == 0.5
    assert saved_items[3]["evidence_support_weight_by_term"]["alpha"] == 0.05
    assert saved_items[4]["claim_csp"]["CIP"] == 0.5
    assert (
        capsys.readouterr().out == "[TERM_CLAIMS_RUN] wrote: out/reports/term_claims_run-1.json\n"
    )


def test_main_skips_terms_below_minimum_claim_count(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    (report_dir / "a2_phase_sparse.json").write_text(
        json.dumps({"raw_full": {"profiles": [{"term": "alpha"}]}}), encoding="utf-8"
    )
    calls = _install_main_stubs(
        monkeypatch,
        items=[{"claim": "too-few"}],
        assignments={"too-few": ["alpha"]},
    )

    assert (
        _run_main(
            monkeypatch,
            ["--run-id", "sparse", "--out-reports", "reports", "--min-claims-per-term", "2"],
        )
        == 0
    )

    result = json.loads((report_dir / "term_claims_sparse.json").read_text(encoding="utf-8"))
    assert result["metrics"] == {"n_terms": 0, "term_consensus": {}}
    assert result["views"]["top_terms_by_gap"] == []
    assert calls["assign"] == [("too-few", {"alpha": ["alpha"]}, 1, 4)]
    assert calls["cluster"] == []


def test_main_uses_view_terms_and_sorts_zero_and_equal_weight_gaps(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    (report_dir / "a2_phase_views.json").write_text(
        json.dumps(
            {
                "raw_full": {},
                "views": {"profiles_top": [{"term": "gamma"}, {"term": "alpha"}, {"term": "beta"}]},
            }
        ),
        encoding="utf-8",
    )
    items = [{"claim": f"claim-{index}"} for index in range(5)]
    assignments = {item["claim"]: ["gamma", "alpha", "beta"] for item in items}
    calls = _install_main_stubs(
        monkeypatch,
        items=items,
        assignments=assignments,
        clusters_by_term={
            "alpha": [],
            "beta": [[0, 1], [2, 3, 4]],
            "gamma": [[0, 1], [2, 3, 4]],
        },
        metrics_by_term={
            "alpha": {"consensus_gap": 0.9, "n_items": 5},
            "beta": {"consensus_gap": 0.9, "n_items": 5},
            "gamma": {"consensus_gap": 0.9, "n_items": 5},
        },
        cips={(term, item["claim"]): 0.1 for term in ("alpha", "beta", "gamma") for item in items},
    )

    assert _run_main(monkeypatch, ["--run-id", "views", "--out-reports", "reports"]) == 0

    result = json.loads((report_dir / "term_claims_views.json").read_text(encoding="utf-8"))
    assert calls["token_terms"] == [["gamma", "alpha", "beta"]]
    assert result["metrics"]["n_terms"] == 3
    assert result["metrics"]["term_consensus"]["alpha"]["consensus_gap"] == 0.0
    top = result["views"]["top_terms_by_gap"]
    assert [entry["term"] for entry in top] == ["beta", "gamma", "alpha"]
    assert top[0]["consensus_gap"] == pytest.approx(0.4)


def test_main_invalid_a2_fails_closed_with_no_terms(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "broken.json").write_text("not-json", encoding="utf-8")
    calls = _install_main_stubs(monkeypatch, items=[], assignments={})

    assert _run_main(monkeypatch, ["--run-id", "broken", "--a2-phase", "broken.json"]) == 0

    result = json.loads(
        (tmp_path / "out" / "reports" / "term_claims_broken.json").read_text(encoding="utf-8")
    )
    assert result["metrics"] == {"n_terms": 0, "term_consensus": {}}
    assert calls["token_terms"] == [[]]
    assert calls["assign"] == []
    assert calls["cluster"] == []


def test_main_requires_run_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["term_claims_run"])
    with pytest.raises(SystemExit) as exc_info:
        term_claims_run.main()
    assert exc_info.value.code == 2


def test_module_entrypoint_runs_main_and_exits_zero(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import abraxas.conspiracy.csp as csp_module
    import abraxas.evidence.index as evidence_index
    import abraxas.memetic.claim_cluster as claim_cluster
    import abraxas.memetic.claim_extract as claim_extract
    import abraxas.memetic.claims_sources as claims_sources
    import abraxas.memetic.term_assign as term_assign
    import abraxas.runes.invoke as invoke_module

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["term_claims_run", "--run-id", "entry"])
    monkeypatch.setattr(
        claim_cluster, "cluster_claims", lambda *_args, **_kwargs: ([], _Metrics({}))
    )
    monkeypatch.setattr(
        claim_extract, "extract_claim_items_from_sources", lambda *_args, **_kwargs: []
    )
    monkeypatch.setattr(claims_sources, "load_sources_from_osh", lambda *_args, **_kwargs: ([], {}))
    monkeypatch.setattr(evidence_index, "evidence_by_term", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(term_assign, "build_term_token_index", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(term_assign, "assign_claim_to_terms", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(csp_module, "compute_claim_csp", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        invoke_module,
        "invoke_capability",
        lambda _capability, payload, **_kwargs: {"artifact": payload["artifact"]},
    )

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(Path(term_claims_run.__file__)), run_name="__main__")

    assert exc_info.value.code == 0
    output = tmp_path / "out" / "reports" / "term_claims_entry.json"
    assert json.loads(output.read_text(encoding="utf-8"))["run_id"] == "entry"
