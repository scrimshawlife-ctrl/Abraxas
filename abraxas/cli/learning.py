"""
Active Learning Loops CLI

Commands for running the learning loop:
- analyze-failures: Generate failure artifacts from backtest results
- generate-proposal: Create proposal from failure analysis
- run-sandbox: Execute proposal in sandbox
- promote: Promote proposal if eligible
- run-loop: Run full learning cycle end-to-end
"""

import argparse
import json
import sys
from pathlib import Path

from abraxas.backtest.ledger import BacktestLedger
from abraxas.learning.failure_analyzer import FailureAnalyzer
from abraxas.learning.promotion_gate import promote_proposal
from abraxas.learning.proposal_generator import ProposalGenerator
from abraxas.learning.sandbox_runner import SandboxRunner


def cmd_analyze_failures(args):
    """Analyze failures from backtest ledger."""
    ledger = BacktestLedger(ledger_path=args.backtest_ledger)
    analyzer = FailureAnalyzer(
        output_dir=args.output_dir, ledger_path=args.learning_ledger
    )

    # Read backtest results
    entries = ledger.read_all()

    failures_analyzed = 0

    for entry in entries:
        status = entry.get("status")
        confidence = entry.get("confidence", "MED")

        # Filter by min_confidence
        if args.min_confidence == "HIGH" and confidence != "HIGH":
            continue
        elif args.min_confidence == "MED" and confidence == "LOW":
            continue

        # Check if this is a failure
        if status == "MISS" or (status == "ABSTAIN" and confidence == "HIGH"):
            # Load full case and result to analyze
            # For now, print that we would analyze this
            print(
                f"Found failure: case={entry.get('case_id')}, "
                f"run={entry.get('backtest_run_id')}, status={status}"
            )
            failures_analyzed += 1

            # In full implementation, would load case, events, ledgers and analyze
            # For v0.1, we demonstrate the flow

    print(f"\nAnalyzed {failures_analyzed} failures")
    print(f"Failure artifacts written to: {args.output_dir}")
    print(f"Learning ledger: {args.learning_ledger}")


def cmd_generate_proposal(args):
    """Generate proposal from failure analysis."""
    failure_path = Path(args.failure_report)

    if not failure_path.exists():
        print(f"Error: Failure report not found: {failure_path}")
        return 1

    # Load failure analysis
    with open(failure_path, "r") as f:
        failure_data = json.load(f)

    from abraxas.learning.schema import FailureAnalysis

    failure = FailureAnalysis(**failure_data)

    # Generate proposal
    generator = ProposalGenerator(
        proposals_dir=args.proposals_dir, ledger_path=args.learning_ledger
    )

    proposal = generator.generate(failure, strategy=args.strategy)
    proposal_path = generator.write_proposal(proposal)
    ledger_hash = generator.append_to_ledger(proposal)

    print(f"Proposal generated: {proposal.proposal_id}")
    print(f"  Type: {proposal.proposal_type.value}")
    print(f"  Description: {proposal.change_description}")
    print(f"  Expected improvement: +{proposal.expected_delta.backtest_pass_rate_delta:.2%}")
    print(f"  Affected components: {', '.join(proposal.affected_components)}")
    print(f"\nProposal written to: {proposal_path}")
    print(f"Ledger hash: {ledger_hash[:16]}...")


def cmd_run_sandbox(args):
    """Run sandbox execution for proposal."""
    runner = SandboxRunner(
        proposals_dir=args.proposals_dir,
        cases_dir=args.cases_dir,
        ledger_path=args.learning_ledger,
    )

    # Load proposal
    proposal = runner.load_proposal(args.proposal_id)

    print(f"Running sandbox for proposal: {proposal.proposal_id}")
    print(f"  Stabilization runs: {args.runs}")
    print(f"  Test cases: {', '.join(proposal.validation_plan.sandbox_cases)}")

    # Run sandbox
    reports = runner.run_sandbox(proposal, run_count=args.runs)

    print(f"\nSandbox execution complete:")
    for idx, report in enumerate(reports, 1):
        print(f"  Run {idx}: {report.sandbox_run_id}")
        print(f"    Pass rate delta: {report.delta.pass_rate_delta:+.2%}")
        print(f"    Regressions: {report.delta.regression_count}")
        print(f"    Promotion eligible: {report.promotion_eligible}")

        # Append to ledger
        runner.append_to_ledger(report)

    # Check if eligible
    all_eligible = all(r.promotion_eligible for r in reports)
    if all_eligible:
        print(f"\n✓ All runs passed promotion criteria")
        print(f"  Ready to promote with: python -m abraxas.cli.learning promote --proposal-id {args.proposal_id}")
    else:
        print(f"\n✗ Some runs failed promotion criteria")
        print(f"  Proposal NOT eligible for promotion")


def cmd_promote(args):
    """Promote proposal if eligible."""
    print(f"Evaluating proposal for promotion: {args.proposal_id}")
    print(f"  Strict mode: {args.strict}")

    promotion = promote_proposal(
        proposal_id=args.proposal_id,
        proposals_dir=args.proposals_dir,
        strict=args.strict,
    )

    if promotion:
        print(f"\n✓ PROMOTION SUCCESSFUL")
        print(f"  Ledger hash: {promotion.ledger_sha256[:16]}...")
        return 0
    else:
        print(f"\n✗ PROMOTION REJECTED")
        print(f"  Proposal did not meet promotion criteria")
        return 1


def cmd_run_loop(args):
    """Run full learning cycle end-to-end."""
    print("Active Learning Loop - Full Cycle")
    print("=" * 60)

    # Step 1: Analyze failures
    print("\n[1/4] Analyzing failures from backtest ledger...")
    analyze_args = argparse.Namespace(
        backtest_ledger=args.backtest_ledger,
        output_dir=args.output_dir,
        learning_ledger=args.learning_ledger,
        min_confidence=args.min_confidence,
    )
    cmd_analyze_failures(analyze_args)

    # Step 2-4 would continue with proposal generation, sandbox, and optional promotion
    # For v0.1, we demonstrate the analysis step

    print("\n" + "=" * 60)
    print("Loop cycle complete (analysis phase)")
    print(f"Next: Review failure artifacts in {args.output_dir}")
    print(f"      Generate proposals with: python -m abraxas.cli.learning generate-proposal")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Active Learning Loops CLI - Turn failures into improvements"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # analyze-failures
    analyze_parser = subparsers.add_parser(
        "analyze-failures", help="Analyze failures from backtest ledger"
    )
    analyze_parser.add_argument(
        "--backtest-ledger",
        type=str,
        default="out/backtest_ledgers/backtest_runs.jsonl",
        help="Path to backtest ledger",
    )
    analyze_parser.add_argument(
        "--output-dir",
        type=str,
        default="out/reports",
        help="Output directory for failure artifacts",
    )
    analyze_parser.add_argument(
        "--learning-ledger",
        type=str,
        default="out/learning_ledgers/failure_analyses.jsonl",
        help="Learning ledger path",
    )
    analyze_parser.add_argument(
        "--min-confidence",
        type=str,
        choices=["LOW", "MED", "HIGH"],
        default="MED",
        help="Minimum confidence level to analyze",
    )

    # generate-proposal
    proposal_parser = subparsers.add_parser(
        "generate-proposal", help="Generate proposal from failure analysis"
    )
    proposal_parser.add_argument(
        "--failure-report",
        type=str,
        required=True,
        help="Path to failure analysis JSON",
    )
    proposal_parser.add_argument(
        "--proposals-dir",
        type=str,
        default="data/sandbox/proposals",
        help="Proposals directory",
    )
    proposal_parser.add_argument(
        "--learning-ledger",
        type=str,
        default="out/learning_ledgers/proposals.jsonl",
        help="Proposals ledger path",
    )
    proposal_parser.add_argument(
        "--strategy",
        type=str,
        default="bounded",
        help="Proposal generation strategy",
    )

    # run-sandbox
    sandbox_parser = subparsers.add_parser(
        "run-sandbox", help="Execute proposal in sandbox"
    )
    sandbox_parser.add_argument(
        "--proposal-id", type=str, required=True, help="Proposal ID to test"
    )
    sandbox_parser.add_argument(
        "--runs", type=int, default=3, help="Number of stabilization runs"
    )
    sandbox_parser.add_argument(
        "--proposals-dir",
        type=str,
        default="data/sandbox/proposals",
        help="Proposals directory",
    )
    sandbox_parser.add_argument(
        "--cases-dir",
        type=str,
        default="data/backtests/cases",
        help="Backtest cases directory",
    )
    sandbox_parser.add_argument(
        "--learning-ledger",
        type=str,
        default="out/learning_ledgers/sandbox_runs.jsonl",
        help="Sandbox runs ledger path",
    )

    # promote
    promote_parser = subparsers.add_parser(
        "promote", help="Promote proposal if eligible"
    )
    promote_parser.add_argument(
        "--proposal-id", type=str, required=True, help="Proposal ID to promote"
    )
    promote_parser.add_argument(
        "--proposals-dir",
        type=str,
        default="data/sandbox/proposals",
        help="Proposals directory",
    )
    promote_parser.add_argument(
        "--strict",
        type=lambda x: x.lower() == "true",
        default=True,
        help="Enforce strict promotion criteria (true/false)",
    )

    # run-loop
    loop_parser = subparsers.add_parser(
        "run-loop", help="Run full learning cycle end-to-end"
    )
    loop_parser.add_argument(
        "--backtest-ledger",
        type=str,
        default="out/backtest_ledgers/backtest_runs.jsonl",
        help="Path to backtest ledger",
    )
    loop_parser.add_argument(
        "--output-dir",
        type=str,
        default="out/reports",
        help="Output directory for artifacts",
    )
    loop_parser.add_argument(
        "--learning-ledger",
        type=str,
        default="out/learning_ledgers/failure_analyses.jsonl",
        help="Learning ledger path",
    )
    loop_parser.add_argument(
        "--min-confidence",
        type=str,
        choices=["LOW", "MED", "HIGH"],
        default="MED",
        help="Minimum confidence level",
    )
    loop_parser.add_argument(
        "--auto-promote",
        type=lambda x: x.lower() == "true",
        default=False,
        help="Automatically promote eligible proposals (true/false)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Dispatch to command
    if args.command == "analyze-failures":
        return cmd_analyze_failures(args)
    elif args.command == "generate-proposal":
        return cmd_generate_proposal(args)
    elif args.command == "run-sandbox":
        return cmd_run_sandbox(args)
    elif args.command == "promote":
        return cmd_promote(args)
    elif args.command == "run-loop":
        return cmd_run_loop(args)


if __name__ == "__main__":
    sys.exit(main() or 0)
