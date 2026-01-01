export function encodePointerSegment(seg: string): string {
  return seg.replace(/~/g, "~0").replace(/\//g, "~1");
}

export function pointerToPath(pointer: string): (string | number)[] {
  if (!pointer || pointer === "/") return [];
  if (!pointer.startsWith("/")) return [];
  return pointer
    .slice(1)
    .split("/")
    .map((s) => s.replace(/~1/g, "/").replace(/~0/g, "~"))
    .map((s) => (/^\d+$/.test(s) ? Number(s) : s));
}

export function jsonPointerGet(doc: unknown, pointer: string): unknown {
  if (pointer === "" || pointer === "/") return doc;
  if (!pointer.startsWith("/")) throw new Error("invalid_pointer");

  const path = pointerToPath(pointer);
  let cur: any = doc;
  for (const seg of path) {
    if (Array.isArray(cur) && typeof seg === "number") {
      cur = cur[seg];
    } else if (cur && typeof cur === "object") {
      cur = cur[String(seg)];
    } else {
      return undefined;
    }
  }
  return cur;
}

