from __future__ import annotations

from scripts.run_governance_lint import run_lint


def test_governance_lint_passes() -> None:
    report = run_lint()
    assert report["ok"] is True
    assert report["errors"] == []


def test_governance_lint_discovers_only_classified_heavy_paths() -> None:
    report = run_lint()
    discovered = set(report["discovered_heavy_paths"])
    classified = set(report["classified_heavy_paths"])
    assert discovered.issubset(classified)


def test_governance_lint_discovers_only_classified_heavy_commands() -> None:
    report = run_lint()
    discovered_cli = set(report["discovered_heavy_cli_subcommands"])
    classified_cli = set(report["classified_cli_subcommands"])
    assert discovered_cli.issubset(classified_cli)

    discovered_make = set(report["discovered_heavy_make_targets"])
    classified_make = set(report["classified_make_targets"])
    assert discovered_make.issubset(classified_make)
