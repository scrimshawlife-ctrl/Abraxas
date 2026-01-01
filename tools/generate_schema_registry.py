import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

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


def parse_inputs(inputs: Any) -> List[Dict[str, Any]]:
    """
    Supports:
      - ["text_event", "config"]
      - [{"name":"text_event","type":"string","required":true}, ...]
    Returns normalized list of {name,type,required}.
    """
    if inputs is None:
        return []
    if isinstance(inputs, list) and (len(inputs) == 0):
        return []
    if isinstance(inputs, list) and isinstance(inputs[0], str):
        # Old format: infer types using heuristics, assume required
        out = []
        for name in inputs:
            n = str(name)
            # Use same heuristics as before for backwards compatibility
            if n in ("text", "text_event", "query", "prompt"):
                typ = "str"
            elif n in ("config", "context", "policy", "health_state", "evidence"):
                typ = "dict"
            elif n == "action_plan":
                typ = "list"
            else:
                typ = "dict"
            out.append({"name": n, "type": typ, "required": True})
        return out
    if isinstance(inputs, list) and isinstance(inputs[0], dict):
        out = []
        for it in inputs:
            name = str(it.get("name", "")).strip()
            if not name:
                continue
            out.append({
                "name": name,
                "type": TYPE_MAP.get(str(it.get("type", "object")).strip().lower(), "dict"),
                "required": bool(it.get("required", True))
            })
        return out
    return []


def parse_outputs(outputs: Any) -> List[Dict[str, Any]]:
    """
    Supports:
      - ["compression_event", "metrics"]
      - [{"name":"compression_event","type":"object","required":true}, ...]
    Returns normalized list of {name,type,required}.
    """
    if outputs is None:
        return []
    if isinstance(outputs, list) and (len(outputs) == 0):
        return []
    if isinstance(outputs, list) and isinstance(outputs[0], str):
        # Old format: all optional, type=object
        return [{"name": n, "type": "dict", "required": False} for n in outputs]
    if isinstance(outputs, list) and isinstance(outputs[0], dict):
        out = []
        for it in outputs:
            name = str(it.get("name", "")).strip()
            if not name:
                continue
            out.append({
                "name": name,
                "type": TYPE_MAP.get(str(it.get("type", "object")).strip().lower(), "dict"),
                "required": bool(it.get("required", False))
            })
        return out
    return []


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

    payload_schemas = {}
    result_schemas = {}
    for rune in runes:
        rune_id = rune.get("rune_id")
        if not rune_id:
            continue

        # Payload schema (inputs)
        required = {}
        optional = {}
        norm_inputs = parse_inputs(rune.get("inputs"))
        for it in norm_inputs:
            n = it["name"]
            t = it["type"]
            is_req = it["required"]
            py_t = TYPE_MAP.get(t, "dict")
            if is_req:
                required[n] = py_t
            else:
                optional[n] = py_t

        payload_schemas[rune_id] = {
            "required": required,
            "optional": optional,
            "allow_extra": True,
        }

        # Result schema (outputs)
        r_req = {}
        r_opt = {}
        norm_outputs = parse_outputs(rune.get("outputs"))
        for it in norm_outputs:
            n = it["name"]
            t = it["type"]
            is_req = it["required"]
            py_t = TYPE_MAP.get(t, "dict")
            if is_req:
                r_req[n] = py_t
            else:
                r_opt[n] = py_t

        result_schemas[rune_id] = {
            "required": r_req,
            "optional": r_opt,
            "allow_extra": True,
        }

    lines = []
    lines.append("# AUTO-GENERATED. DO NOT EDIT.")
    lines.append(f"# meta: {stable_json(meta)}")
    lines.append("")
    lines.append("PAYLOAD_SCHEMAS = {")
    for rune_id, spec in payload_schemas.items():
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
        lines.append(f'    "allow_extra": {str(spec["allow_extra"])},')
        lines.append("  },")
    lines.append("}")
    lines.append("")
    lines.append("RESULT_SCHEMAS = {")
    for rune_id, spec in result_schemas.items():
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
        lines.append(f'    "allow_extra": {str(spec["allow_extra"])},')
        lines.append("  },")
    lines.append("}")
    lines.append("")
    lines.append("# Backwards compatibility")
    lines.append("SCHEMAS = PAYLOAD_SCHEMAS")
    lines.append("")
    lines.append("def payload_schema_for(rune_id: str):")
    lines.append("    return PAYLOAD_SCHEMAS.get(rune_id)")
    lines.append("")
    lines.append("def result_schema_for(rune_id: str):")
    lines.append("    return RESULT_SCHEMAS.get(rune_id)")
    lines.append("")
    lines.append("def schema_for(rune_id: str):")
    lines.append("    \"\"\"Backwards compatibility - returns payload schema.\"\"\"")
    lines.append("    return PAYLOAD_SCHEMAS.get(rune_id)")
    lines.append("")

    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(str(OUT_PATH))


if __name__ == "__main__":
    gen()
