#!/usr/bin/env bash
# Platform-independent drift check for the tracked architecture SVG.
#
# Why not just regenerate and `git diff`? Because Mermaid lays text out with the
# host's fonts, so the same pinned mermaid-cli produces different width/viewBox
# values on macOS than on an Ubuntu runner. A byte-exact comparison therefore fails
# on every CI run for reasons that have nothing to do with drift -- an instrument
# that reports the wrong thing.
#
# Instead the artifact carries a sha256 stamp of the Mermaid source it was generated
# from (written by scripts/export_architecture_svg.sh), and this compares that stamp
# against the real hash of the .mmd on disk. It catches the failure that actually
# matters -- "the source was edited and the SVG was not regenerated" -- on any
# platform, without rendering anything.
set -euo pipefail

SRC="docs/assets/architecture/abraxas-architecture-overview.mmd"
SVG="docs/assets/architecture/abraxas-architecture-overview.svg"

for f in "$SRC" "$SVG"; do
  if [[ ! -f "$f" ]]; then
    echo "Missing required file: $f" >&2
    exit 2
  fi
done

read -r expected actual < <(python3 - "$SRC" "$SVG" <<'PY'
import hashlib
import re
import sys
from pathlib import Path

src = Path(sys.argv[1])
svg = Path(sys.argv[2])

digest = hashlib.sha256(src.read_bytes()).hexdigest()
stamp = re.search(r"source-sha256:\s*([0-9a-f]{64})", svg.read_text(encoding="utf-8"))
print(digest, stamp.group(1) if stamp else "-")
PY
)

if [[ "$actual" == "-" ]]; then
  echo "The SVG carries no source-sha256 stamp, so drift cannot be detected." >&2
  echo "Regenerate it: scripts/export_architecture_svg.sh" >&2
  exit 1
fi

if [[ "$actual" != "$expected" ]]; then
  echo "DRIFT: the Mermaid source changed but the SVG was not regenerated." >&2
  echo "  $SRC sha256: $expected" >&2
  echo "  $SVG stamp:  $actual" >&2
  echo "  Fix: scripts/export_architecture_svg.sh" >&2
  exit 1
fi

echo "In sync: the SVG stamp matches $SRC ($expected)."
