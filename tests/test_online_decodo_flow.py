from __future__ import annotations

import json
from types import SimpleNamespace

from abx.online_sourcing import route_online_sources
from abx.online_resolver import execute_task_routing, resolve_routing_to_urls


def test_route_online_sources_builds_decodo_request_envelope() -> None:
    routing = route_online_sources(
        term="abraxas",
        query="abraxas resonance",
        known_urls=[
            "https://example.com/a",
            "https://example.com/a",
            "https://news.example.org/b",
        ],
        caps={"decodo_available": True, "online_allowed": True},
    )

    assert routing["provider"] == "decodo"
    req = routing["request"]
    assert req["candidate_urls"] == ["https://example.com/a", "https://news.example.org/b"]
    assert req["domains"] == ["example.com", "news.example.org"]
    assert req["max_results"] == 12
    assert req["capability"] == {"online_allowed": True, "decodo_available": True}
    assert routing["transport_outcome"] == "executed_live"
    assert routing["reason_code"] == "decodo_live_path"


def test_route_online_sources_reports_policy_block_when_online_disabled() -> None:
    routing = route_online_sources(
        term="abraxas",
        query="abraxas resonance",
        known_urls=["https://example.com/a"],
        caps={"online_allowed": False, "decodo_available": False},
    )

    assert routing["provider"] == "none"
    assert routing["transport_outcome"] == "blocked_policy"
    assert routing["error"] == "online_blocked_by_policy"
    assert routing["reason_code"] == "online_policy_blocked"


def test_route_online_sources_honors_online_policy_even_if_decodo_available() -> None:
    routing = route_online_sources(
        term="abraxas",
        query="abraxas resonance",
        known_urls=["https://example.com/a"],
        caps={"online_allowed": False, "decodo_available": True},
    )

    assert routing["provider"] == "none"
    assert routing["transport_outcome"] == "blocked_policy"
    assert routing["reason_code"] == "online_policy_blocked"


def test_resolve_routing_to_urls_decodo_uses_candidates_and_domains() -> None:
    provider, urls, meta = resolve_routing_to_urls(
        {
            "provider": "decodo",
            "request": {
                "candidate_urls": ["https://example.com/a"],
                "domains": ["example.com", "alt.example.com"],
                "max_results": 3,
                "capability": {"online_allowed": True, "decodo_available": True},
            },
            "transport_outcome": "executed_live",
        }
    )

    assert provider == "decodo"
    assert urls == [
        "https://example.com/a",
        "https://example.com",
        "https://alt.example.com",
    ]
    assert "request" in meta
    assert meta["transport_outcome"] == "executed_live"
    assert meta["reason_code"] == "decodo_live_path"


def test_resolve_routing_to_urls_decodo_filters_non_http_and_invalid_max_results() -> None:
    provider, urls, _ = resolve_routing_to_urls(
        {
            "provider": "decodo",
            "request": {
                "candidate_urls": ["file:///etc/passwd", "https://ok.example/path"],
                "domains": ["site.example"],
                "max_results": "invalid",
                "capability": {"online_allowed": True, "decodo_available": True},
            },
        }
    )

    assert provider == "decodo"
    assert urls == ["https://ok.example/path", "https://site.example"]


def test_resolve_routing_to_urls_decodo_blocked_by_capability() -> None:
    provider, urls, meta = resolve_routing_to_urls(
        {
            "provider": "decodo",
            "request": {
                "candidate_urls": ["https://ok.example/path"],
                "capability": {"online_allowed": True, "decodo_available": False},
            },
        }
    )

    assert provider == "decodo"
    assert urls == []
    assert meta["transport_outcome"] == "blocked_policy"
    assert meta["reason_code"] == "decodo_unavailable_or_policy_blocked"


def test_resolve_routing_to_urls_fallback_reason_codes() -> None:
    provider, urls, meta = resolve_routing_to_urls(
        {
            "provider": "direct_http",
            "results": [{"url": "https://example.com/a"}],
            "transport_outcome": "executed_fallback",
            "reason_code": "fallback_direct_http",
        }
    )

    assert provider == "direct_http"
    assert urls == ["https://example.com/a"]
    assert meta["transport_outcome"] == "executed_fallback"
    assert meta["reason_code"] == "fallback_direct_http"


def test_execute_task_routing_decodo_emits_anchors(tmp_path, monkeypatch) -> None:
    anchor_ledger = tmp_path / "anchor_ledger.jsonl"
    evidence_ledger = tmp_path / "evidence_graph.jsonl"

    evidence_ledger.write_text(
        json.dumps(
            {
                "kind": "claim_added",
                "claim_id": "claim-1",
                "text": "Abraxas signal strengthening",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    def fake_http_get(url: str, timeout: int = 14, headers: dict | None = None):
        html = "<html><head><title>Abraxas Signal Note</title></head><body>Signal structure update.</body></html>"
        return html, {"content-type": "text/html"}

    monkeypatch.setattr("abx.online_resolver._http_get", fake_http_get)
    monkeypatch.setattr(
        "abx.online_resolver.classify_relation",
        lambda **kwargs: SimpleNamespace(relation="SUPPORTS", confidence=0.9, rationale="keyword overlap"),
    )

    result = execute_task_routing(
        run_id="run-1",
        task={"task_id": "task-1", "claim_id": "claim-1", "term": "Abraxas"},
        routing={
            "provider": "decodo",
            "request": {
                "candidate_urls": ["https://example.com/a"],
                "domains": [],
                "max_results": 5,
                "capability": {"online_allowed": True, "decodo_available": True},
            },
            "transport_outcome": "executed_live",
        },
        anchor_ledger=str(anchor_ledger),
        evidence_graph_ledger=str(evidence_ledger),
        max_fetch=2,
    )

    assert result["status"] == "OK"
    assert result["provider"] == "decodo"
    assert result["transport_outcome"] == "executed_live"
    assert len(result["created_anchors"]) == 1

    rows = [json.loads(line) for line in anchor_ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1
    assert rows[0]["provider"] == "decodo"


def test_execute_task_routing_returns_noop_when_no_urls(tmp_path) -> None:
    anchor_ledger = tmp_path / "anchor_ledger.jsonl"
    evidence_ledger = tmp_path / "evidence_graph.jsonl"
    evidence_ledger.write_text("", encoding="utf-8")

    result = execute_task_routing(
        run_id="run-2",
        task={"task_id": "task-2", "claim_id": "claim-2", "term": "Abraxas"},
        routing={"provider": "decodo", "request": {"candidate_urls": [], "domains": []}},
        anchor_ledger=str(anchor_ledger),
        evidence_graph_ledger=str(evidence_ledger),
    )

    assert result["status"] == "NOOP"
    assert result["transport_outcome"] == "blocked_policy"
    assert result["created_anchors"] == []


def test_resolve_routing_to_urls_decodo_blocks_when_capability_missing() -> None:
    provider, urls, meta = resolve_routing_to_urls(
        {
            "provider": "decodo",
            "request": {
                "candidate_urls": ["https://ok.example/path"],
                "domains": [],
            },
        }
    )
    assert provider == "decodo"
    assert urls == []
    assert meta["transport_outcome"] == "blocked_policy"
    assert meta["reason_code"] == "decodo_capability_missing"
