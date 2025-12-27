import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG_PATH = ROOT / "registry" / "abx_rune_registry.json"
OUT_PATH = ROOT / "abx" / "schema_registry_gen.py"

TYPE_MAP = {
    "str": "str",
    "string": "str",
    "int": "int",
    "integer": "int",
    "float": "float",
    "number": "float",
    "bool": "bool",
    "boolean": "bool",
    "dict": "dict",
    "object": "dict",
    "list": "list",
    "array": "list",
}


def stable_json(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def infer_type(token: str) -> str:
    if not token:
        return "object"
    t = token.strip().lower()
    return TYPE_MAP.get(t, "object")


def load_registry():
    if not REG_PATH.exists():
        raise SystemExit(f"Missing registry: {REG_PATH}")
    return json.loads(REG_PATH.read_text(encoding="utf-8"))


def gen():
    reg = load_registry()
    runes = reg.get("runes", []) or []
    meta = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "registry_sha256": sha256_str(stable_json(reg)),
        "count": len(runes),
    }

    schemas = {}
    for rune in runes:
        rune_id = rune.get("rune_id")
        if not rune_id:
            continue
        inputs = rune.get("inputs", []) or []
        required = {}
        optional = {}
        for name in inputs:
            token = str(name)
            if token in ("text", "text_event", "query", "prompt"):
                required[token] = "str"
            elif token in ("config", "context", "policy", "health_state", "evidence", "action_plan"):
                required[token] = "dict" if token != "action_plan" else "list"
            else:
                required[token] = "dict"
        if "seed" not in required:
            optional["seed"] = "int"

        schemas[rune_id] = {
            "required": required,
            "optional": optional,
            "allow_extra": True,
        }

    lines = []
    lines.append("# AUTO-GENERATED. DO NOT EDIT.")
    lines.append(f"# meta: {stable_json(meta)}")
    lines.append("")
    lines.append("SCHEMAS = {")
    for rune_id, spec in schemas.items():
        lines.append(f'  "{rune_id}": {{')
        lines.append("    \"required\": {")
        for key, typ in spec["required"].items():
            py_t = TYPE_MAP.get(typ, "dict")
            if py_t == "str":
                pt = "str"
            elif py_t == "int":
                pt = "int"
            elif py_t == "float":
                pt = "float"
            elif py_t == "bool":
                pt = "bool"
            elif py_t == "list":
                pt = "list"
            else:
                pt = "dict"
            lines.append(f'      "{key}": {pt},')
        lines.append("    },")
        lines.append("    \"optional\": {")
        for key, typ in spec["optional"].items():
            if typ == "int":
                pt = "int"
            else:
                pt = "dict"
            lines.append(f'      "{key}": {pt},')
        lines.append("    },")
        lines.append(f'    "allow_extra": {str(spec["allow_extra"])},')
        lines.append("  },")
    lines.append("}")
    lines.append("")
    lines.append("def schema_for(rune_id: str):")
    lines.append("    return SCHEMAS.get(rune_id)")
    lines.append("")

    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(str(OUT_PATH))


if __name__ == "__main__":
    gen()
