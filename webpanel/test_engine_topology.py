"""The console's engine view must read the live registry, not a second hardcoded list.

Why this file exists: the registry's own docstring records that every engine was once
stamped REGISTERED, which made `aether` (zero files in this repo, deliberately planned)
indistinguishable from `athanor` (a working provider). The console showed NOTHING about
engines -- `grep -ci engine webpanel/operator_console.py` returned 0 -- while the registry
held the full topology. These tests exist so the view that IS added cannot reintroduce that
collapse, and cannot drift from the registry later.
"""
from __future__ import annotations

import pytest

from webpanel.engine_topology import build_engine_topology


class TestTopologyReadsTheRegistry:
    def test_returns_all_registered_engines(self):
        topo = build_engine_topology()
        names = {row["name"] for row in topo["engines"]}
        # the coordinator and the test double live in the registry too -- they must not be
        # silently dropped, they must be *classified* (see test_non_engines_are_marked)
        assert "athanor" in names
        assert "oracle" in names
        assert "aether" in names
        assert len(names) >= 10, f"expected the full registry, got {sorted(names)}"

    def test_planned_is_distinct_from_active(self):
        """The counterfactual: if these two collapse, the card reintroduces the exact bug
        the registry was built to prevent."""
        topo = build_engine_topology()
        by_name = {row["name"]: row for row in topo["engines"]}
        assert by_name["aether"]["state"] == "planned"
        assert by_name["athanor"]["state"] == "active"
        assert by_name["aether"]["state"] != by_name["athanor"]["state"]

    def test_non_engines_are_marked_as_such(self):
        """`yggdrasil` is the coordinator and `mock` is a test double -- neither is an
        engine to be started, and neither may be counted as one."""
        topo = build_engine_topology()
        by_name = {row["name"]: row for row in topo["engines"]}
        assert by_name["yggdrasil"]["kind"] == "coordinator"
        assert by_name["mock"]["kind"] == "test_double"
        assert topo["counts"]["engines"] < len(topo["engines"])

    def test_aether_is_never_presented_as_available(self):
        """Directly quotes the manifest rule the registry encodes."""
        topo = build_engine_topology()
        by_name = {row["name"]: row for row in topo["engines"]}
        assert by_name["aether"]["available"] is False


class TestCountsAreConsistent:
    def test_counts_add_up(self):
        topo = build_engine_topology()
        c = topo["counts"]
        assert c["engines"] == c["active"] + c["planned"] + c["other"]
        assert c["total"] == len(topo["engines"])
