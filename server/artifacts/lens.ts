import path from "node:path";
import fs from "node:fs/promises";

export type ArtifactKind =
  | "oracle_envelope_v2"
  | "narrative_bundle_v1"
  | "drift_report_v1"
  | "unknown";

export type ArtifactStatusFlags = {
  missing_inputs?: boolean;
  not_computable?: boolean;
};

export type ArtifactIndexItem = {
  artifact_id: string;
  kind: ArtifactKind;
  relative_path: string;
  filename: string;
  created_at?: string;
  schema_version?: string;
  tags?: string[];
  status_flags?: ArtifactStatusFlags;
};

export type ArtifactIndexEntry = {
  artifact_id: string;
  created_at?: string;
  schema_version?: string;
  tags?: string[];
  status_flags?: ArtifactStatusFlags;
  available: {
    envelope: boolean;
    narrative: boolean;
  };
  files: ArtifactIndexItem[];
};

export type ArtifactIndex = {
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

const KNOWN_KINDS: ArtifactKind[] = [
  "oracle_envelope_v2",
  "narrative_bundle_v1",
  "drift_report_v1",
];

function inferKindFromName(name: string): ArtifactKind {
  const lower = name.toLowerCase();
  for (const kind of KNOWN_KINDS) {
    if (lower.includes(kind)) return kind;
  }
  return "unknown";
}

function safeIsoFromDate(d: Date): string {
  // Always emit UTC ISO; deterministic for a given Date.
  return d.toISOString();
}

function extractArtifactId(
  parsed: JsonValue,
  fallbackFromFilename: string,
): string {
  if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
    const obj = parsed as Record<string, JsonValue>;
    const direct = obj["artifact_id"];
    if (typeof direct === "string" && direct.trim()) return direct;

    const meta = obj["meta"];
    if (meta && typeof meta === "object" && !Array.isArray(meta)) {
      const metaId = (meta as Record<string, JsonValue>)["artifact_id"];
      if (typeof metaId === "string" && metaId.trim()) return metaId;
    }

    const prov = obj["provenance"];
    if (prov && typeof prov === "object" && !Array.isArray(prov)) {
      const provId = (prov as Record<string, JsonValue>)["artifact_id"];
      if (typeof provId === "string" && provId.trim()) return provId;
    }
  }

  // Try `<artifact_id>__<kind>.json` style.
  const m = fallbackFromFilename.match(
    /^(.+?)__(oracle_envelope_v2|narrative_bundle_v1|drift_report_v1)(?:\..*)?\.json$/i,
  );
  if (m?.[1]) return m[1];

  // Last resort: strip extension.
  return fallbackFromFilename.replace(/\.json$/i, "");
}

function extractCreatedAt(parsed: JsonValue): string | undefined {
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return;
  const obj = parsed as Record<string, JsonValue>;
  const direct = obj["created_at"];
  if (typeof direct === "string" && direct.trim()) return direct;

  const meta = obj["meta"];
  if (meta && typeof meta === "object" && !Array.isArray(meta)) {
    const metaCreated = (meta as Record<string, JsonValue>)["created_at"];
    if (typeof metaCreated === "string" && metaCreated.trim()) return metaCreated;
  }

  const prov = obj["provenance"];
  if (prov && typeof prov === "object" && !Array.isArray(prov)) {
    const provCreated =
      (prov as Record<string, JsonValue>)["created_at_utc"] ??
      (prov as Record<string, JsonValue>)["started_at_utc"];
    if (typeof provCreated === "string" && provCreated.trim()) return provCreated;
  }
}

function extractSchemaVersion(parsed: JsonValue): string | undefined {
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return;
  const obj = parsed as Record<string, JsonValue>;
  const direct = obj["schema_version"];
  if (typeof direct === "string" && direct.trim()) return direct;

  const meta = obj["meta"];
  if (meta && typeof meta === "object" && !Array.isArray(meta)) {
    const metaSchema = (meta as Record<string, JsonValue>)["schema_version"];
    if (typeof metaSchema === "string" && metaSchema.trim()) return metaSchema;
  }
}

function extractTags(parsed: JsonValue): string[] | undefined {
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return;
  const obj = parsed as Record<string, JsonValue>;
  const tags = obj["tags"];
  if (Array.isArray(tags)) {
    const out = tags.filter((t): t is string => typeof t === "string").map((t) => t.trim()).filter(Boolean);
    if (out.length) return out;
  }

  const meta = obj["meta"];
  if (meta && typeof meta === "object" && !Array.isArray(meta)) {
    const metaTags = (meta as Record<string, JsonValue>)["tags"];
    if (Array.isArray(metaTags)) {
      const out = metaTags
        .filter((t): t is string => typeof t === "string")
        .map((t) => t.trim())
        .filter(Boolean);
      if (out.length) return out;
    }
  }
}

function extractStatusFlags(parsed: JsonValue): ArtifactStatusFlags | undefined {
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return;
  const obj = parsed as Record<string, JsonValue>;

  const maybeNotComputable = obj["not_computable"];
  const flags: ArtifactStatusFlags = {};
  if (typeof maybeNotComputable === "boolean") flags.not_computable = maybeNotComputable;

  const constraints =
    obj["constraints"] ??
    obj["constraints_report"] ??
    (obj["meta"] && typeof obj["meta"] === "object" && !Array.isArray(obj["meta"])
      ? (obj["meta"] as Record<string, JsonValue>)["constraints"]
      : undefined);

  if (constraints && typeof constraints === "object" && !Array.isArray(constraints)) {
    const c = constraints as Record<string, JsonValue>;
    const missingInputs = c["missing_inputs"];
    if (Array.isArray(missingInputs) && missingInputs.length > 0) {
      flags.missing_inputs = true;
    }
    const notComputable = c["not_computable"];
    if (typeof notComputable === "boolean") {
      flags.not_computable = flags.not_computable ?? notComputable;
    }
  }

  return Object.keys(flags).length ? flags : undefined;
}

async function listJsonFilesRecursively(rootDir: string): Promise<string[]> {
  const out: string[] = [];
  async function walk(absDir: string) {
    const entries = await fs.readdir(absDir, { withFileTypes: true });
    // Deterministic ordering for traversal.
    entries.sort((a, b) => a.name.localeCompare(b.name));
    for (const entry of entries) {
      const abs = path.join(absDir, entry.name);
      if (entry.isDirectory()) {
        // Skip common non-artifact directories if misconfigured.
        if (entry.name === "node_modules" || entry.name === ".git") continue;
        await walk(abs);
        continue;
      }
      if (entry.isFile() && entry.name.toLowerCase().endsWith(".json")) {
        out.push(abs);
      }
    }
  }
  await walk(rootDir);
  // Deterministic ordering for the final list.
  out.sort((a, b) => a.localeCompare(b));
  return out;
}

export function getArtifactRootDir(): string {
  const configured = process.env.ABRAXAS_ARTIFACT_DIR?.trim();
  if (configured) return path.resolve(configured);
  return path.resolve(process.cwd(), "out");
}

export function validateArtifactId(id: string): boolean {
  // Conservative: keep IDs as opaque tokens but disallow path separators.
  if (!id) return false;
  if (id.includes("/") || id.includes("\\") || id.includes("..")) return false;
  return id.length <= 256;
}

export async function buildArtifactIndex(rootDir: string): Promise<ArtifactIndex> {
  const files = await listJsonFilesRecursively(rootDir);
  const items: ArtifactIndexItem[] = [];

  for (const absPath of files) {
    const filename = path.basename(absPath);
    const kind = inferKindFromName(filename);
    // If the file doesn't look like a dashboard artifact, still index it as unknown
    // so the user can see what's in the directory without hidden magic.
    let parsed: JsonValue | undefined;
    try {
      const raw = await fs.readFile(absPath, "utf-8");
      parsed = JSON.parse(raw) as JsonValue;
    } catch {
      parsed = undefined;
    }

    const artifact_id = extractArtifactId(parsed ?? null, filename);
    const created_at = extractCreatedAt(parsed ?? null);
    const schema_version = extractSchemaVersion(parsed ?? null);
    const tags = extractTags(parsed ?? null);
    const status_flags = extractStatusFlags(parsed ?? null);

    const relative_path = path.relative(rootDir, absPath);
    items.push({
      artifact_id,
      kind,
      relative_path,
      filename,
      created_at,
      schema_version,
      tags,
      status_flags,
    });
  }

  // Group by artifact_id deterministically.
  const byId = new Map<string, ArtifactIndexItem[]>();
  for (const it of items) {
    const arr = byId.get(it.artifact_id) ?? [];
    arr.push(it);
    byId.set(it.artifact_id, arr);
  }

  const grouped: ArtifactIndexEntry[] = [];
  const artifactIds = Array.from(byId.keys()).sort((a, b) => a.localeCompare(b));
  for (const artifact_id of artifactIds) {
    const group = byId.get(artifact_id) ?? [];
    group.sort((a, b) => a.filename.localeCompare(b.filename));

    // Choose a representative created_at/schema_version/tags/status_flags (prefer non-empty).
    const created_at =
      group.map((g) => g.created_at).find((v) => typeof v === "string" && v.trim()) ??
      undefined;
    const schema_version =
      group.map((g) => g.schema_version).find((v) => typeof v === "string" && v.trim()) ??
      undefined;
    const tags =
      group.map((g) => g.tags).find((v) => Array.isArray(v) && v.length) ?? undefined;
    const status_flags =
      group.map((g) => g.status_flags).find((v) => v && Object.keys(v).length) ?? undefined;

    grouped.push({
      artifact_id,
      created_at,
      schema_version,
      tags,
      status_flags,
      available: {
        envelope: group.some((g) => g.kind === "oracle_envelope_v2"),
        narrative: group.some((g) => g.kind === "narrative_bundle_v1"),
      },
      files: group,
    });
  }

  return { root_dir: rootDir, items: grouped };
}

export async function readArtifactJsonByKind(params: {
  rootDir: string;
  artifactId: string;
  kind: Exclude<ArtifactKind, "unknown">;
}): Promise<{ json: JsonValue; file: ArtifactIndexItem } | null> {
  const { rootDir, artifactId, kind } = params;
  const index = await buildArtifactIndex(rootDir);
  const entry = index.items.find((i) => i.artifact_id === artifactId);
  if (!entry) return null;

  const file = entry.files.find((f) => f.kind === kind);
  if (!file) return null;

  const abs = path.resolve(rootDir, file.relative_path);
  // Safety: ensure resolved path remains under rootDir.
  const rootResolved = path.resolve(rootDir) + path.sep;
  const absResolved = path.resolve(abs);
  if (!absResolved.startsWith(rootResolved)) return null;

  const raw = await fs.readFile(absResolved, "utf-8");
  const json = JSON.parse(raw) as JsonValue;
  return { json, file };
}

export async function listDriftReports(rootDir: string): Promise<ArtifactIndexEntry[]> {
  const index = await buildArtifactIndex(rootDir);
  const drift = index.items
    .map((i) => ({
      ...i,
      files: i.files.filter((f) => f.kind === "drift_report_v1"),
    }))
    .filter((i) => i.files.length > 0);

  // Prefer created_at descending if parseable; fallback to artifact_id.
  drift.sort((a, b) => {
    const da = a.created_at ? Date.parse(a.created_at) : NaN;
    const db = b.created_at ? Date.parse(b.created_at) : NaN;
    if (!Number.isNaN(da) && !Number.isNaN(db) && da !== db) return db - da;
    return a.artifact_id.localeCompare(b.artifact_id);
  });
  return drift;
}

export function fallbackCreatedAtFromStat(statMtimeMs: number): string {
  return safeIsoFromDate(new Date(statMtimeMs));
}

