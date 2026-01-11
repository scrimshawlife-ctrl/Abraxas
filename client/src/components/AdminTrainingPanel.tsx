import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

const todayISO = () => new Date().toISOString().slice(0, 10);

type CandidatePayload = Record<string, unknown>;

export default function AdminTrainingPanel() {
  const [day, setDay] = useState(todayISO());
  const [rootPath, setRootPath] = useState("");
  const [ingestKind, setIngestKind] = useState("note");
  const [ingestDomain, setIngestDomain] = useState("game_theory");
  const [ingestTags, setIngestTags] = useState("zero_sum,nash");
  const [ingestText, setIngestText] = useState("Nash equilibrium basics...");
  const [ingestSource, setIngestSource] = useState("");
  const [category, setCategory] = useState("terms");
  const [itemJson, setItemJson] = useState("{\n  \"term\": \"example\",\n  \"notes\": \"why this matters\"\n}");
  const [ingest, setIngest] = useState<Record<string, unknown>[]>([]);
  const [candidates, setCandidates] = useState<Record<string, unknown> | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const parsedItem = useMemo(() => {
    try {
      return JSON.parse(itemJson) as CandidatePayload;
    } catch (err) {
      return null;
    }
  }, [itemJson]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (rootPath) {
        params.set("root", rootPath);
      }
      const query = params.toString() ? `?${params.toString()}` : "";
      const [ingestRes, candidatesRes, healthRes] = await Promise.all([
        fetch(`/admin/kite/${day}/ingest${query}`),
        fetch(`/admin/kite/${day}/candidates${query}`),
        fetch(`/admin/health${query}`),
      ]);

      if (!healthRes.ok) {
        throw new Error("Admin access denied or admin panel unavailable.");
      }

      const ingestJson = await ingestRes.json();
      const candidatesJson = await candidatesRes.json();
      setIngest((ingestJson.ingest as Record<string, unknown>[]) || []);
      setCandidates(candidatesJson.candidates || null);
      setStatus("Admin panel online.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load admin data.");
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }, [day, rootPath]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSubmit = async () => {
    if (!parsedItem) {
      setError("Item JSON is invalid.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/admin/kite/candidates", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ category, item: parsedItem, day, root: rootPath || undefined }),
      });
      if (!res.ok) {
        throw new Error("Failed to append candidate.");
      }
      const json = await res.json();
      setCandidates(json.candidates || null);
      setStatus("Candidate appended.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to append candidate.");
    } finally {
      setLoading(false);
    }
  };

  const handleIngest = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/kite/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kind: ingestKind,
          domain: ingestDomain,
          tags: ingestTags.split(",").map((tag) => tag.trim()).filter(Boolean),
          text: ingestText,
          source: ingestSource || undefined,
          day,
          root: rootPath || undefined,
        }),
      });
      if (!res.ok) {
        throw new Error("Failed to ingest training note.");
      }
      setStatus("KITE ingest saved.");
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to ingest training note.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-4">
        <div className="space-y-2">
          <label className="text-sm font-medium text-muted-foreground">Run Day</label>
          <Input type="date" value={day} onChange={(event) => setDay(event.target.value)} />
        </div>
        <div className="space-y-2 min-w-[240px]">
          <label className="text-sm font-medium text-muted-foreground">Storage Root</label>
          <Input
            placeholder="~/.abraxas (optional)"
            value={rootPath}
            onChange={(event) => setRootPath(event.target.value)}
          />
        </div>
        <Button onClick={fetchData} disabled={loading}>
          Refresh
        </Button>
      </div>

      {status && (
        <Alert>
          <AlertTitle>Status</AlertTitle>
          <AlertDescription>{status}</AlertDescription>
        </Alert>
      )}
      {error && (
        <Alert variant="destructive">
          <AlertTitle>Issue</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>KITE Ingest</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground">Kind</label>
              <select
                className="w-full rounded border border-border bg-background px-3 py-2 text-sm"
                value={ingestKind}
                onChange={(event) => setIngestKind(event.target.value)}
              >
                <option value="note">Note</option>
                <option value="link">Link</option>
                <option value="transcript">Transcript</option>
                <option value="dataset">Dataset</option>
                <option value="snippet">Snippet</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-muted-foreground">Domain</label>
              <Input value={ingestDomain} onChange={(event) => setIngestDomain(event.target.value)} />
            </div>
            <div className="space-y-2 md:col-span-2">
              <label className="text-sm font-medium text-muted-foreground">Tags</label>
              <Input value={ingestTags} onChange={(event) => setIngestTags(event.target.value)} />
            </div>
            <div className="space-y-2 md:col-span-2">
              <label className="text-sm font-medium text-muted-foreground">Source (optional)</label>
              <Input value={ingestSource} onChange={(event) => setIngestSource(event.target.value)} />
            </div>
            <div className="space-y-2 md:col-span-2">
              <label className="text-sm font-medium text-muted-foreground">Text</label>
              <Textarea
                value={ingestText}
                onChange={(event) => setIngestText(event.target.value)}
                className="min-h-[140px]"
              />
            </div>
          </div>
          <Button onClick={handleIngest} disabled={loading}>
            Ingest Note
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>KITE Ingest Log</CardTitle>
        </CardHeader>
        <CardContent>
          {ingest.length === 0 ? (
            <p className="text-sm text-muted-foreground">No ingests logged for this day.</p>
          ) : (
            <div className="space-y-2 text-sm">
              {ingest.map((entry, index) => (
                <div key={`${index}-${entry.schema}`} className="rounded border border-border p-3">
                  <pre className="whitespace-pre-wrap text-xs text-muted-foreground">
                    {JSON.stringify(entry, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>KITE Candidate Queue</CardTitle>
        </CardHeader>
        <CardContent>
          {candidates ? (
            <pre className="whitespace-pre-wrap text-xs text-muted-foreground">
              {JSON.stringify(candidates, null, 2)}
            </pre>
          ) : (
            <p className="text-sm text-muted-foreground">No candidates loaded.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Append Candidate</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-muted-foreground">Category</label>
            <select
              className="w-full rounded border border-border bg-background px-3 py-2 text-sm"
              value={category}
              onChange={(event) => setCategory(event.target.value)}
            >
              <option value="terms">Terms</option>
              <option value="metrics">Metrics</option>
              <option value="overlays">Overlays</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-muted-foreground">Item JSON</label>
            <Textarea
              value={itemJson}
              onChange={(event) => setItemJson(event.target.value)}
              className="min-h-[160px] font-mono text-xs"
            />
          </div>
          <Button onClick={handleSubmit} disabled={loading}>
            Append Candidate
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
