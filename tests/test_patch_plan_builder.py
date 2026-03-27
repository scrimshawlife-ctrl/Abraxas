from server.abraxas.upgrade_spine.utils import build_patch_plan


def test_build_patch_plan_is_deterministic_for_same_payload():
    ops = [{"op": "apply_rent_ruleset_update", "issues": ["manifest_missing"]}]
    notes = ["rent_report_reference"]

    one = build_patch_plan(operations=ops, notes=notes, metadata={"source": "rent"})
    two = build_patch_plan(operations=ops, notes=notes, metadata={"source": "rent"})

    assert one == two
    assert one["plan_id"] == two["plan_id"]
    assert one["operations"][0]["op"] == "apply_rent_ruleset_update"
