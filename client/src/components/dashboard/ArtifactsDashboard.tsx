import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { AalCard, AalDivider, AalButton, AalTag } from "../../../../aal-ui-kit/src";
import { jsonPointerGet } from "./pointer";

type ArtifactIndexItem = {
  artifact_id: string;
  created_at: string;
  envelope_path: string | null;
  narrative_path: string | null;
  missing_inputs_count: number;
  not_computable_count: number;
};

type DriftIndexItem = {
  report_id: string;
  created_at: string;
  path: string;
  cluster_count: number;
};

type PointerDiffChange = {
  pointer: string;
  before: unknown;
  after: unknown;
};

type DiffResponse = {
  kind: "envelope" | "narrative";
  left: string;
  right: string;
  changes: PointerDiffChange[];
};

async function getJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return (await res.json()) as T;
}

function JsonBlock({ value, title, highlightPointer }: { value: unknown; title: string; highlightPointer?: string }) {
  const highlightedValue = useMemo(() => {
    if (!highlightPointer) return undefined;
    try {
      return jsonPointerGet(value, highlightPointer);
    } catch {
      return undefined;
    }
  }, [value, highlightPointer]);

  return (
    <AalCard>
      <div className="aal-stack-md">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
          <div className="aal-heading-sm">{title}</div>
          {highlightPointer ? (
            <AalTag>{highlightPointer}</AalTag>
          ) : (
            <AalTag>no pointer selected</AalTag>
          )}
        </div>

        {highlightPointer ? (
          <div className="aal-body" style={{ fontSize: 12, opacity: 0.85 }}>
            <span style={{ opacity: 0.65 }}>Value at pointer:</span>{" "}
            <code style={{ wordBreak: "break-word" }}>{JSON.stringify(highlightedValue)}</code>
          </div>
        ) : null}

        <pre
          className="aal-body"
          style={{
            fontSize: 12,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            maxHeight: 420,
            overflow: "auto",
            background: "rgba(0,0,0,0.18)",
            padding: 12,
            borderRadius: 12,
          }}
        >
          {JSON.stringify(value, null, 2)}
        </pre>
      </div>
    </AalCard>
  );
}

export default function ArtifactsDashboard() {
  const [selectedArtifactId, setSelectedArtifactId] = useState<string>("");
  const [diffLeft, setDiffLeft] = useState<string>("");
  const [diffRight, setDiffRight] = useState<string>("");
  const [diffKind, setDiffKind] = useState<"envelope" | "narrative">("envelope");
  const [selectedPointer, setSelectedPointer] = useState<string>("");

  const artifactsQuery = useQuery({
    queryKey: ["/api/artifacts"],
    queryFn: () => getJSON<ArtifactIndexItem[]>("/api/artifacts"),
  });

  const driftQuery = useQuery({
    queryKey: ["/api/drift_reports"],
    queryFn: () => getJSON<DriftIndexItem[]>("/api/drift_reports"),
  });

  const artifactIds = useMemo(() => (artifactsQuery.data || []).map((a) => a.artifact_id), [artifactsQuery.data]);

  const envelopeQuery = useQuery({
    queryKey: ["/api/artifacts", selectedArtifactId, "envelope"],
    queryFn: () => getJSON<unknown>(`/api/artifacts/${encodeURIComponent(selectedArtifactId)}/envelope`),
    enabled: Boolean(selectedArtifactId),
  });

  const narrativeQuery = useQuery({
    queryKey: ["/api/artifacts", selectedArtifactId, "narrative"],
    queryFn: () => getJSON<unknown>(`/api/artifacts/${encodeURIComponent(selectedArtifactId)}/narrative`),
    enabled: Boolean(selectedArtifactId),
  });

  const diffQuery = useQuery({
    queryKey: ["/api/diff", diffKind, diffLeft, diffRight],
    queryFn: () =>
      getJSON<DiffResponse>(
        `/api/diff?kind=${encodeURIComponent(diffKind)}&left=${encodeURIComponent(diffLeft)}&right=${encodeURIComponent(
          diffRight
        )}`
      ),
    enabled: Boolean(diffLeft && diffRight),
  });

  const canDiff = Boolean(diffLeft && diffRight && diffLeft !== diffRight);

  const handleRescan = async () => {
    await getJSON<{ ok: true }>("/api/rescan");
    await artifactsQuery.refetch();
    await driftQuery.refetch();
  };

  return (
    <div className="aal-stack-lg">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
        <div>
          <div className="aal-heading-lg">Artifacts Dashboard</div>
          <div className="aal-body" style={{ opacity: 0.75 }}>
            Read-only index over <code>out/</code> with JSON Pointer diffs.
          </div>
        </div>

        <AalButton variant="secondary" onClick={handleRescan}>
          Rescan out/
        </AalButton>
      </div>

      <AalDivider />

      <AalCard>
        <div className="aal-stack-md">
          <div className="aal-heading-sm">Artifacts</div>

          {artifactsQuery.isLoading ? <div className="aal-body">Loading…</div> : null}
          {artifactsQuery.error ? (
            <div className="aal-body" style={{ color: "var(--aal-color-magenta)" }}>
              Failed to load artifacts: {String(artifactsQuery.error)}
            </div>
          ) : null}

          <div className="aal-row-md" style={{ flexWrap: "wrap" }}>
            <label className="aal-body" style={{ minWidth: 120, opacity: 0.75 }}>
              Inspect
            </label>
            <select
              className="aal-input"
              value={selectedArtifactId}
              onChange={(e) => {
                setSelectedPointer("");
                setSelectedArtifactId(e.target.value);
              }}
              style={{ minWidth: 320 }}
            >
              <option value="">(select artifact)</option>
              {artifactIds.map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
            <AalTag>{artifactIds.length} total</AalTag>
          </div>

          {selectedArtifactId ? (
            <div className="aal-body" style={{ fontSize: 12, opacity: 0.75 }}>
              Tip: use the Diff section below to click a pointer and highlight a field.
            </div>
          ) : null}
        </div>
      </AalCard>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <JsonBlock
          title={`Envelope ${selectedArtifactId ? `(${selectedArtifactId})` : ""}`}
          value={envelopeQuery.data ?? (selectedArtifactId ? { error: "Envelope not found" } : {})}
          highlightPointer={selectedPointer}
        />
        <JsonBlock
          title={`Narrative ${selectedArtifactId ? `(${selectedArtifactId})` : ""}`}
          value={narrativeQuery.data ?? (selectedArtifactId ? { error: "Narrative not found" } : {})}
          highlightPointer={selectedPointer}
        />
      </div>

      <AalDivider />

      <AalCard>
        <div className="aal-stack-md">
          <div className="aal-heading-sm">Drift reports</div>

          {driftQuery.isLoading ? <div className="aal-body">Loading…</div> : null}
          {driftQuery.error ? (
            <div className="aal-body" style={{ color: "var(--aal-color-magenta)" }}>
              Failed to load drift reports: {String(driftQuery.error)}
            </div>
          ) : null}

          <div style={{ display: "grid", gap: 8 }}>
            {(driftQuery.data || []).slice(0, 20).map((d) => (
              <div key={d.report_id} className="aal-body" style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                <code>{d.report_id}</code>
                <span style={{ opacity: 0.6 }}>{d.cluster_count} clusters</span>
                <span style={{ opacity: 0.6 }}>{d.path}</span>
              </div>
            ))}
            {(driftQuery.data || []).length > 20 ? (
              <div className="aal-body" style={{ opacity: 0.6 }}>
                Showing first 20.
              </div>
            ) : null}
            {(driftQuery.data || []).length === 0 ? (
              <div className="aal-body" style={{ opacity: 0.6 }}>
                No drift reports detected in <code>out/</code>.
              </div>
            ) : null}
          </div>
        </div>
      </AalCard>

      <AalDivider />

      <AalCard>
        <div className="aal-stack-md">
          <div className="aal-heading-sm">Diff (JSON Pointer)</div>

          <div className="aal-row-md" style={{ flexWrap: "wrap" }}>
            <label className="aal-body" style={{ minWidth: 120, opacity: 0.75 }}>
              Kind
            </label>
            <select className="aal-input" value={diffKind} onChange={(e) => setDiffKind(e.target.value as any)}>
              <option value="envelope">envelope</option>
              <option value="narrative">narrative</option>
            </select>
          </div>

          <div className="aal-row-md" style={{ flexWrap: "wrap" }}>
            <label className="aal-body" style={{ minWidth: 120, opacity: 0.75 }}>
              Left
            </label>
            <select className="aal-input" value={diffLeft} onChange={(e) => setDiffLeft(e.target.value)} style={{ minWidth: 320 }}>
              <option value="">(select)</option>
              {artifactIds.map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
          </div>

          <div className="aal-row-md" style={{ flexWrap: "wrap" }}>
            <label className="aal-body" style={{ minWidth: 120, opacity: 0.75 }}>
              Right
            </label>
            <select className="aal-input" value={diffRight} onChange={(e) => setDiffRight(e.target.value)} style={{ minWidth: 320 }}>
              <option value="">(select)</option>
              {artifactIds.map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
            {!canDiff && diffLeft && diffRight ? (
              <AalTag>pick two different ids</AalTag>
            ) : null}
          </div>

          {diffQuery.isLoading ? <div className="aal-body">Computing diff…</div> : null}
          {diffQuery.error ? (
            <div className="aal-body" style={{ color: "var(--aal-color-magenta)" }}>
              Diff failed: {String(diffQuery.error)}
            </div>
          ) : null}

          {diffQuery.data ? (
            <div className="aal-stack-md">
              <div className="aal-body" style={{ opacity: 0.75 }}>
                {diffQuery.data.changes.length} change(s). Click a pointer to highlight it in the JSON panels above.
              </div>

              <div style={{ display: "grid", gap: 8 }}>
                {diffQuery.data.changes.slice(0, 200).map((c) => (
                  <button
                    key={c.pointer}
                    onClick={() => setSelectedPointer(c.pointer)}
                    className="aal-body"
                    style={{
                      textAlign: "left",
                      padding: 10,
                      borderRadius: 12,
                      background: selectedPointer === c.pointer ? "rgba(0,255,255,0.12)" : "rgba(255,255,255,0.04)",
                      border: "1px solid rgba(255,255,255,0.08)",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                      <code>{c.pointer || "(root)"}</code>
                      <span style={{ opacity: 0.6 }}>select</span>
                    </div>
                    <div style={{ fontSize: 12, opacity: 0.8 }}>
                      <span style={{ opacity: 0.6 }}>before:</span> <code>{JSON.stringify(c.before)}</code>
                    </div>
                    <div style={{ fontSize: 12, opacity: 0.8 }}>
                      <span style={{ opacity: 0.6 }}>after:</span> <code>{JSON.stringify(c.after)}</code>
                    </div>
                  </button>
                ))}
                {diffQuery.data.changes.length > 200 ? (
                  <div className="aal-body" style={{ opacity: 0.6 }}>
                    Showing first 200 changes.
                  </div>
                ) : null}
              </div>
            </div>
          ) : (
            <div className="aal-body" style={{ opacity: 0.6 }}>
              Choose left/right to compute a diff.
            </div>
          )}
        </div>
      </AalCard>
    </div>
  );
}

