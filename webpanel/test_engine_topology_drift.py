"""The console's engine set must equal the registry's. Forever.

Without this, the card works today and silently diverges the first time an engine is added
or renamed. That is exactly how the console drifted from the architecture the first time --
and how the canonical manifest once listed paths that did not resolve, which is why
tests/test_engine_manifest_agreement.py exists.

This file exists because of a specific loss: a grouping change in engine_topology.py dropped
`aether` and `hyperlex` from `counts` (said 8 engines and 3 planned when there are 10 and 5)
and then dropped them from the TEMPLATE too, so they disappeared from the page. Both bugs
were internally consistent -- `counts == active + planned + other` still held. Only an
assertion against the raw rows catches a loss.
"""
from __future__ import annotations

from webpanel.engine_topology import build_engine_topology


class TestNoDrift:
    def test_console_set_equals_registry_set(self):
        from abraxas.yggdrasil.coordinator import YggdrasilCoordinator

        coord = YggdrasilCoordinator()
        try:
            coord.initialize()
        except Exception:
            pass
        registry_names = sorted(coord.rune_registry.list_engines())

        console_names = sorted(row["name"] for row in build_engine_topology()["engines"])

        assert console_names == registry_names, (
            "the console and the registry disagree about which engines exist.\n"
            f"  registry only: {sorted(set(registry_names) - set(console_names))}\n"
            f"  console only:  {sorted(set(console_names) - set(registry_names))}\n"
            "Fix the console view. Do NOT edit the registry to match -- the registry is the "
            "source of truth."
        )

    def test_every_engine_has_a_state(self):
        """No row may render a blank or unknown state -- that would be indistinguishable
        from a rendering bug."""
        for row in build_engine_topology()["engines"]:
            assert row["state"] in ("active", "planned", "unavailable"), row

    def test_planned_engines_are_never_available(self):
        """The manifest rule, enforced on every engine rather than only on aether."""
        for row in build_engine_topology()["engines"]:
            if row["state"] == "planned":
                assert row["available"] is False, f"{row['name']} is planned but marked available"

    def test_model_requirement_is_always_one_of_three_values(self):
        for row in build_engine_topology()["engines"]:
            assert row["model_requirement"] in ("yes", "no", "unknown"), row

    def test_no_engine_is_marked_available_and_planned_at_once(self):
        """A contradiction the card must never render."""
        for row in build_engine_topology()["engines"]:
            assert not (row["available"] and row["state"] == "planned"), row
