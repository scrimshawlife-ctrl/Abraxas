#!/usr/bin/env bash
set -euo pipefail

SVG="docs/assets/architecture/abraxas-architecture-overview.svg"

if [[ ! -f "$SVG" ]]; then
  echo "Missing SVG artifact: $SVG" >&2
  exit 1
fi

if ! grep -q 'viewBox="' "$SVG"; then
  echo "SVG must include a viewBox for deterministic rendering: $SVG" >&2
  exit 1
fi

if grep -Eq 'width="100%"|height="100%"' "$SVG"; then
  echo "SVG must not use 100% width/height attributes: $SVG" >&2
  exit 1
fi

if grep -Eqi 'max-width' "$SVG"; then
  echo "SVG must not contain max-width inline style/CSS rules: $SVG" >&2
  exit 1
fi

echo "Architecture SVG validation passed: $SVG"
