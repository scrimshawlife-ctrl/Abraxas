#!/usr/bin/env bash
set -euo pipefail

SRC="docs/assets/architecture/abraxas-architecture-overview.mmd"
SVG_OUT="docs/assets/architecture/abraxas-architecture-overview.svg"
PNG_OUT="docs/assets/architecture/abraxas-architecture-overview.png"

if ! command -v npx >/dev/null 2>&1; then
  echo "npx is required to export Mermaid diagrams." >&2
  exit 2
fi

npx @mermaid-js/mermaid-cli -i "$SRC" -o "$SVG_OUT"

if [[ "${EXPORT_PNG:-0}" == "1" ]]; then
  npx @mermaid-js/mermaid-cli -i "$SRC" -o "$PNG_OUT"
fi

echo "Exported: $SVG_OUT"
if [[ "${EXPORT_PNG:-0}" == "1" ]]; then
  echo "Exported: $PNG_OUT"
fi
