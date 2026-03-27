#!/usr/bin/env bash
set -euo pipefail

python3 tools/acceptance/run_acceptance_suite.py --output out/acceptance
