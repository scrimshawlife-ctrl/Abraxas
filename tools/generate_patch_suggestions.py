import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def stable_json(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def load_registry():
    reg = ROOT / "registry" / "abx_rune_registry.json"
    if not reg.exists():
        return {"runes": []}
    return json.loads(reg.read_text(encoding="utf-8"))


def rune_ids(registry: dict) -> list[str]:
    return [
        rune.get("rune_id")
        for rune in registry.get("runes", [])
        if rune.get("rune_id")
    ]


def best_rune_for_symbol(registry: dict, symbol: str) -> str:
    symbol_lower = (symbol or "").lower()
    ids = rune_ids(registry)
    for rune_id in ids:
        if rune_id and rune_id.lower() in symbol_lower:
            return rune_id
    if "compression" in symbol_lower:
        return "compression.detect" if "compression.detect" in ids else (ids[0] if ids else "UNKNOWN")
    if "self_heal" in symbol_lower or "self-heal" in symbol_lower or "heal" in symbol_lower:
        return "infra.self_heal" if "infra.self_heal" in ids else (ids[0] if ids else "UNKNOWN")
    if "systemctl" in symbol_lower or "systemd" in symbol_lower or "restart" in symbol_lower:
        return "actuator.apply" if "actuator.apply" in ids else (ids[0] if ids else "UNKNOWN")
    return ids[0] if ids else "UNKNOWN"


def read_file(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8", errors="ignore")


def write_text(relpath: str, text: str):
    path = ROOT / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def mk_diff_header(meta: dict) -> str:
    ts = datetime.now(timezone.utc).isoformat()
    meta_sha = sha256_str(stable_json(meta))
    return (
        "# PATCH-SUGGESTION (UNAPPLIED)\n"
        f"# generated_at_utc: {ts}\n"
        f"# meta_sha256: {meta_sha}\n"
        f"# meta: {stable_json(meta)}\n\n"
    )


def boundary_from_file(rel: str) -> str:
    rel = rel.replace("\\", "/")
    return rel.split("/", 1)[0] if "/" in rel else "root"


def wrapper_path_for(rel: str) -> str:
    boundary = boundary_from_file(rel)
    return f"{boundary}/rune_wrappers/generated_wrappers.py"


def ensure_wrapper_file_block(rune_id: str) -> str:
    fn_name = rune_id.replace(".", "_").replace("-", "_")
    return (
        "from abx.kernel import invoke\n\n"
        f"def {fn_name}(payload: dict, context: dict | None = None):\n"
        f"    \"\"\"Auto-generated wrapper: {rune_id} via kernel.invoke.\"\"\"\n"
        f"    return invoke(rune_id=\"{rune_id}\", payload=payload, context=context or {{}})\n"
    )


def suggest_cross_boundary_stub(item: dict) -> str:
    file = item["file"]
    line = int(item["line"])
    symbol = item.get("symbol", "")
    rel = file.replace("\\", "/")

    src = read_file(rel).splitlines()
    idx = max(0, min(len(src) - 1, line - 1))
    original = src[idx]

    registry = load_registry()
    rune_id = best_rune_for_symbol(registry, symbol)
    wrapper_rel = wrapper_path_for(rel)

    wrapper_exists = (ROOT / wrapper_rel).exists()
    wrapper_body = ensure_wrapper_file_block(rune_id)
    wrapper_diff = []
    if not wrapper_exists:
        wrapper_diff.append(f"diff --git a/{wrapper_rel} b/{wrapper_rel}")
        wrapper_diff.append("new file mode 100644")
        wrapper_diff.append("--- /dev/null")
        wrapper_diff.append(f"+++ b/{wrapper_rel}")
        wrapper_diff.append(
            f"@@ -0,0 +1,{len(wrapper_body.splitlines())} @@"
        )
        wrapper_diff.append(wrapper_body)
        wrapper_diff = "\n".join(wrapper_diff) + "\n"
    else:
        existing = read_file(wrapper_rel)
        if rune_id.replace(".", "_") not in existing:
            wrapper_diff.append(f"diff --git a/{wrapper_rel} b/{wrapper_rel}")
            wrapper_diff.append(f"--- a/{wrapper_rel}")
            wrapper_diff.append(f"+++ b/{wrapper_rel}")
            wrapper_diff.append(
                f"@@ -1,1 +1,{len(wrapper_body.splitlines()) + 1} @@"
            )
            wrapper_diff.append(existing.rstrip() + "\n\n" + wrapper_body)
            wrapper_diff = "\n".join(wrapper_diff) + "\n"
        else:
            wrapper_diff = ""

    fn_name = rune_id.replace(".", "_").replace("-", "_")
    insert = [
        original,
        "# ABX-RUNES MIGRATION: "
        f"{item.get('from')}→{item.get('to')} bypass detected for symbol={symbol}",
        f"# Proposed wrapper: from {wrapper_rel.replace('/', '.').replace('.py','')} import {fn_name}",
        "# Then replace direct call sites with:",
        f"#   resp = {fn_name}(payload={{...}}, context={{}})",
    ]
    new_src = src[:idx] + insert + src[idx + 1 :]

    old_block = "\n".join(src[max(0, idx - 1) : min(len(src), idx + 2)])
    new_block = "\n".join(new_src[max(0, idx - 1) : min(len(new_src), idx + 7)])

    callsite_diff = []
    callsite_diff.append(f"diff --git a/{rel} b/{rel}")
    callsite_diff.append(f"--- a/{rel}")
    callsite_diff.append(f"+++ b/{rel}")
    callsite_diff.append(f"@@ -{max(1, line - 1)},3 +{max(1, line - 1)},8 @@")
    callsite_diff.append(old_block)
    callsite_diff.append(new_block)
    callsite_diff = "\n".join(callsite_diff) + "\n"

    return (wrapper_diff + "\n" + callsite_diff).strip() + "\n"


def suggest_forbidden_actuation_note(item: dict) -> str:
    file = item["file"]
    line = int(item["line"])
    rel = file.replace("\\", "/")
    src = read_file(rel).splitlines()
    idx = max(0, min(len(src) - 1, line - 1))
    original = src[idx]

    new_line = (
        f"{original}\n"
        "# ABX-GATE VIOLATION: forbidden actuation outside infra/actuator.py. "
        "Move into actuator.apply behind governance."
    )

    diff = []
    diff.append(f"diff --git a/{rel} b/{rel}")
    diff.append(f"--- a/{rel}")
    diff.append(f"+++ b/{rel}")
    diff.append(f"@@ -{line},1 +{line},2 @@")
    diff.append(original)
    diff.append(new_line)
    return "\n".join(diff) + "\n"


def suggest_detector_purity_split(item: dict) -> str:
    file = item["file"]
    line = int(item["line"])
    rel = file.replace("\\", "/")
    src = read_file(rel).splitlines()
    idx = max(0, min(len(src) - 1, line - 1))
    original = src[idx]

    insert = [
        original,
        "# ABX-DETECTOR PURITY: split into pure core(text, config)->result and io_shell() that calls core.",
        "# Detectors must annotate/log only; side effects must be behind governed actuator.",
    ]
    new_src = src[:idx] + insert + src[idx + 1 :]

    old_block = "\n".join(src[max(0, idx - 1) : min(len(src), idx + 2)])
    new_block = "\n".join(new_src[max(0, idx - 1) : min(len(new_src), idx + 5)])

    diff = []
    diff.append(f"diff --git a/{rel} b/{rel}")
    diff.append(f"--- a/{rel}")
    diff.append(f"+++ b/{rel}")
    diff.append(f"@@ -{max(1, line - 1)},3 +{max(1, line - 1)},6 @@")
    diff.append(old_block)
    diff.append(new_block)
    return "\n".join(diff) + "\n"


def main():
    audit_path = "data/audit_report.json"
    mq_path = "data/migration_queue.json"

    if not (ROOT / audit_path).exists():
        raise SystemExit(
            "Missing data/audit_report.json. Run: abx doctor --full --emit data/audit_report.json"
        )
    if not (ROOT / mq_path).exists():
        raise SystemExit("Missing data/migration_queue.json. Run: abx doctor --full")

    audit = load_json(audit_path)
    findings = audit.get("findings", {}) or {}
    cross = findings.get("cross_boundary_imports", []) or []
    forbidden = findings.get("forbidden_actuation", []) or []
    detector = findings.get("detector_purity", []) or []

    out_dir = ROOT / "data" / "patch_suggestions"
    out_dir.mkdir(parents=True, exist_ok=True)

    batch = []

    for i, item in enumerate(forbidden[:10], start=1):
        meta = {"type": "forbidden_actuation", "rank": i, "item": item}
        diff = mk_diff_header(meta) + suggest_forbidden_actuation_note(item)
        name = (
            f"p{1:02d}_{i:03d}_forbidden_actuation_"
            f"{sha256_str(stable_json(item))[:12]}.diff"
        )
        write_text(f"data/patch_suggestions/{name}", diff)
        batch.append(name)

    for i, item in enumerate(cross[:25], start=1):
        registry = load_registry()
        rune_id = best_rune_for_symbol(registry, item.get("symbol", ""))
        meta = {"type": "cross_boundary_import", "rank": i, "item": item}
        diff = mk_diff_header(meta) + suggest_cross_boundary_stub(item)
        safe_rune = rune_id.replace(".", "_").replace("-", "_")
        name = (
            f"p{2:02d}_{i:03d}_cross_boundary_{safe_rune}_"
            f"{sha256_str(stable_json(item))[:12]}.diff"
        )
        write_text(f"data/patch_suggestions/{name}", diff)
        batch.append(name)

    for i, item in enumerate(detector[:25], start=1):
        meta = {"type": "detector_purity", "rank": i, "item": item}
        diff = mk_diff_header(meta) + suggest_detector_purity_split(item)
        name = (
            f"p{3:02d}_{i:03d}_detector_purity_"
            f"{sha256_str(stable_json(item))[:12]}.diff"
        )
        write_text(f"data/patch_suggestions/{name}", diff)
        batch.append(name)

    index = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "count": len(batch),
        "files": batch,
    }
    write_text(
        "data/patch_suggestions/index.json",
        json.dumps(index, indent=2, sort_keys=True),
    )
    print("data/patch_suggestions/index.json")


if __name__ == "__main__":
    main()
