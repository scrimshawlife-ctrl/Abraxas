from __future__ import annotations

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = ROOT / "docs" / "assets" / "architecture" / "abraxas-architecture-overview.svg"


def _parse_dimension(value: str | None) -> float | None:
    if value is None:
        return None
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*(?:px)?\s*", value)
    if not match:
        return None
    return float(match.group(1))


def main() -> int:
    if not SVG_PATH.exists():
        print(f"architecture-svg-bounds-check: FAIL (missing file: {SVG_PATH.relative_to(ROOT)})")
        return 1

    root = ET.parse(SVG_PATH).getroot()
    width = _parse_dimension(root.get("width"))
    height = _parse_dimension(root.get("height"))
    view_box = root.get("viewBox", "")

    if not view_box:
        print("architecture-svg-bounds-check: FAIL (missing viewBox)")
        return 1

    parts = view_box.replace(",", " ").split()
    if len(parts) != 4:
        print(f"architecture-svg-bounds-check: FAIL (invalid viewBox: {view_box})")
        return 1

    try:
        _, _, vb_width, vb_height = [float(x) for x in parts]
    except ValueError:
        print(f"architecture-svg-bounds-check: FAIL (non-numeric viewBox: {view_box})")
        return 1

    if vb_width <= 0 or vb_height <= 0:
        print("architecture-svg-bounds-check: FAIL (viewBox must be positive)")
        return 1

    if vb_width > 5000 or vb_height > 5000:
        print(
            f"architecture-svg-bounds-check: FAIL (viewBox unusually large: {vb_width}x{vb_height})"
        )
        return 1

    if width is not None and height is not None:
        ratio_w = width / vb_width
        ratio_h = height / vb_height
        if ratio_w <= 0 or ratio_h <= 0:
            print("architecture-svg-bounds-check: FAIL (invalid width/height ratio)")
            return 1
        if not math.isclose(ratio_w, ratio_h, rel_tol=0.20):
            print("architecture-svg-bounds-check: FAIL (width/height scaling mismatched vs viewBox)")
            return 1

    text_content = "".join(root.itertext()).lower()
    if "placeholder" in text_content and "generated" not in text_content:
        print("architecture-svg-bounds-check: FAIL (placeholder SVG must be explicitly marked generated)")
        return 1

    print(
        "architecture-svg-bounds-check: PASS "
        f"(width={root.get('width')}, height={root.get('height')}, viewBox={view_box})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
