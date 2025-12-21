#!/usr/bin/env python3
"""
ABX-Runes Retroactive Builder + Future-Proof Dynamic Builder
===========================================================

What it does (Abraxas repo):
- Scans abraxas/runes/definitions/*.json for rune defs.
- Ensures deterministic SVG sigils exist for every rune def.
- Writes/updates sigils/manifest.json with sha256 + seed provenance.
- Ensures operators exist for each rune:
  - If missing, generates a stub operator module with a deterministic, typed signature.
- Ensures operators/map.py contains a complete RuneID -> function mapping.
- Provides a dynamic dispatcher (operators/dispatch.py) so future runes can be added
  without manual wiring (optional strict mode still available).

No network calls. Stdlib only. Deterministic outputs. ABX-Core friendly.

Run:
  python scripts/abx_runes_build.py --write
  python scripts/abx_runes_build.py --check
  python scripts/abx_runes_build.py --write --strict-map

Assumes repo layout:
  abraxas/runes/definitions/
  abraxas/runes/sigils/
  abraxas/runes/operators/

If your layout differs, set ABX_RUNES_ROOT env var to point at abraxas/runes.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional


# ---------------------------
# Deterministic primitives
# ---------------------------

GENERATOR_VERSION = "abx_runes_build@1"
SVG_SIZE = 512
FLOAT_PREC = 3

def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

class SigilPRNG:
    """Hash-chain PRNG: deterministic and portable."""
    def __init__(self, seed_material: str) -> None:
        self.state = hashlib.sha256(seed_material.encode("utf-8")).digest()

    def next_bytes(self, n: int) -> bytes:
        out = b""
        while len(out) < n:
            self.state = hashlib.sha256(self.state).digest()
            out += self.state
        return out[:n]

    def next_u16(self) -> int:
        return int.from_bytes(self.next_bytes(2), "big")

    def next_f(self, lo: float, hi: float) -> float:
        x = self.next_u16() / 65535.0
        return lo + (hi - lo) * x

def f(x: float) -> str:
    return f"{x:.{FLOAT_PREC}f}"

def svg_header() -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_SIZE}" height="{SVG_SIZE}" '
        f'viewBox="0 0 {SVG_SIZE} {SVG_SIZE}">\n'
    )

def svg_footer() -> str:
    return "</svg>\n"

def svg_line(x1,y1,x2,y2,sw=3) -> str:
    return (
        f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" '
        f'stroke="#000" stroke-width="{sw}" stroke-linecap="round"/>\n'
    )

def svg_circle(cx,cy,r,sw=3,fill="none") -> str:
    return (
        f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" '
        f'stroke="#000" stroke-width="{sw}" fill="{fill}"/>\n'
    )

def svg_path(d,sw=3) -> str:
    return (
        f'<path d="{d}" stroke="#000" stroke-width="{sw}" fill="none" '
        f'stroke-linecap="round" stroke-linejoin="round"/>\n'
    )


# ---------------------------
# Rune schema
# ---------------------------

@dataclasses.dataclass(frozen=True)
class RuneDef:
    id: str
    name: str
    short_name: str
    layer: str
    motto: str
    canonical_statement: str
    function: str
    inputs: List[str]
    outputs: List[str]
    constraints: List[str]
    hooks: List[str]
    evidence_tier: str
    provenance_sources: List[str]
    introduced_version: str

    @staticmethod
    def from_json(d: Dict[str, Any]) -> "RuneDef":
        # Minimal normalization
        return RuneDef(
            id=str(d["id"]),
            name=str(d["name"]),
            short_name=str(d["short_name"]),
            layer=str(d.get("layer", "Core")),
            motto=str(d.get("motto", "")),
            canonical_statement=str(d.get("canonical_statement", "")),
            function=str(d.get("function", "")),
            inputs=list(d.get("inputs", [])),
            outputs=list(d.get("outputs", [])),
            constraints=list(d.get("constraints", [])),
            hooks=list(d.get("hooks", [])),
            evidence_tier=str(d.get("evidence_tier", "Unknown")),
            provenance_sources=list(d.get("provenance_sources", [])),
            introduced_version=str(d.get("introduced_version", "v0.0")),
        )

    def seed_material(self) -> str:
        # Deterministic, stable seed for sigils + any future derived artifacts
        return f"{self.id}|{self.name}|{self.introduced_version}|{self.canonical_statement}"


# ---------------------------
# Sigil rendering (generic)
# ---------------------------

def render_sigil(r: RuneDef) -> Tuple[str, str]:
    """
    Generic family style:
      - Outer ring + inner ring + central dot
      - Distinct motif derived from short_name + PRNG
    """
    import math

    seed = r.seed_material()
    prng = SigilPRNG(seed)

    cx = cy = SVG_SIZE / 2.0
    outer = prng.next_f(190, 220)
    inner = prng.next_f(70, 95)

    s = svg_header()
    s += '<g id="sigil">\n'
    s += svg_circle(cx, cy, outer, sw=4)
    s += svg_circle(cx, cy, inner, sw=3)
    s += svg_circle(cx, cy, 6, sw=0, fill="#000")

    sn = r.short_name.strip().upper()

    # Motif selection: stable by short_name prefix; falls back to hashed selection
    if sn == "RFA":
        k = 10 + (prng.next_u16() % 7)
        for i in range(k):
            ang = (i / k) * 2 * math.pi
            r2 = outer - 8
            r1 = inner + 10
            x1 = cx + r1 * math.cos(ang); y1 = cy + r1 * math.sin(ang)
            x2 = cx + r2 * math.cos(ang); y2 = cy + r2 * math.sin(ang)
            s += svg_line(x1, y1, x2, y2, sw=3)

    elif sn == "TAM":
        turns = 3 + (prng.next_u16() % 3)
        pts = []
        steps = 160
        for i in range(steps):
            t = i / (steps - 1)
            ang = t * turns * 2 * math.pi
            rad = inner + t * (outer - inner - 12)
            x = cx + rad * math.cos(ang); y = cy + rad * math.sin(ang)
            pts.append((x, y))
        d = "M " + " L ".join([f"{f(x)} {f(y)}" for x, y in pts])
        s += svg_path(d, sw=3)

    elif sn == "WSSS":
        r0 = outer - 18
        s += svg_path(
            f"M {f(cx-r0)} {f(cy-r0)} L {f(cx+r0)} {f(cy-r0)} L {f(cx+r0)} {f(cy+r0)} "
            f"L {f(cx-r0)} {f(cy+r0)} Z",
            sw=3,
        )
        amp = prng.next_f(6, 10)
        basey = cy + r0 * 0.55
        startx = cx - r0 * 0.8
        seg = 12
        pts = []
        for i in range(seg + 1):
            x = startx + (2 * r0 * 0.8) * (i / seg)
            y = basey + (amp * math.sin(i * math.pi))
            pts.append((x, y))
        d = "M " + " L ".join([f"{f(x)} {f(y)}" for x, y in pts])
        s += svg_path(d, sw=2)

    elif sn == "SDS":
        r0 = outer - 28
        s += svg_line(cx-r0*0.35, cy-r0*0.45, cx-r0*0.35, cy+r0*0.45, sw=4)
        s += svg_line(cx+r0*0.35, cy-r0*0.45, cx+r0*0.35, cy+r0*0.45, sw=4)
        open_ang = prng.next_f(0.7, 1.2)
        rr = r0 * 0.42
        a0 = -open_ang; a1 = open_ang
        x0 = cx + rr*math.cos(a0); y0 = cy + rr*math.sin(a0)
        x1 = cx + rr*math.cos(a1); y1 = cy + rr*math.sin(a1)
        s += svg_path(f"M {f(x0)} {f(y0)} A {f(rr)} {f(rr)} 0 0 1 {f(x1)} {f(y1)}", sw=4)

    elif sn == "IPL":
        r0 = outer - 26
        s += svg_path(
            f"M {f(cx-r0)} {f(cy-r0*0.4)} L {f(cx+r0)} {f(cy-r0*0.4)} L {f(cx+r0)} {f(cy+r0*0.4)} "
            f"L {f(cx-r0)} {f(cy+r0*0.4)} Z",
            sw=3,
        )
        for i in range(3):
            px = cx + (i - 1) * r0 * 0.3
            s += svg_line(px, cy-r0*0.25, px, cy+r0*0.25, sw=5)
        s += svg_line(cx+r0*0.65, cy+r0*0.45, cx+r0*0.85, cy+r0*0.45, sw=4)

    elif sn == "ADD":
        dx = prng.next_f(-22, 22); dy = prng.next_f(-22, 22)
        s += svg_circle(cx+dx, cy+dy, 8, sw=3)
        s += svg_line(cx+dx, cy+dy, cx, cy, sw=3)
        ang = math.atan2(-dy, -dx)
        head = 14
        a1 = ang + 0.5; a2 = ang - 0.5
        xh = cx; yh = cy
        s += svg_line(xh, yh, xh + head*math.cos(a1), yh + head*math.sin(a1), sw=3)
        s += svg_line(xh, yh, xh + head*math.cos(a2), yh + head*math.sin(a2), sw=3)

    else:
        # Fallback motif: deterministic radial chords + arc segment count
        k = 7 + (prng.next_u16() % 9)
        for i in range(k):
            ang = prng.next_f(0, 2*math.pi)
            ang2 = ang + prng.next_f(0.4, 2.2)
            r1 = prng.next_f(inner+8, outer-20)
            r2 = prng.next_f(inner+8, outer-20)
            x1 = cx + r1 * math.cos(ang);  y1 = cy + r1 * math.sin(ang)
            x2 = cx + r2 * math.cos(ang2); y2 = cy + r2 * math.sin(ang2)
            s += svg_line(x1, y1, x2, y2, sw=3)

    s += "</g>\n"
    s += svg_footer()
    return s, seed


# ---------------------------
# Operator stub generation
# ---------------------------

def safe_module_name(short_name: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", short_name.lower())

def make_operator_stub(r: RuneDef) -> str:
    """
    Generate a deterministic stub with:
      - apply_<short>() signature derived from inputs
      - returns dict with output keys (None values)
      - raises NotImplementedError if strict_execution=True
    """
    fn = f"apply_{safe_module_name(r.short_name)}"
    args = ", ".join([f"{re.sub(r'[^a-zA-Z0-9_]+','_',x)}: Any" for x in (r.inputs or ["payload"])])
    out_keys = r.outputs or ["result"]
    out_dict = "{\n" + "\n".join([f'        "{k}": None,' for k in out_keys]) + "\n    }"

    return f'''"""ABX-Rune Operator: {r.id} {r.short_name}

AUTO-GENERATED OPERATOR STUB
Rune: {r.id} {r.short_name} — {r.name}
Layer: {r.layer}
Motto: {r.motto}

Canonical statement:
  {r.canonical_statement}

Function:
  {r.function}

Inputs: {", ".join(r.inputs) if r.inputs else "payload"}
Outputs: {", ".join(out_keys)}

Constraints:
  - {'; '.join(r.constraints) if r.constraints else 'None'}

Provenance:
  {chr(10).join(f"  - {s}" for s in r.provenance_sources)}
"""

from __future__ import annotations
from typing import Any, Dict

def {fn}({args}, *, strict_execution: bool = False) -> Dict[str, Any]:
    """Apply {r.short_name} rune operator.

    Args:
        {chr(10).join(f"        {re.sub(r'[^a-zA-Z0-9_]+','_',x)}: Input {x}" for x in (r.inputs or ["payload"]))}
        strict_execution: If True, raises NotImplementedError for unimplemented operators

    Returns:
        Dict with keys: {", ".join(out_keys)}

    Raises:
        NotImplementedError: If strict_execution=True and operator not implemented
    """
    if strict_execution:
        raise NotImplementedError(
            f"Operator {r.short_name} not implemented yet. "
            f"Provide a real implementation for rune {r.id}."
        )

    # Stub implementation - returns empty outputs
    return {out_dict}
'''

def expected_operator_module_path(operators_dir: Path, r: RuneDef) -> Path:
    return operators_dir / f"{safe_module_name(r.short_name)}.py"

def expected_operator_function_name(r: RuneDef) -> str:
    return f"apply_{safe_module_name(r.short_name)}"


# ---------------------------
# Build orchestration
# ---------------------------

def load_runes(def_dir: Path) -> List[RuneDef]:
    out: List[RuneDef] = []
    for p in sorted(def_dir.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        out.append(RuneDef.from_json(d))
    if not out:
        raise SystemExit(f"No rune definitions found in {def_dir}")
    return out

def write_text(path: Path, text: str, *, write: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if write:
        path.write_text(text, encoding="utf-8", newline="\n")

def build_sigils(runes: List[RuneDef], sigil_dir: Path, *, write: bool, check: bool) -> Dict[str, Any]:
    sigil_dir.mkdir(parents=True, exist_ok=True)
    entries: List[Dict[str, Any]] = []
    changed: List[str] = []

    for r in runes:
        svg, seed = render_sigil(r)
        fn = f"{r.id}_{r.short_name}.svg"
        outp = sigil_dir / fn
        b = svg.encode("utf-8")
        h = sha256_hex(b)

        if check:
            if not outp.exists():
                raise SystemExit(f"[SIGIL] Missing {outp}")
            if sha256_hex(outp.read_bytes()) != h:
                raise SystemExit(f"[SIGIL] Hash mismatch {fn}")
        else:
            prior = outp.read_text(encoding="utf-8") if outp.exists() else None
            if prior != svg:
                changed.append(f"sigils/{fn}")
            write_text(outp, svg, write=write)

        entries.append({
            "id": r.id,
            "short_name": r.short_name,
            "svg_path": f"sigils/{fn}",
            "sha256": h,
            "seed_material": seed,
            "width": SVG_SIZE,
            "height": SVG_SIZE,
        })

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generator_version": GENERATOR_VERSION,
        "entries": entries,
    }
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    manifest_path = sigil_dir / "manifest.json"

    if check:
        if not manifest_path.exists():
            raise SystemExit("[MANIFEST] Missing manifest.json")
        # In check mode, we still verify that manifest entries match current generated ones
        current = json.loads(manifest_path.read_text(encoding="utf-8"))
        cur_entries = {(e["id"], e["short_name"]): e for e in current.get("entries", [])}
        for e in entries:
            key = (e["id"], e["short_name"])
            if key not in cur_entries:
                raise SystemExit(f"[MANIFEST] Missing entry for {key}")
            if cur_entries[key]["sha256"] != e["sha256"]:
                raise SystemExit(f"[MANIFEST] sha256 mismatch for {key}")
    else:
        prior = manifest_path.read_text(encoding="utf-8") if manifest_path.exists() else None
        if prior != manifest_text:
            changed.append("sigils/manifest.json")
        write_text(manifest_path, manifest_text, write=write)

    return {"changed": changed, "count": len(entries)}

def build_operators(runes: List[RuneDef], operators_dir: Path, *, write: bool, check: bool) -> Dict[str, Any]:
    operators_dir.mkdir(parents=True, exist_ok=True)
    changed: List[str] = []
    created: List[str] = []

    for r in runes:
        mod_path = expected_operator_module_path(operators_dir, r)
        if mod_path.exists():
            continue
        stub = make_operator_stub(r)
        if check:
            raise SystemExit(f"[OPERATORS] Missing operator module for {r.id} {r.short_name}: {mod_path}")
        created.append(str(mod_path.relative_to(operators_dir.parents[1] if len(operators_dir.parents) > 1 else operators_dir)))
        changed.append(str(mod_path))
        write_text(mod_path, stub, write=write)

    # Ensure __init__.py exists
    init_path = operators_dir / "__init__.py"
    init_content = '''"""ABX-Rune Operators.

This package contains operator implementations for each ABX-Rune.
Use the dispatch function for dynamic resolution.
"""

from .dispatch import dispatch

__all__ = ["dispatch"]
'''
    if not init_path.exists():
        if check:
            raise SystemExit(f"[OPERATORS] Missing {init_path}")
        write_text(init_path, init_content, write=write)
        changed.append(str(init_path))

    return {"changed": changed, "created": created}

def write_dispatcher(operators_dir: Path, *, write: bool, check: bool) -> None:
    """
    Dynamic dispatch: allows new runes to work without editing map.py,
    as long as operator modules follow naming convention apply_<short_name_lower>.
    """
    dispatch_path = operators_dir / "dispatch.py"
    text = """\"\"\"Dynamic ABX-Rune operator dispatcher.

Provides runtime resolution of rune IDs to operator functions.
\"\"\"

from __future__ import annotations
from typing import Any, Dict, Callable
import importlib
from pathlib import Path
import json

def _runes_root() -> Path:
    return Path(__file__).resolve().parents[1]

def _load_defs() -> list[dict]:
    defs_dir = _runes_root() / "definitions"
    out = []
    for p in sorted(defs_dir.glob("*.json")):
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out

def dispatch(rune_id: str, **kwargs: Any) -> Dict[str, Any]:
    \"\"\"Dynamic ABX-Rune dispatcher.

    Resolves rune_id -> definition -> operator module apply_<short_name>.
    If the operator is missing, raises a clear error.

    Args:
        rune_id: Rune identifier (e.g., "ϟ₁", "ϟ₂")
        **kwargs: Arguments to pass to the operator function

    Returns:
        Dict containing operator outputs

    Raises:
        KeyError: If rune_id is unknown
        ImportError: If operator module is missing
        AttributeError: If operator function is missing

    Example:
        >>> result = dispatch("ϟ₁", semantic_field=data, context_vector=ctx)
    \"\"\"
    defs = _load_defs()
    match = None
    for d in defs:
        if d.get("id") == rune_id:
            match = d
            break
    if not match:
        raise KeyError(f"Unknown rune id: {rune_id}")

    short_name = str(match["short_name"]).strip().lower()
    mod_name = short_name
    fn_name = f"apply_{short_name}"

    try:
        mod = importlib.import_module(f"abraxas.runes.operators.{mod_name}")
    except Exception as e:
        raise ImportError(
            f"Missing operator module for rune {rune_id} ({match['short_name']}): "
            f"abraxas.runes.operators.{mod_name}"
        ) from e

    fn = getattr(mod, fn_name, None)
    if not callable(fn):
        raise AttributeError(
            f"Missing operator function {fn_name} in module "
            f"abraxas.runes.operators.{mod_name}"
        )

    return fn(**kwargs)
"""
    if check and not dispatch_path.exists():
        raise SystemExit("[DISPATCH] Missing operators/dispatch.py")
    if not check:
        write_text(dispatch_path, text, write=write)

def write_map_py(runes: List[RuneDef], operators_dir: Path, *, write: bool, strict_map: bool) -> None:
    """
    Writes operators/map.py as a strict mapping (optional).
    Even if you use dynamic dispatch, keeping map.py helps traceability and speed.
    """
    if not strict_map:
        return
    map_path = operators_dir / "map.py"

    # Imports in deterministic order by rune id
    imports: List[str] = []
    mapping: List[str] = []
    for r in sorted(runes, key=lambda x: x.id):
        mod = safe_module_name(r.short_name)
        fn = expected_operator_function_name(r)
        imports.append(f"from .{mod} import {fn}")
        mapping.append(f'    "{r.id}": {fn},')

    text = (
        '"""Strict mapping of rune IDs to operator functions.\n\n'
        'Auto-generated by abx_runes_build.py --strict-map\n'
        '"""\n\n'
        "from __future__ import annotations\n"
        "from typing import Callable, Dict, Any\n\n"
        + "\n".join(imports)
        + "\n\n"
        + "RUNE_FUNCTIONS: Dict[str, Callable[..., Any]] = {\n"
        + "\n".join(mapping)
        + "\n}\n"
    )
    write_text(map_path, text, write=write)

def resolve_runes_root(repo_root: Path) -> Path:
    """Resolve runes root directory.

    Checks in order:
    1. ABX_RUNES_ROOT environment variable
    2. abraxas/runes (current layout)
    3. src/abraxas/runes (alternative layout)
    """
    # Allow override
    env = os.environ.get("ABX_RUNES_ROOT")
    if env:
        return Path(env).resolve()

    # Check current layout (abraxas/runes)
    cand1 = repo_root / "abraxas" / "runes"
    if cand1.exists():
        return cand1

    # Check alternative layout (src/abraxas/runes)
    cand2 = repo_root / "src" / "abraxas" / "runes"
    if cand2.exists():
        return cand2

    raise SystemExit(
        "Could not locate runes root. Set ABX_RUNES_ROOT or run from Abraxas repo root.\n"
        f"Checked: {cand1}, {cand2}"
    )

def main() -> int:
    ap = argparse.ArgumentParser(
        description="ABX-Runes retroactive builder and future-proof dynamic builder"
    )
    ap.add_argument("--write", action="store_true", help="Write changes to disk.")
    ap.add_argument("--check", action="store_true", help="Verify everything is built and deterministic.")
    ap.add_argument("--strict-map", action="store_true", help="Generate/update operators/map.py strict mapping.")
    args = ap.parse_args()

    if args.write == args.check:
        raise SystemExit("Choose exactly one of --write or --check")

    repo_root = Path.cwd().resolve()
    runes_root = resolve_runes_root(repo_root)

    print(f"ABX-Runes Builder (version: {GENERATOR_VERSION})")
    print(f"Runes root: {runes_root}")
    print()

    def_dir = runes_root / "definitions"
    sigil_dir = runes_root / "sigils"
    operators_dir = runes_root / "operators"

    runes = load_runes(def_dir)
    print(f"Loaded {len(runes)} rune definitions")

    # 1) Sigils + manifest
    sig_res = build_sigils(runes, sigil_dir, write=args.write, check=args.check)

    # 2) Operator stubs for missing runes
    op_res = build_operators(runes, operators_dir, write=args.write, check=args.check)

    # 3) Dynamic dispatcher (future-proof)
    write_dispatcher(operators_dir, write=args.write, check=args.check)

    # 4) Optional strict mapping file
    if args.write:
        write_map_py(runes, operators_dir, write=True, strict_map=args.strict_map)

    if args.check:
        print("[OK] ABX-Runes build verified (sigils, manifest, operators, dispatch).")
        return 0

    # Write-mode summary
    print()
    print("[DONE] ABX-Runes build applied.")
    if sig_res["changed"]:
        print("Changed:")
        for x in sig_res["changed"]:
            print("  -", x)
    if op_res["created"]:
        print("Operator stubs created:")
        for x in op_res["created"]:
            print("  -", x)
    if args.strict_map:
        print("Strict mapping written: operators/map.py")

    print()
    print("Next:")
    print("  python scripts/abx_runes_build.py --check")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
