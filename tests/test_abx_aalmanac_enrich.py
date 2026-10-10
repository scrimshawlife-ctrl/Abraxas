from __future__ import annotations

import json
import runpy
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

import abx.aalmanac_enrich as aalmanac_enrich


def _write_jsonl(path: Path, rows: list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_jsonl_helpers_and_utc_timestamp(tmp_path: Path) -> None:
    assert aalmanac_enrich._utc_now_iso().endswith("+00:00")
    assert aalmanac_enrich._read_jsonl("") == []
    assert aalmanac_enrich._read_jsonl(str(tmp_path / "missing.jsonl")) == []

    source = tmp_path / "mixed.jsonl"
    source.write_text(
        '\n{"valid": 1}\nnot json\n["not", "an", "object"]\n{"unicode": "café"}\n',
        encoding="utf-8",
    )
    assert aalmanac_enrich._read_jsonl(str(source)) == [
        {"valid": 1},
        {"unicode": "café"},
    ]

    appended = tmp_path / "nested" / "events.jsonl"
    aalmanac_enrich._append_jsonl(str(appended), {"message": "café"})
    assert appended.read_text(encoding="utf-8") == '{"message": "café"}\n'


def test_domain_group_classifies_known_sources_and_fallbacks() -> None:
    assert aalmanac_enrich._domain_group("HTTPS://X.COM/profile") == "social"
    assert aalmanac_enrich._domain_group("https://nature.com/article") == "reference"
    assert aalmanac_enrich._domain_group("https://www.reuters.com/story") == "mainstream"
    assert aalmanac_enrich._domain_group("") == "none"
    assert aalmanac_enrich._domain_group("https://unknown.example") == "other"


def test_tokenize_and_find_concordance_handle_empty_text_and_caps() -> None:
    assert aalmanac_enrich._tokenize("I am 7 cats, e-mail Python's XY") == [
        "am",
        "cats",
        "e-mail",
        "python's",
        "xy",
    ]
    assert aalmanac_enrich._tokenize("") == []

    assert aalmanac_enrich._find_concordance("", "some text") == []
    assert aalmanac_enrich._find_concordance("term", "") == []
    assert aalmanac_enrich._find_concordance("term", "a term here", max_snips=0) == []
    assert aalmanac_enrich._find_concordance("missing", "some text") == []
    snippets = aalmanac_enrich._find_concordance(
        "alpha", "Alpha\nthen ALPHA final", window=2, max_snips=1
    )
    assert snippets == ["Alpha t"]
    assert "\n" not in snippets[0]
    assert (
        len(aalmanac_enrich._find_concordance("alpha", "Alpha and alpha", window=8, max_snips=5))
        == 2
    )


def test_co_terms_and_compressed_definition_cover_empty_and_ranked_context() -> None:
    assert aalmanac_enrich._co_terms("", ["alpha"]) == Counter()
    assert aalmanac_enrich._co_terms("alpha", []) == Counter()
    assert aalmanac_enrich._co_terms("alpha beta", ["alpha", "signal"]) == Counter()
    assert aalmanac_enrich._co_terms(
        "alpha", ["alpha", "the", "signal", "alpha", "evidence", "of", "alpha"], span=1
    ) == Counter({"the": 1, "signal": 1, "evidence": 1})

    assert aalmanac_enrich._compress_definition("alpha", Counter(), Counter()) == (
        "alpha: insufficient context yet (await more anchors/runs)."
    )
    assert (
        aalmanac_enrich._compress_definition(
            "alpha",
            Counter({"signal": 5, "evidence": 3}),
            Counter({"none": 9, "social": 4, "reference": 3, "mainstream": 2}),
        )
        == "alpha: contexts: signal, evidence | domains: social, reference"
    )


def test_main_filters_inputs_caps_terms_and_emits_enrichment_and_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    canon = tmp_path / "input" / "aalmanac.jsonl"
    _write_jsonl(
        canon,
        [
            {"kind": "aalmanac_entry", "tier": "CANON", "term": "alpha"},
            {"kind": "aalmanac_entry", "tier": "CANON", "term": "beta"},
            {"kind": "other", "tier": "CANON", "term": "ignored-kind"},
            {"kind": "aalmanac_entry", "tier": "DRAFT", "term": "ignored-tier"},
            {"kind": "aalmanac_entry", "tier": "CANON"},
        ],
    )
    oracle = tmp_path / "input" / "oracle.jsonl"
    _write_jsonl(
        oracle,
        [
            {
                "kind": "oracle_run",
                "oracle_id": "beta-run",
                "text": "Beta shares a signal and context.",
            },
            {"kind": "oracle_run", "oracle_id": "empty", "text": ""},
            {"kind": "oracle_run", "oracle_id": "no-match", "text": "unrelated words only"},
        ],
    )
    anchors = tmp_path / "input" / "anchors.jsonl"
    _write_jsonl(
        anchors,
        [
            {},
            {"title": "unrelated title", "content_hint": "nothing relevant"},
            {
                "title": "beta evidence",
                "content_hint": "beta provides an anchor signal",
                "domain": "https://www.reuters.com/story",
                "anchor_id": "anchor-news",
            },
            {
                "title": "beta reference",
                "content_hint": "beta in a study",
                "domain": "https://nature.com/study",
                "anchor_id": "anchor-reference",
            },
        ],
    )
    events = tmp_path / "out" / "ledger" / "events.jsonl"
    report = tmp_path / "out" / "reports" / "state.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "aalmanac_enrich",
            "--run-id",
            "test-run",
            "--aalmanac",
            str(canon),
            "--oracle-ledger",
            str(oracle),
            "--anchor-ledger",
            str(anchors),
            "--events-ledger",
            str(events),
            "--out",
            str(report),
            "--max-terms",
            "1",
            "--max-snips",
            "2",
        ],
    )

    assert aalmanac_enrich.main() == 0

    state = json.loads(report.read_text(encoding="utf-8"))
    assert state["version"] == "aalmanac_state.v0.1"
    assert state["run_id"] == "test-run"
    assert state["n_terms"] == 1
    item = state["items"][0]
    assert item["term"] == "beta"
    assert item["run_id"] == "test-run"
    assert "contexts:" in item["definition"]
    assert set(item["domain_tags"]) == {"mainstream", "reference"}
    assert len(item["usage"]) == 2
    assert item["usage"][0]["source_kind"] == "oracle"
    assert item["usage"][1]["source_kind"] == "anchor"
    assert item["provenance"]["sources_sampled"] == 3
    assert item["provenance"]["oracle_window"] == 200
    assert item["provenance"]["anchor_window"] == 500

    event = json.loads(events.read_text(encoding="utf-8").splitlines()[0])
    assert event["kind"] == "aalmanac_enriched"
    assert event["term"] == "beta"
    assert event["notes"].startswith("Deterministic enrichment")
    assert capsys.readouterr().out == f"[AALMANAC_STATE] wrote: {report} terms=1\n"


def test_module_entrypoint_uses_default_ledgers_and_default_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["aalmanac_enrich", "--run-id", "empty-run"])

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(aalmanac_enrich.__file__, run_name="__main__")

    assert exc_info.value.code == 0
    reports = list((tmp_path / "out" / "reports").glob("aalmanac_state_*.json"))
    assert len(reports) == 1
    state = json.loads(reports[0].read_text(encoding="utf-8"))
    assert state["run_id"] == "empty-run"
    assert state["n_terms"] == 0
    assert state["items"] == []
    assert capsys.readouterr().out == (
        f"[AALMANAC_STATE] wrote: out/reports/{reports[0].name} terms=0\n"
    )
