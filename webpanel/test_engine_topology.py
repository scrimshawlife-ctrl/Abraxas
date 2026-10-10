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

    def test_counts_match_the_rows_they_summarise(self):
        """`counts == active + planned + other` is internally consistent and can still be
        WRONG. It passed at 8 engines / 3 planned while there were 10 and 5, because the
        grouping had dropped the two engines whose model requirement is unknown.

        This asserts against the actual rows, which is the only thing that catches a loss.
        """
        topo = build_engine_topology()
        c = topo["counts"]
        engine_rows = [r for r in topo["engines"] if r["kind"] == "engine"]
        assert c["engines"] == len(engine_rows), (
            f"counts says {c['engines']} engines, the rows contain {len(engine_rows)}"
        )
        assert c["active"] == len([r for r in engine_rows if r["state"] == "active"])
        assert c["planned"] == len([r for r in engine_rows if r["state"] == "planned"])

    def test_every_engine_row_appears_in_exactly_one_model_group(self):
        """A row cannot vanish between the groups. This is what the 8-vs-10 loss looked like."""
        topo = build_engine_topology()
        grouped = (
            [r["name"] for r in topo["needs_model"]]
            + [r["name"] for r in topo["no_model"]]
            + [r["name"] for r in topo["model_unknown"]]
        )
        engine_names = [r["name"] for r in topo["engines"] if r["kind"] == "engine"]
        assert sorted(grouped) == sorted(engine_names), (
            f"groups hold {sorted(grouped)}, engines are {sorted(engine_names)}"
        )
        assert len(grouped) == len(set(grouped)), "a row appears in two groups"

    def test_an_unimplemented_engine_is_unknown_not_modelled(self):
        """aether is PLANNED with no implementation. Claiming it needs a model would be an
        assertion about code that does not exist."""
        topo = build_engine_topology()
        by_name = {r["name"]: r for r in topo["engines"]}
        assert by_name["aether"]["model_requirement"] == "unknown"
