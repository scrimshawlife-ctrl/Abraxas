from __future__ import annotations

from scripts.build_stub_taxonomy_artifact import build_taxonomy, classify_stub


def test_classify_stub_categories() -> None:
    assert classify_stub({"stub_type": "interface", "marker": "raise NotImplementedError"}) == "intentional_abstract"
    assert classify_stub(
        {
            "stub_type": "not_implemented",
            "file": "abraxas/detectors/shadow/types.py",
            "marker": 'raise NotImplementedError("Subclasses must implement detect()")',
        }
    ) == "intentional_abstract"
    assert classify_stub(
        {
            "stub_type": "not_implemented",
            "file": "abraxas/narratives/templates.py",
            "marker": 'raise NotImplementedError("Subclasses must implement render()")',
        }
    ) == "intentional_abstract"
    assert classify_stub(
        {
            "stub_type": "operator",
            "file": "abraxas/runes/operators/source_discover.py",
            "marker": 'raise NotImplementedError("SOURCE_DISCOVER requires payload")',
        }
    ) == "policy_block"
    assert classify_stub(
        {
            "stub_type": "operator",
            "file": "abraxas/runes/operators/rfa.py",
            "marker": "strict_execution: If True, raises NotImplementedError for unimplemented operator",
        }
    ) == "implementation_gap"


def test_build_taxonomy_counts() -> None:
    artifact = build_taxonomy(
        {
            "stubs": [
                {"stub_type": "interface", "file": "abraxas/sources/adapters/base.py", "marker": "raise NotImplementedError"},
                {
                    "stub_type": "operator",
                    "file": "abraxas/runes/operators/source_discover.py",
                    "marker": 'raise NotImplementedError("SOURCE_DISCOVER requires payload")',
                },
                {
                    "stub_type": "operator",
                    "file": "abraxas/runes/operators/rfa.py",
                    "marker": "strict_execution: If True, raises NotImplementedError for unimplemented operator",
                },
            ]
        }
    )

    assert artifact["n_stubs"] == 3
    assert artifact["gap_summary"]["intentional_abstract"] == 1
    assert artifact["gap_summary"]["policy_block"] == 1
    assert artifact["gap_summary"]["implementation_gap"] == 1
