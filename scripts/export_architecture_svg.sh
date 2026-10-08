#!/usr/bin/env bash
set -euo pipefail

SRC="docs/assets/architecture/abraxas-architecture-overview.mmd"
SVG_OUT="docs/assets/architecture/abraxas-architecture-overview.svg"
PNG_OUT="docs/assets/architecture/abraxas-architecture-overview.png"
CONFIG="docs/assets/architecture/mermaid-export-config.json"

# Chromium on GitHub's ubuntu runners cannot use its sandbox -- unprivileged user
# namespaces are restricted, and puppeteer dies with "No usable sandbox!" before
# rendering. Hand it a config that passes --no-sandbox. Left unset locally, where the
# sandbox works. Expanded unquoted at the call sites on purpose, so an empty value
# vanishes instead of becoming an empty argument; the path contains no spaces.
PUPPETEER_OPT=""
if [[ -n "${CI:-}" ]]; then
  PUPPETEER_OPT="-p docs/assets/architecture/puppeteer-config.json"
fi

if ! command -v npx >/dev/null 2>&1; then
  echo "npx is required to export Mermaid diagrams." >&2
  exit 2
fi

if [[ ! -f "$SRC" ]]; then
  echo "Missing Mermaid source: $SRC" >&2
  exit 2
fi

if [[ ! -f "$CONFIG" ]]; then
  echo "Missing Mermaid config: $CONFIG" >&2
  exit 2
fi

TMP_SVG="$(mktemp "${TMPDIR:-/tmp}/abraxas-architecture.XXXXXX.svg")"
cleanup() {
  rm -f "$TMP_SVG"
}
trap cleanup EXIT

npx --yes @mermaid-js/mermaid-cli@12.0.0 $PUPPETEER_OPT -i "$SRC" -o "$TMP_SVG" -c "$CONFIG"

python - "$TMP_SVG" <<'PY'
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
root = ET.fromstring(text)

def strip_max_width(style: str | None) -> str | None:
    if style is None:
        return None
    cleaned = re.sub(r"(?:^|;)\s*max-width\s*:[^;]+", "", style)
    cleaned = re.sub(r";;+", ";", cleaned).strip(" ;")
    return cleaned or None

def strip_max_width_from_css(css: str) -> str:
    # Remove max-width rules from CSS - more robust regex
    cleaned = re.sub(r"\s*max-width\s*:[^;}]+;?", "", css)
    # Clean up any double semicolons or semicolon before }
    cleaned = re.sub(r";\s*;", ";", cleaned)
    cleaned = re.sub(r";\s*}", "}", cleaned)
    cleaned = re.sub(r"\{\s*;", "{", cleaned)
    return cleaned

def numeric_dimension(value: str | None) -> float | None:
    if value is None:
        return None
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*(?:px)?\s*", value)
    if not match:
        return None
    return float(match.group(1))

def fmt(value: float) -> str:
    rounded = round(value)
    if abs(value - rounded) < 1e-6:
        return str(int(rounded))
    return f"{value:.3f}".rstrip("0").rstrip(".")

style = strip_max_width(root.get("style"))
if style is None:
    root.attrib.pop("style", None)
else:
    root.set("style", style)

# Also strip max-width from <style> tag content
for style_elem in root.iter():
    if style_elem.tag.endswith("style") and style_elem.text:
        style_elem.text = strip_max_width_from_css(style_elem.text)

# Also strip max-width from all style attributes on any element
for elem in root.iter():
    if "style" in elem.attrib:
        cleaned_style = strip_max_width(elem.attrib["style"])
        if cleaned_style is None:
            elem.attrib.pop("style", None)
        else:
            elem.set("style", cleaned_style)

view_box = root.get("viewBox")
if view_box:
    parts = view_box.replace(",", " ").split()
    if len(parts) == 4:
        _, _, width, height = map(float, parts)
        root.set("width", fmt(width))
        root.set("height", fmt(height))
else:
    width = numeric_dimension(root.get("width"))
    height = numeric_dimension(root.get("height"))
    if width is not None and height is not None:
        root.set("viewBox", f"0 0 {fmt(width)} {fmt(height)}")
        root.set("width", fmt(width))
        root.set("height", fmt(height))

path.write_text(ET.tostring(root, encoding="unicode"), encoding="utf-8")
PY

python - "$TMP_SVG" "$SRC" <<'PY'
import hashlib
import re
import sys
from pathlib import Path

svg_path = Path(sys.argv[1])
src_path = Path(sys.argv[2])
digest = hashlib.sha256(src_path.read_bytes()).hexdigest()

header = (
    "<!-- ABRAXAS GENERATED ARTIFACT: derived from "
    f"{src_path.as_posix()} via scripts/export_architecture_svg.sh "
    f"source-sha256: {digest} -->"
)

text = svg_path.read_text(encoding="utf-8")
# Strip any previous stamp rather than only adding one when absent, so regenerating
# after a source edit refreshes the hash instead of leaving a stale one behind.
text = re.sub(r"^<!-- ABRAXAS GENERATED ARTIFACT[^\n]*-->\n", "", text, count=1)
svg_path.write_text(header + "\n" + text, encoding="utf-8")
print(header)
PY

mv "$TMP_SVG" "$SVG_OUT"

if [[ "${EXPORT_PNG:-0}" == "1" ]]; then
  PNG_WIDTH="$(python - "$SVG_OUT" <<'PY'
import sys
import xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
width = root.get("width", "")
print(width.split("px", 1)[0] if width else "")
PY
)"

  if [[ -n "$PNG_WIDTH" ]]; then
    npx --yes @mermaid-js/mermaid-cli@12.0.0 $PUPPETEER_OPT -i "$SRC" -o "$PNG_OUT" -c "$CONFIG" -w "$PNG_WIDTH"
  else
    npx --yes @mermaid-js/mermaid-cli@12.0.0 $PUPPETEER_OPT -i "$SRC" -o "$PNG_OUT" -c "$CONFIG"
  fi
fi

echo "Exported: $SVG_OUT"
if [[ "${EXPORT_PNG:-0}" == "1" ]]; then
  echo "Exported: $PNG_OUT"
fi
