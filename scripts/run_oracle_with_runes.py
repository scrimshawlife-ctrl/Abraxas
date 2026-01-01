#!/usr/bin/env python3
"""Run oracle with ABX-Runes integration from JSON input files.

Usage:
    python scripts/run_oracle_with_runes.py --input input.json
    python scripts/run_oracle_with_runes.py --input input.json --state state.json --context context.json

JSON Format Examples:

input.json:
{
  "intent": "daily_oracle",
  "v": 1
}

state.json (optional):
{
  "arousal": 0.5,
  "coherence": 0.7,
  "openness": 0.8,
  "receptivity": 0.6,
  "stability": 0.5
}

context.json (optional):
{
  "time_of_day": "morning",
  "recent_history_count": 5
}
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from abx.core.pipeline import run_oracle
from abx.util.jsonutil import dumps_stable


def load_json_file(path: str) -> dict:
    """Load JSON from file."""
    with open(path) as f:
        return json.load(f)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run Abraxas Oracle with ABX-Runes integration"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to input JSON file (required)",
    )
    parser.add_argument(
        "--state",
        help="Path to state_vector JSON file (optional)",
    )
    parser.add_argument(
        "--context",
        help="Path to context JSON file (optional)",
    )
    parser.add_argument(
        "--depth",
        choices=["grounding", "shallow", "deep"],
        default="deep",
        help="Requested depth level (default: deep)",
    )
    parser.add_argument(
        "--anchor",
        help="Semantic anchor string (default: uses input intent)",
    )
    parser.add_argument(
        "--history",
        help="Path to JSON file with outputs_history array (optional)",
    )

    args = parser.parse_args()

    # Load input
    input_obj = load_json_file(args.input)

    # Load optional parameters
    state_vector = load_json_file(args.state) if args.state else None
    context = load_json_file(args.context) if args.context else None
    outputs_history = load_json_file(args.history) if args.history else None

    # Run oracle
    output = run_oracle(
        input_obj=input_obj,
        state_vector=state_vector,
        context=context,
        requested_depth=args.depth,
        anchor=args.anchor,
        outputs_history=outputs_history,
    )

    # Print output as pretty JSON
    print(dumps_stable(output))


if __name__ == "__main__":
    main()
