/**
 * Deterministic JSON pointer diff (v0.1)
 *
 * Produces a stable, pointer-sorted list of changes between two JSON values.
 */
export type JsonValue =
  | null
  | boolean
  | number
  | string
  | JsonValue[]
  | { [k: string]: JsonValue };

export type PointerDiffChange = {
  pointer: string;
  before: JsonValue;
  after: JsonValue;
};

function encodePointerSegment(seg: string): string {
  return seg.replace(/~/g, "~0").replace(/\//g, "~1");
}

function walk(a: JsonValue, b: JsonValue, pointer: string, out: PointerDiffChange[]): void {
  const ta = Array.isArray(a) ? "array" : a === null ? "null" : typeof a;
  const tb = Array.isArray(b) ? "array" : b === null ? "null" : typeof b;

  if (ta !== tb) {
    out.push({ pointer, before: a, after: b });
    return;
  }

  if (ta === "array") {
    const aa = a as JsonValue[];
    const bb = b as JsonValue[];
    const n = Math.max(aa.length, bb.length);
    for (let i = 0; i < n; i++) {
      const va = i < aa.length ? aa[i] : null;
      const vb = i < bb.length ? bb[i] : null;
      walk(va, vb, `${pointer}/${i}`, out);
    }
    return;
  }

  if (ta === "object") {
    const ao = a as Record<string, JsonValue>;
    const bo = b as Record<string, JsonValue>;
    const keys = Array.from(new Set([...Object.keys(ao), ...Object.keys(bo)])).sort();
    for (const k of keys) {
      const va = Object.prototype.hasOwnProperty.call(ao, k) ? ao[k] : null;
      const vb = Object.prototype.hasOwnProperty.call(bo, k) ? bo[k] : null;
      walk(va, vb, `${pointer}/${encodePointerSegment(k)}`, out);
    }
    return;
  }

  if (a !== b) {
    out.push({ pointer, before: a, after: b });
  }
}

export function diffObjects(left: JsonValue, right: JsonValue): PointerDiffChange[] {
  const changes: PointerDiffChange[] = [];
  walk(left, right, "", changes);
  changes.sort((x, y) => x.pointer.localeCompare(y.pointer));
  return changes;
}
