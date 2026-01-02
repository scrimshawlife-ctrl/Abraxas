import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { FileJson, GitCompare, Layers, Search } from "lucide-react";

type ArtifactKind = "oracle_envelope_v2" | "narrative_bundle_v1" | "drift_report_v1" | "unknown";

type ArtifactStatusFlags = {
  missing_inputs?: boolean;
  not_computable?: boolean;
};

type ArtifactIndexItem = {
  artifact_id: string;
  kind: ArtifactKind;
  relative_path: string;
  filename: string;
  created_at?: string;
  schema_version?: string;
  tags?: string[];
  status_flags?: ArtifactStatusFlags;
};

type ArtifactIndexEntry = {
  artifact_id: string;
  created_at?: string;
  schema_version?: string;
  tags?: string[];
  status_flags?: ArtifactStatusFlags;
  available: { envelope: boolean; narrative: boolean };
  files: ArtifactIndexItem[];
};

type ArtifactIndex = {
  root_dir: string;
  items: ArtifactIndexEntry[];
};

type JsonValue =
  | null
  | boolean
  | number
  | string
  | JsonValue[]
  | { [k: string]: JsonValue };

type DiffEntry =
  | { type: "added"; pointer: string; after: JsonValue }
  | { type: "removed"; pointer: string; before: JsonValue }
  | { type: "changed"; pointer: string; before: JsonValue; after: JsonValue };

function isObject(v: JsonValue): v is Record<string, JsonValue> {
  return !!v && typeof v === "object" && !Array.isArray(v);
}

function encodePointerSegment(seg: string): string {
  return seg.replaceAll("~", "~0").replaceAll("/", "~1");
}

function decodePointerSegment(seg: string): string {
  return seg.replaceAll("~1", "/").replaceAll("~0", "~");
}

function normalizePointer(pointer: string): string {
  if (!pointer) return "";
  if (pointer.startsWith("#/")) return pointer.slice(1);
  return pointer;
}

function parsePointer(pointer: string): (string | number)[] {
  const p = normalizePointer(pointer);
  if (!p) return [];
  if (p.startsWith("/")) {
    // RFC6901 JSON Pointer
    return p
      .split("/")
      .slice(1)
      .map((s) => decodePointerSegment(s))
      .map((s) => (s.match(/^\d+$/) ? Number(s) : s));
  }
  // Fallback: dot path with optional [idx]
  const out: (string | number)[] = [];
  for (const part of p.split(".").filter(Boolean)) {
    const m = part.match(/^([^\[]+)(?:\[(\d+)\])?$/);
    if (!m) continue;
    out.push(m[1]);
    if (m[2]) out.push(Number(m[2]));
  }
  return out;
}

function toJsonPointer(segments: (string | number)[]): string {
  if (!segments.length) return "";
  return (
    "/" +
    segments
      .map((s) => (typeof s === "number" ? String(s) : encodePointerSegment(s)))
      .join("/")
  );
}

function getAtPointer(root: JsonValue, pointer: string): { ok: boolean; value?: JsonValue } {
  const segs = parsePointer(pointer);
  let cur: JsonValue = root;
  for (const seg of segs) {
    if (typeof seg === "number") {
      if (!Array.isArray(cur)) return { ok: false };
      cur = cur[seg];
      continue;
    }
    if (!isObject(cur)) return { ok: false };
    cur = cur[seg];
  }
  return { ok: true, value: cur };
}

function stableStringify(value: JsonValue, indent = 2): string {
  const seen = new WeakSet<object>();
  const normalize = (v: JsonValue): JsonValue => {
    if (!v || typeof v !== "object") return v;
    if (Array.isArray(v)) return v.map(normalize);
    if (seen.has(v as object)) return null; // should never happen for JSON artifacts
    seen.add(v as object);
    const obj = v as Record<string, JsonValue>;
    const keys = Object.keys(obj).sort((a, b) => a.localeCompare(b));
    const out: Record<string, JsonValue> = {};
    for (const k of keys) out[k] = normalize(obj[k]);
    return out;
  };
  return JSON.stringify(normalize(value), null, indent);
}

function diffJson(a: JsonValue, b: JsonValue): DiffEntry[] {
  const out: DiffEntry[] = [];
  const walk = (pa: (string | number)[], va: JsonValue, vb: JsonValue) => {
    if (va === vb) return;
    if (Array.isArray(va) && Array.isArray(vb)) {
      const max = Math.max(va.length, vb.length);
      for (let i = 0; i < max; i++) {
        if (i >= va.length) {
          out.push({ type: "added", pointer: toJsonPointer([...pa, i]), after: vb[i] });
        } else if (i >= vb.length) {
          out.push({ type: "removed", pointer: toJsonPointer([...pa, i]), before: va[i] });
        } else {
          walk([...pa, i], va[i], vb[i]);
        }
      }
      return;
    }
    if (isObject(va) && isObject(vb)) {
      const keys = Array.from(new Set([...Object.keys(va), ...Object.keys(vb)])).sort((x, y) =>
        x.localeCompare(y),
      );
      for (const k of keys) {
        if (!(k in va)) {
          out.push({ type: "added", pointer: toJsonPointer([...pa, k]), after: vb[k] });
        } else if (!(k in vb)) {
          out.push({ type: "removed", pointer: toJsonPointer([...pa, k]), before: va[k] });
        } else {
          walk([...pa, k], va[k], vb[k]);
        }
      }
      return;
    }
    out.push({ type: "changed", pointer: toJsonPointer(pa), before: va, after: vb });
  };
  walk([], a, b);
  out.sort((x, y) => x.pointer.localeCompare(y.pointer));
  return out;
}

function findFirstPointerByKey(root: JsonValue, key: string): string | null {
  // Deterministic DFS: object keys sorted.
  const walk = (path: (string | number)[], v: JsonValue): string | null => {
    if (isObject(v)) {
      const keys = Object.keys(v).sort((a, b) => a.localeCompare(b));
      for (const k of keys) {
        if (k === key) return toJsonPointer([...path, k]);
        const found = walk([...path, k], v[k]);
        if (found) return found;
      }
    } else if (Array.isArray(v)) {
      for (let i = 0; i < v.length; i++) {
        const found = walk([...path, i], v[i]);
        if (found) return found;
      }
    }
    return null;
  };
  return walk([], root);
}

function JsonTree(props: {
  value: JsonValue;
  selectedPointer: string;
  onSelectPointer: (pointer: string) => void;
}) {
  const { value, selectedPointer, onSelectPointer } = props;
  const [open, setOpen] = useState<Record<string, boolean>>({ "/": true });
  const nodesRef = useRef<Map<string, HTMLElement>>(new Map());

  const selectedSegs = useMemo(() => parsePointer(selectedPointer), [selectedPointer]);
  const selectedAncestors = useMemo(() => {
    const set = new Set<string>(["/"]);
    const cur: (string | number)[] = [];
    for (const seg of selectedSegs) {
      cur.push(seg);
      set.add(toJsonPointer(cur));
    }
    return set;
  }, [selectedSegs]);

  useEffect(() => {
    if (!selectedPointer) return;
    // Ensure ancestors are open.
    setOpen((prev) => {
      const next = { ...prev };
      for (const p of Array.from(selectedAncestors)) next[p] = true;
      return next;
    });
    const el = nodesRef.current.get(normalizePointer(selectedPointer) || "/");
    if (el) el.scrollIntoView({ block: "center" });
  }, [selectedPointer, selectedAncestors]);

  const renderNode = (pathSegs: (string | number)[], v: JsonValue, label?: string) => {
    const pointer = pathSegs.length ? toJsonPointer(pathSegs) : "/";
    const isSelected = normalizePointer(selectedPointer) === pointer || (!selectedPointer && pointer === "/");
    const isContainer = isObject(v) || Array.isArray(v);
    const isOpen = open[pointer] ?? selectedAncestors.has(pointer);

    const setNodeRef = (el: HTMLElement | null) => {
      if (!el) {
        nodesRef.current.delete(pointer);
        return;
      }
      nodesRef.current.set(pointer, el);
    };

    const line = (
      <div
        key={`line:${pointer}`}
        ref={setNodeRef as any}
        className={[
          "flex items-center gap-2 rounded px-2 py-1 font-mono text-xs",
          "hover:bg-muted/50 cursor-pointer",
          isSelected ? "bg-muted" : "",
        ].join(" ")}
        onClick={() => onSelectPointer(pointer === "/" ? "" : pointer)}
        title={`${pointer}`}
      >
        <div className="w-5 text-muted-foreground select-none">
          {isContainer ? (
            <button
              type="button"
              className="w-5 text-left"
              onClick={(e) => {
                e.stopPropagation();
                setOpen((prev) => ({ ...prev, [pointer]: !isOpen }));
              }}
              aria-label={isOpen ? "Collapse" : "Expand"}
            >
              {isOpen ? "▾" : "▸"}
            </button>
          ) : (
            ""
          )}
        </div>
        <div className="flex-1 min-w-0">
          {label !== undefined && <span className="text-foreground">{label}</span>}
          {label !== undefined && <span className="text-muted-foreground">: </span>}
          {!isContainer && (
            <span className="text-muted-foreground break-all">
              {typeof v === "string" ? JSON.stringify(v) : String(v)}
            </span>
          )}
          {Array.isArray(v) && <span className="text-muted-foreground">[len={v.length}]</span>}
          {isObject(v) && <span className="text-muted-foreground">{`{keys=${Object.keys(v).length}}`}</span>}
        </div>
      </div>
    );

    if (!isContainer) return line;

    const children: React.ReactNode[] = [];
    if (isOpen) {
      if (Array.isArray(v)) {
        for (let i = 0; i < v.length; i++) {
          children.push(
            <div key={`child:${pointer}:${i}`} className="pl-4">
              {renderNode([...pathSegs, i], v[i], String(i))}
            </div>,
          );
        }
      } else if (isObject(v)) {
        const keys = Object.keys(v).sort((a, b) => a.localeCompare(b));
        for (const k of keys) {
          children.push(
            <div key={`child:${pointer}:${k}`} className="pl-4">
              {renderNode([...pathSegs, k], v[k], k)}
            </div>,
          );
        }
      }
    }

    return (
      <div key={`node:${pointer}`}>
        {line}
        {children}
      </div>
    );
  };

  return <div className="space-y-0.5">{renderNode([], value, undefined)}</div>;
}

function CompactJson(props: { value: JsonValue }) {
  return (
    <pre className="font-mono text-xs whitespace-pre-wrap break-words bg-muted/30 border rounded p-3 overflow-auto">
      {stableStringify(props.value, 2)}
    </pre>
  );
}

export default function DashboardLens() {
  const [artifactFilter, setArtifactFilter] = useState("");
  const [selectedArtifactId, setSelectedArtifactId] = useState<string>("");
  const [selectedPointer, setSelectedPointer] = useState<string>("");
  const [driftId, setDriftId] = useState<string>("");
  const [diffA, setDiffA] = useState<string>("");
  const [diffB, setDiffB] = useState<string>("");

  const { data: index, isLoading: indexLoading, error: indexError } = useQuery<ArtifactIndex>({
    queryKey: ["/api/artifacts"],
  });

  const artifactIds = useMemo(() => {
    const ids = (index?.items ?? []).map((i) => i.artifact_id);
    ids.sort((a, b) => a.localeCompare(b));
    return ids;
  }, [index?.items]);

  const selectedEntry = useMemo(() => {
    if (!selectedArtifactId) return null;
    return (index?.items ?? []).find((i) => i.artifact_id === selectedArtifactId) ?? null;
  }, [index?.items, selectedArtifactId]);

  const { data: envelope } = useQuery<JsonValue>({
    queryKey: ["/api/artifacts", encodeURIComponent(selectedArtifactId), "envelope"],
    enabled: !!selectedArtifactId,
    retry: false,
  });

  const { data: narrative } = useQuery<JsonValue>({
    queryKey: ["/api/artifacts", encodeURIComponent(selectedArtifactId), "narrative"],
    enabled: !!selectedArtifactId,
    retry: false,
  });

  const { data: driftIndex } = useQuery<{ root_dir: string; items: ArtifactIndexEntry[] }>({
    queryKey: ["/api/drift_reports"],
    retry: false,
  });

  const { data: drift } = useQuery<JsonValue>({
    queryKey: ["/api/drift_reports", encodeURIComponent(driftId)],
    enabled: !!driftId,
    retry: false,
  });

  const { data: diffEnvelopeA } = useQuery<JsonValue>({
    queryKey: ["/api/artifacts", encodeURIComponent(diffA), "envelope"],
    enabled: !!diffA,
    retry: false,
  });
  const { data: diffEnvelopeB } = useQuery<JsonValue>({
    queryKey: ["/api/artifacts", encodeURIComponent(diffB), "envelope"],
    enabled: !!diffB,
    retry: false,
  });
  const { data: diffNarrativeA } = useQuery<JsonValue>({
    queryKey: ["/api/artifacts", encodeURIComponent(diffA), "narrative"],
    enabled: !!diffA,
    retry: false,
  });
  const { data: diffNarrativeB } = useQuery<JsonValue>({
    queryKey: ["/api/artifacts", encodeURIComponent(diffB), "narrative"],
    enabled: !!diffB,
    retry: false,
  });

  const filteredItems = useMemo(() => {
    const items = index?.items ?? [];
    const q = artifactFilter.trim().toLowerCase();
    if (!q) return items;
    return items.filter((it) => it.artifact_id.toLowerCase().includes(q));
  }, [artifactFilter, index?.items]);

  const envelopePanels = useMemo(() => {
    if (!envelope) return [];
    const keys = ["signal_scores", "motifs", "clusters", "constraints", "provenance"];
    return keys
      .map((k) => ({ key: k, pointer: findFirstPointerByKey(envelope, k) }))
      .filter((x) => x.pointer);
  }, [envelope]);

  const driftClusters = useMemo(() => {
    if (!drift) return [];
    // Common shapes: { clusters: [...] } or nested.
    const direct = isObject(drift) ? drift["clusters"] : null;
    if (Array.isArray(direct)) return direct as JsonValue[];
    const p = findFirstPointerByKey(drift, "clusters");
    if (!p) return [];
    const got = getAtPointer(drift, p);
    if (got.ok && Array.isArray(got.value)) return got.value as JsonValue[];
    return [];
  }, [drift]);

  const envelopeDiff = useMemo(() => {
    if (!diffEnvelopeA || !diffEnvelopeB) return [];
    return diffJson(diffEnvelopeA, diffEnvelopeB);
  }, [diffEnvelopeA, diffEnvelopeB]);

  const narrativeDiff = useMemo(() => {
    if (!diffNarrativeA || !diffNarrativeB) return [];
    return diffJson(diffNarrativeA, diffNarrativeB);
  }, [diffNarrativeA, diffNarrativeB]);

  // Seed diff selections for convenience.
  useEffect(() => {
    if (artifactIds.length && !diffA) setDiffA(artifactIds[0]);
    if (artifactIds.length > 1 && !diffB) setDiffB(artifactIds[1]);
  }, [artifactIds, diffA, diffB]);

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-2xl font-semibold flex items-center gap-2">
            <Layers className="w-6 h-6" />
            Dashboard Lens (v0.1)
          </div>
          <div className="text-sm text-muted-foreground">
            Read-only viewer for artifacts. No truth computation; audit-first pointer jumps.
          </div>
          <div className="mt-2 text-xs text-muted-foreground">
            Artifact root: <span className="font-mono">{index?.root_dir ?? "(loading...)"}</span>
          </div>
        </div>
      </div>

      <Tabs defaultValue="browse">
        <TabsList>
          <TabsTrigger value="browse">
            <FileJson className="w-4 h-4 mr-2" />
            Artifacts
          </TabsTrigger>
          <TabsTrigger value="drift">
            <Search className="w-4 h-4 mr-2" />
            Drift
          </TabsTrigger>
          <TabsTrigger value="diff">
            <GitCompare className="w-4 h-4 mr-2" />
            Diff
          </TabsTrigger>
        </TabsList>

        <TabsContent value="browse" className="space-y-3">
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-full max-w-md">
                <Input
                  value={artifactFilter}
                  onChange={(e) => setArtifactFilter(e.target.value)}
                  placeholder="Filter by artifact_id…"
                />
              </div>
              <div className="text-xs text-muted-foreground">
                {indexLoading ? "Loading…" : `${filteredItems.length} artifact_id(s)`}
              </div>
            </div>

            {indexError && (
              <div className="mt-3 text-sm text-destructive">
                Failed to load artifact index: {(indexError as Error).message}
              </div>
            )}

            {!indexLoading && filteredItems.length === 0 && (
              <div className="mt-4 text-sm text-muted-foreground">
                No JSON artifacts found yet. Place dashboard artifacts under{" "}
                <span className="font-mono">{index?.root_dir ?? "out/"}</span> (or set{" "}
                <span className="font-mono">ABRAXAS_ARTIFACT_DIR</span>).
              </div>
            )}

            {filteredItems.length > 0 && (
              <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-3">
                <div className="border rounded p-3">
                  <div className="text-sm font-medium mb-2">Artifact Browser</div>
                  <ScrollArea className="h-[360px] pr-3">
                    <div className="space-y-2">
                      {filteredItems.map((it) => {
                        const missing = it.status_flags?.missing_inputs;
                        const notComputable = it.status_flags?.not_computable;
                        return (
                          <button
                            key={it.artifact_id}
                            type="button"
                            className={[
                              "w-full text-left rounded border p-3 hover:bg-muted/40",
                              selectedArtifactId === it.artifact_id ? "bg-muted/40 border-primary/40" : "",
                            ].join(" ")}
                            onClick={() => {
                              setSelectedArtifactId(it.artifact_id);
                              setSelectedPointer("");
                            }}
                          >
                            <div className="flex items-center justify-between gap-2">
                              <div className="font-mono text-sm">{it.artifact_id}</div>
                              <div className="flex items-center gap-2">
                                {it.available.envelope && <Badge variant="secondary">envelope</Badge>}
                                {it.available.narrative && <Badge variant="secondary">narrative</Badge>}
                                {missing && <Badge variant="destructive">missing_inputs</Badge>}
                                {notComputable && <Badge variant="destructive">not_computable</Badge>}
                              </div>
                            </div>
                            <div className="mt-1 text-xs text-muted-foreground">
                              created_at: {it.created_at ?? "(unknown)"} · schema: {it.schema_version ?? "(unknown)"}
                            </div>
                            {it.tags?.length ? (
                              <div className="mt-1 text-xs text-muted-foreground">tags: {it.tags.join(", ")}</div>
                            ) : null}
                          </button>
                        );
                      })}
                    </div>
                  </ScrollArea>
                </div>

                <div className="border rounded p-3">
                  <div className="text-sm font-medium mb-2">Viewer</div>
                  {!selectedEntry && (
                    <div className="text-sm text-muted-foreground">Select an artifact_id to view envelope/narrative.</div>
                  )}

                  {selectedEntry && (
                    <ResizablePanelGroup direction="horizontal" className="h-[360px] border rounded">
                      <ResizablePanel defaultSize={55} minSize={25}>
                        <div className="h-full flex flex-col">
                          <div className="px-3 py-2 border-b flex items-center justify-between">
                            <div className="text-xs font-medium">Envelope JSON</div>
                            <div className="text-[10px] text-muted-foreground font-mono">
                              {selectedPointer ? `selected: ${selectedPointer}` : ""}
                            </div>
                          </div>
                          <ScrollArea className="flex-1 p-2">
                            {envelope ? (
                              <JsonTree
                                value={envelope}
                                selectedPointer={selectedPointer}
                                onSelectPointer={setSelectedPointer}
                              />
                            ) : (
                              <div className="text-sm text-muted-foreground">
                                Envelope not available for this artifact_id.
                              </div>
                            )}
                          </ScrollArea>
                        </div>
                      </ResizablePanel>
                      <ResizableHandle withHandle />
                      <ResizablePanel defaultSize={45} minSize={25}>
                        <div className="h-full flex flex-col">
                          <div className="px-3 py-2 border-b flex items-center justify-between">
                            <div className="text-xs font-medium">Key Panels</div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setSelectedPointer(findFirstPointerByKey(envelope ?? null, "provenance") ?? "")}
                              disabled={!envelope}
                            >
                              provenance
                            </Button>
                          </div>
                          <ScrollArea className="flex-1 p-3">
                            <div className="space-y-4">
                              {envelopePanels.length === 0 && (
                                <div className="text-sm text-muted-foreground">
                                  No known panel pointers found (signal_scores/motifs/clusters/constraints/provenance).
                                </div>
                              )}
                              {envelopePanels.map((p) => (
                                <div key={p.key} className="space-y-2">
                                  <div className="flex items-center justify-between">
                                    <div className="text-sm font-medium">{p.key}</div>
                                    <Button
                                      size="sm"
                                      variant="secondary"
                                      onClick={() => setSelectedPointer(p.pointer as string)}
                                    >
                                      jump
                                    </Button>
                                  </div>
                                  <div className="text-[10px] text-muted-foreground font-mono">{p.pointer}</div>
                                  {p.pointer ? (() => {
                                    const got = getAtPointer(envelope ?? null, p.pointer);
                                    if (!got.ok) return <div className="text-sm text-muted-foreground">Pointer not resolvable.</div>;
                                    return <CompactJson value={got.value ?? null} />;
                                  })() : null}
                                </div>
                              ))}

                              <div className="border-t pt-4">
                                <div className="text-sm font-medium mb-2">Narrative</div>
                                {narrative ? (
                                  <div className="space-y-3">
                                    <div className="text-sm">
                                      <span className="text-muted-foreground">headline: </span>
                                      <span className="font-medium">
                                        {isObject(narrative) && typeof narrative["headline"] === "string"
                                          ? (narrative["headline"] as string)
                                          : "(missing)"}
                                      </span>
                                    </div>

                                    {isObject(narrative) && Array.isArray(narrative["signal_summary"]) && (
                                      <div>
                                        <div className="text-xs font-medium mb-1">signal_summary</div>
                                        <div className="space-y-1">
                                          {(narrative["signal_summary"] as JsonValue[]).slice(0, 50).map((s, idx) => {
                                            const ptr =
                                              isObject(s) && typeof s["pointer"] === "string" ? (s["pointer"] as string) : "";
                                            return (
                                              <button
                                                key={`ss:${idx}`}
                                                className="w-full text-left text-xs font-mono rounded px-2 py-1 hover:bg-muted/40"
                                                onClick={() => {
                                                  if (ptr) setSelectedPointer(ptr);
                                                }}
                                                title={ptr ? `jump ${ptr}` : "no pointer"}
                                              >
                                                {stableStringify(s, 0)}
                                              </button>
                                            );
                                          })}
                                        </div>
                                      </div>
                                    )}

                                    {isObject(narrative) && Array.isArray(narrative["motifs"]) && (
                                      <div>
                                        <div className="text-xs font-medium mb-1">motifs</div>
                                        <div className="flex flex-wrap gap-2">
                                          {(narrative["motifs"] as JsonValue[]).slice(0, 50).map((m, idx) => (
                                            <Badge key={`m:${idx}`} variant="secondary" className="font-mono">
                                              {typeof m === "string" ? m : stableStringify(m, 0)}
                                            </Badge>
                                          ))}
                                        </div>
                                      </div>
                                    )}

                                    {isObject(narrative) && Array.isArray(narrative["what_changed"]) && (
                                      <div>
                                        <div className="text-xs font-medium mb-1">what_changed</div>
                                        <div className="space-y-1">
                                          {(narrative["what_changed"] as JsonValue[]).slice(0, 50).map((w, idx) => (
                                            <div key={`wc:${idx}`} className="text-xs font-mono bg-muted/30 border rounded p-2">
                                              {stableStringify(w, 0)}
                                            </div>
                                          ))}
                                        </div>
                                      </div>
                                    )}

                                    {isObject(narrative) && narrative["constraints_report"] && (
                                      <div>
                                        <div className="text-xs font-medium mb-1">constraints_report</div>
                                        <CompactJson value={narrative["constraints_report"] ?? null} />
                                      </div>
                                    )}
                                  </div>
                                ) : (
                                  <div className="text-sm text-muted-foreground">
                                    Narrative not available for this artifact_id.
                                  </div>
                                )}
                              </div>
                            </div>
                          </ScrollArea>
                        </div>
                      </ResizablePanel>
                    </ResizablePanelGroup>
                  )}
                </div>
              </div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="drift" className="space-y-3">
          <Card className="p-4 space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <div className="text-sm font-medium">Drift Reports</div>
              <Select value={driftId} onValueChange={setDriftId}>
                <SelectTrigger className="w-[420px]">
                  <SelectValue placeholder="Select drift_report_v1 artifact_id…" />
                </SelectTrigger>
                <SelectContent>
                  {(driftIndex?.items ?? []).map((it) => (
                    <SelectItem key={it.artifact_id} value={it.artifact_id}>
                      {it.artifact_id}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="text-xs text-muted-foreground">
                {(driftIndex?.items ?? []).length} report(s)
              </div>
            </div>

            {!driftId && <div className="text-sm text-muted-foreground">Select a drift report to inspect clusters.</div>}

            {driftId && (
              <ResizablePanelGroup direction="horizontal" className="h-[520px] border rounded">
                <ResizablePanel defaultSize={40} minSize={25}>
                  <div className="h-full flex flex-col">
                    <div className="px-3 py-2 border-b text-xs font-medium">Clusters</div>
                    <ScrollArea className="flex-1 p-2">
                      {driftClusters.length === 0 && (
                        <div className="text-sm text-muted-foreground">No clusters found in this drift report.</div>
                      )}
                      <div className="space-y-2">
                        {driftClusters.map((c, idx) => {
                          const strength =
                            isObject(c) && typeof c["strength_score"] === "number" ? (c["strength_score"] as number) : undefined;
                          const conf =
                            isObject(c) && typeof c["confidence"] === "number" ? (c["confidence"] as number) : undefined;
                          const name =
                            isObject(c) && typeof c["cluster_id"] === "string"
                              ? (c["cluster_id"] as string)
                              : isObject(c) && typeof c["name"] === "string"
                                ? (c["name"] as string)
                                : `cluster_${idx}`;
                          return (
                            <div key={`cluster:${idx}`} className="border rounded p-3">
                              <div className="flex items-center justify-between gap-2">
                                <div className="font-mono text-sm">{name}</div>
                                <div className="flex items-center gap-2">
                                  {typeof strength === "number" && <Badge variant="secondary">strength={strength.toFixed(3)}</Badge>}
                                  {typeof conf === "number" && <Badge variant="secondary">conf={conf.toFixed(3)}</Badge>}
                                </div>
                              </div>
                              <div className="mt-2 space-y-2">
                                {isObject(c) && Array.isArray(c["shared_motifs"]) && (
                                  <div>
                                    <div className="text-xs font-medium mb-1">shared_motifs</div>
                                    <div className="flex flex-wrap gap-2">
                                      {(c["shared_motifs"] as JsonValue[]).slice(0, 20).map((m, mi) => (
                                        <Badge key={`sm:${idx}:${mi}`} variant="secondary" className="font-mono">
                                          {typeof m === "string" ? m : stableStringify(m, 0)}
                                        </Badge>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {isObject(c) && Array.isArray(c["domains_involved"]) && (
                                  <div>
                                    <div className="text-xs font-medium mb-1">domains_involved</div>
                                    <div className="flex flex-wrap gap-2">
                                      {(c["domains_involved"] as JsonValue[]).slice(0, 20).map((d, di) => (
                                        <Badge key={`di:${idx}:${di}`} variant="outline" className="font-mono">
                                          {typeof d === "string" ? d : stableStringify(d, 0)}
                                        </Badge>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {isObject(c) && Array.isArray(c["evidence_refs"]) && (
                                  <div>
                                    <div className="text-xs font-medium mb-1">evidence_refs</div>
                                    <div className="space-y-1">
                                      {(c["evidence_refs"] as JsonValue[]).slice(0, 50).map((r, ri) => {
                                        const aid =
                                          isObject(r) && typeof r["artifact_id"] === "string" ? (r["artifact_id"] as string) : "";
                                        const ptr =
                                          isObject(r) && typeof r["pointer"] === "string" ? (r["pointer"] as string) : "";
                                        return (
                                          <button
                                            key={`ref:${idx}:${ri}`}
                                            className="w-full text-left text-xs font-mono rounded border px-2 py-1 hover:bg-muted/40"
                                            onClick={() => {
                                              if (!aid) return;
                                              setSelectedArtifactId(aid);
                                              setSelectedPointer(ptr || "");
                                            }}
                                            title={aid ? `open ${aid}${ptr ? ` @ ${ptr}` : ""}` : "invalid evidence ref"}
                                          >
                                            {aid || "(missing artifact_id)"} {ptr ? ` ${ptr}` : ""}
                                          </button>
                                        );
                                      })}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </ScrollArea>
                  </div>
                </ResizablePanel>
                <ResizableHandle withHandle />
                <ResizablePanel defaultSize={60} minSize={25}>
                  <div className="h-full flex flex-col">
                    <div className="px-3 py-2 border-b flex items-center justify-between">
                      <div className="text-xs font-medium">Envelope (evidence target)</div>
                      <div className="text-[10px] text-muted-foreground font-mono">
                        {selectedArtifactId ? selectedArtifactId : "(select evidence ref)"}
                      </div>
                    </div>
                    <ScrollArea className="flex-1 p-2">
                      {selectedArtifactId && envelope ? (
                        <JsonTree value={envelope} selectedPointer={selectedPointer} onSelectPointer={setSelectedPointer} />
                      ) : (
                        <div className="text-sm text-muted-foreground">
                          Click an evidence_ref to open its referenced artifact and jump to the pointer target.
                        </div>
                      )}
                    </ScrollArea>
                  </div>
                </ResizablePanel>
              </ResizablePanelGroup>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="diff" className="space-y-3">
          <Card className="p-4 space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <div className="text-sm font-medium">Select two artifact_ids</div>
              <Select value={diffA} onValueChange={setDiffA}>
                <SelectTrigger className="w-[360px]">
                  <SelectValue placeholder="Artifact A" />
                </SelectTrigger>
                <SelectContent>
                  {artifactIds.map((id) => (
                    <SelectItem key={`a:${id}`} value={id}>
                      {id}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={diffB} onValueChange={setDiffB}>
                <SelectTrigger className="w-[360px]">
                  <SelectValue placeholder="Artifact B" />
                </SelectTrigger>
                <SelectContent>
                  {artifactIds.map((id) => (
                    <SelectItem key={`b:${id}`} value={id}>
                      {id}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                variant="secondary"
                onClick={() => {
                  setDiffA(diffB);
                  setDiffB(diffA);
                }}
                disabled={!diffA || !diffB}
              >
                swap
              </Button>
            </div>

            <ResizablePanelGroup direction="horizontal" className="h-[520px] border rounded">
              <ResizablePanel defaultSize={50} minSize={25}>
                <div className="h-full flex flex-col">
                  <div className="px-3 py-2 border-b text-xs font-medium">Envelope diff (pointer changes)</div>
                  <ScrollArea className="flex-1 p-2">
                    {!diffEnvelopeA || !diffEnvelopeB ? (
                      <div className="text-sm text-muted-foreground">
                        Envelope(s) missing for selected artifact(s).
                      </div>
                    ) : envelopeDiff.length === 0 ? (
                      <div className="text-sm text-muted-foreground">No differences detected.</div>
                    ) : (
                      <div className="space-y-2">
                        {envelopeDiff.slice(0, 500).map((d) => (
                          <div key={`ed:${d.pointer}`} className="border rounded p-2">
                            <div className="flex items-center justify-between gap-2">
                              <div className="text-xs font-mono">{d.pointer || "/"}</div>
                              <Badge variant={d.type === "changed" ? "secondary" : "outline"}>{d.type}</Badge>
                            </div>
                            {"before" in d && (
                              <div className="mt-1 text-[11px] font-mono text-muted-foreground break-words">
                                - {stableStringify(d.before, 0)}
                              </div>
                            )}
                            {"after" in d && (
                              <div className="mt-1 text-[11px] font-mono text-muted-foreground break-words">
                                + {stableStringify(d.after, 0)}
                              </div>
                            )}
                          </div>
                        ))}
                        {envelopeDiff.length > 500 && (
                          <div className="text-xs text-muted-foreground">Truncated to 500 entries.</div>
                        )}
                      </div>
                    )}
                  </ScrollArea>
                </div>
              </ResizablePanel>
              <ResizableHandle withHandle />
              <ResizablePanel defaultSize={50} minSize={25}>
                <div className="h-full flex flex-col">
                  <div className="px-3 py-2 border-b text-xs font-medium">Narrative diff (what_changed + raw)</div>
                  <ScrollArea className="flex-1 p-3">
                    {!diffNarrativeA || !diffNarrativeB ? (
                      <div className="text-sm text-muted-foreground">
                        Narrative(s) missing for selected artifact(s).
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {isObject(diffNarrativeB) && Array.isArray(diffNarrativeB["what_changed"]) && (
                          <div>
                            <div className="text-sm font-medium mb-2">what_changed (B)</div>
                            <div className="space-y-2">
                              {(diffNarrativeB["what_changed"] as JsonValue[]).slice(0, 100).map((w, idx) => (
                                <div key={`wcb:${idx}`} className="text-xs font-mono bg-muted/30 border rounded p-2">
                                  {stableStringify(w, 0)}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        <div>
                          <div className="text-sm font-medium mb-2">Narrative pointer diff</div>
                          {narrativeDiff.length === 0 ? (
                            <div className="text-sm text-muted-foreground">No differences detected.</div>
                          ) : (
                            <div className="space-y-2">
                              {narrativeDiff.slice(0, 300).map((d) => (
                                <div key={`nd:${d.pointer}`} className="border rounded p-2">
                                  <div className="flex items-center justify-between gap-2">
                                    <div className="text-xs font-mono">{d.pointer || "/"}</div>
                                    <Badge variant={d.type === "changed" ? "secondary" : "outline"}>{d.type}</Badge>
                                  </div>
                                  {"before" in d && (
                                    <div className="mt-1 text-[11px] font-mono text-muted-foreground break-words">
                                      - {stableStringify(d.before, 0)}
                                    </div>
                                  )}
                                  {"after" in d && (
                                    <div className="mt-1 text-[11px] font-mono text-muted-foreground break-words">
                                      + {stableStringify(d.after, 0)}
                                    </div>
                                  )}
                                </div>
                              ))}
                              {narrativeDiff.length > 300 && (
                                <div className="text-xs text-muted-foreground">Truncated to 300 entries.</div>
                              )}
                            </div>
                          )}
                        </div>

                        <div>
                          <div className="text-sm font-medium mb-2">Raw (canonical) narrative JSON</div>
                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                            <div>
                              <div className="text-xs text-muted-foreground mb-1">A</div>
                              <CompactJson value={diffNarrativeA} />
                            </div>
                            <div>
                              <div className="text-xs text-muted-foreground mb-1">B</div>
                              <CompactJson value={diffNarrativeB} />
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </ScrollArea>
                </div>
              </ResizablePanel>
            </ResizablePanelGroup>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

