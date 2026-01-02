import { promises as fs } from "fs";
import type { Dirent } from "fs";
import path from "path";

import type { JsonValue } from "./diff";

const DEFAULT_OUT_DIR = path.resolve(process.cwd(), "out");

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

function looksLikeEnvelope(obj: Record<string, unknown>): boolean {
  const hasId = Boolean(obj["artifact_id"] || obj["id"] || obj["artifactId"]);
  if (!hasId) return false;
  return "signal_layer" in obj || "symbolic_compression" in obj;
}

function looksLikeNarrative(obj: Record<string, unknown>): boolean {
  return "headline" in obj && "signal_summary" in obj;
}

function looksLikeDrift(obj: Record<string, unknown>): boolean {
  return "clusters" in obj && "provenance" in obj;
}

function artifactId(obj: Record<string, unknown>, fallback: string): string {
  return String(obj["artifact_id"] || obj["id"] || obj["artifactId"] || fallback);
}

function safeJsonParse(text: string): unknown | null {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

async function listFilesRecursive(dir: string): Promise<string[]> {
  const out: string[] = [];
  let ents: Dirent[] = [];
  try {
    ents = await fs.readdir(dir, { withFileTypes: true });
  } catch {
    return out;
  }

  ents.sort((a, b) => a.name.localeCompare(b.name));
  for (const ent of ents) {
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) {
      out.push(...(await listFilesRecursive(p)));
    } else {
      out.push(p);
    }
  }
  return out;
}

export type ArtifactIndexItem = {
  artifact_id: string;
  created_at: string;
  envelope_path: string | null;
  narrative_path: string | null;
  missing_inputs_count: number;
  not_computable_count: number;
};

export type DriftIndexItem = {
  report_id: string;
  created_at: string;
  path: string;
  cluster_count: number;
};

type StoredItem = { path: string; obj: JsonValue };

export class ArtifactStore {
  private outDir: string;
  private env = new Map<string, StoredItem>();
  private nar = new Map<string, StoredItem>();
  private drift = new Map<string, StoredItem>();

  constructor(outDir: string = DEFAULT_OUT_DIR) {
    this.outDir = outDir;
  }

  async rescan(): Promise<void> {
    this.env.clear();
    this.nar.clear();
    this.drift.clear();

    const files = (await listFilesRecursive(this.outDir)).filter((p) =>
      p.endsWith(".json") || p.endsWith(".jsonl")
    );

    for (const p of files) {
      const rel = path.relative(process.cwd(), p);
      let text = "";
      try {
        text = await fs.readFile(p, "utf8");
      } catch {
        continue;
      }

      if (p.endsWith(".json")) {
        const parsed = safeJsonParse(text);
        if (!isRecord(parsed)) continue;
        this.ingestObject(parsed, rel, path.basename(p, ".json"));
        continue;
      }

      // .jsonl
      const lines = text.split(/\r?\n/);
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i]?.trim();
        if (!line) continue;
        const parsed = safeJsonParse(line);
        if (!isRecord(parsed)) continue;
        this.ingestObject(parsed, rel, `${path.basename(p, ".jsonl")}:${i + 1}`);
      }
    }
  }

  private ingestObject(obj: Record<string, unknown>, relPath: string, fallbackId: string): void {
    const aid = artifactId(obj, fallbackId);

    if (looksLikeEnvelope(obj)) {
      this.env.set(aid, { path: relPath, obj: obj as unknown as JsonValue });
      return;
    }

    if (looksLikeNarrative(obj)) {
      this.nar.set(aid, { path: relPath, obj: obj as unknown as JsonValue });
      return;
    }

    if (looksLikeDrift(obj)) {
      const prov = isRecord(obj["provenance"]) ? (obj["provenance"] as Record<string, unknown>) : {};
      const rid = String(prov["input_set_hash"] || fallbackId);
      this.drift.set(rid, { path: relPath, obj: obj as unknown as JsonValue });
    }
  }

  listArtifacts(): ArtifactIndexItem[] {
    const ids = Array.from(
      new Set([...Array.from(this.env.keys()), ...Array.from(this.nar.keys())])
    ).sort();

    return ids.map((id) => {
      const env = this.env.get(id);
      const nar = this.nar.get(id);

      let created_at = "";
      let missing_inputs_count = 0;
      let not_computable_count = 0;

      if (env?.obj && isRecord(env.obj)) {
        const o = env.obj as unknown as Record<string, unknown>;
        created_at = String(o["created_at"] || o["createdAt"] || "");
        const mi = o["missing_inputs"];
        const nc = o["not_computable"];
        missing_inputs_count = Array.isArray(mi) ? mi.length : 0;
        not_computable_count = Array.isArray(nc) ? nc.length : 0;
      }

      return {
        artifact_id: id,
        created_at,
        envelope_path: env?.path ?? null,
        narrative_path: nar?.path ?? null,
        missing_inputs_count,
        not_computable_count,
      };
    });
  }

  getEnvelope(artifactId: string): JsonValue {
    const item = this.env.get(artifactId);
    if (!item) throw new Error("not_found");
    return item.obj;
  }

  getNarrative(artifactId: string): JsonValue {
    const item = this.nar.get(artifactId);
    if (!item) throw new Error("not_found");
    return item.obj;
  }

  listDriftReports(): DriftIndexItem[] {
    const ids = Array.from(this.drift.keys()).sort();
    return ids.map((id) => {
      const item = this.drift.get(id)!;
      const obj = item.obj;
      let created_at = "";
      let cluster_count = 0;
      if (obj && isRecord(obj)) {
        const o = obj as unknown as Record<string, unknown>;
        const prov = isRecord(o["provenance"]) ? (o["provenance"] as Record<string, unknown>) : {};
        created_at = String(prov["created_at"] || "");
        cluster_count = Array.isArray(o["clusters"]) ? (o["clusters"] as unknown[]).length : 0;
      }
      return { report_id: id, created_at, path: item.path, cluster_count };
    });
  }

  getDrift(reportId: string): JsonValue {
    const item = this.drift.get(reportId);
    if (!item) throw new Error("not_found");
    return item.obj;
  }
}

