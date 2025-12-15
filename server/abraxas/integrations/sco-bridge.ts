/**
 * ABX-Core - SCO Bridge
 * TypeScript bridge to Python Symbolic Compression Operator
 * @module abraxas/integrations/sco-bridge
 */

import { spawn } from "child_process";
import { writeFile, unlink } from "fs/promises";
import { join } from "path";
import { randomBytes } from "crypto";

// ================================
// Type Definitions
// ================================

export type CompressionTier = "ECO_T1" | "SCO_T2";
export type CompressionStatus = "proto" | "emergent" | "stabilizing";

export interface SymbolicCompressionEvent {
  event_type: string;
  tier: CompressionTier;
  original_token: string;
  replacement_token: string;
  domain: string;
  phonetic_similarity: number;
  semantic_transparency_delta: number;
  intent_preservation_score: number;
  compression_pressure: number;
  symbolic_transparency_index: number;
  symbolic_load_capacity: number;
  replacement_direction_vector: {
    humor: number;
    aggression: number;
    authority: number;
    intimacy: number;
    nihilism: number;
    irony: number;
  };
  observed_frequency: number;
  status: CompressionStatus;
  provenance_sha256: string;
}

export interface SCORecord {
  id: string;
  text: string;
}

export interface SCOLexiconEntry {
  canonical: string;
  variants: string[];
}

export interface SCOAnalysisOptions {
  records: SCORecord[];
  lexicon: SCOLexiconEntry[];
  domain?: string;
  stiLexiconPath?: string;
}

export interface SCOAnalysisResult {
  events: SymbolicCompressionEvent[];
  provenance: string;
  eventCount: number;
}

// ================================
// Python CLI Bridge
// ================================

class SCOBridge {
  private pythonPath: string;

  constructor(pythonPath: string = "python3") {
    this.pythonPath = pythonPath;
  }

  /**
   * Run SCO analysis via Python CLI
   */
  async analyze(options: SCOAnalysisOptions): Promise<SCOAnalysisResult> {
    const tmpDir = "/tmp/abraxas-sco";
    const sessionId = randomBytes(8).toString("hex");
    const recordsPath = join(tmpDir, `records-${sessionId}.json`);
    const lexiconPath = join(tmpDir, `lexicon-${sessionId}.json`);
    const outPath = join(tmpDir, `events-${sessionId}.jsonl`);

    try {
      // Write input files
      await writeFile(recordsPath, JSON.stringify(options.records, null, 2));
      await writeFile(lexiconPath, JSON.stringify(options.lexicon, null, 2));

      // Build command args
      const args = [
        "-m",
        "abraxas.cli.sco_run",
        "--records",
        recordsPath,
        "--lexicon",
        lexiconPath,
        "--out",
        outPath,
        "--domain",
        options.domain || "general",
      ];

      if (options.stiLexiconPath) {
        args.push("--sti", options.stiLexiconPath);
      }

      // Execute Python CLI
      const { stdout, stderr } = await this._exec(this.pythonPath, args);

      // Parse provenance from stdout
      const provenanceMatch = stdout.match(/transparency_lexicon_provenance=([a-f0-9]{64})/);
      const provenance = provenanceMatch ? provenanceMatch[1] : "";

      // Read and parse events
      const events = await this._readEventsJSONL(outPath);

      return {
        events,
        provenance,
        eventCount: events.length,
      };
    } finally {
      // Cleanup temp files
      await this._cleanup([recordsPath, lexiconPath, outPath]);
    }
  }

  /**
   * Execute Python subprocess
   */
  private _exec(cmd: string, args: string[]): Promise<{ stdout: string; stderr: string }> {
    return new Promise((resolve, reject) => {
      const proc = spawn(cmd, args);
      let stdout = "";
      let stderr = "";

      proc.stdout.on("data", (data) => {
        stdout += data.toString();
      });

      proc.stderr.on("data", (data) => {
        stderr += data.toString();
      });

      proc.on("close", (code) => {
        if (code === 0) {
          resolve({ stdout, stderr });
        } else {
          reject(new Error(`SCO CLI exited with code ${code}:\n${stderr}`));
        }
      });

      proc.on("error", (err) => {
        reject(new Error(`Failed to spawn Python process: ${err.message}`));
      });
    });
  }

  /**
   * Read JSONL events file
   */
  private async _readEventsJSONL(path: string): Promise<SymbolicCompressionEvent[]> {
    const fs = await import("fs/promises");
    const content = await fs.readFile(path, "utf-8");
    return content
      .split("\n")
      .filter((line) => line.trim())
      .map((line) => JSON.parse(line));
  }

  /**
   * Cleanup temp files
   */
  private async _cleanup(paths: string[]): Promise<void> {
    await Promise.all(
      paths.map((p) =>
        unlink(p).catch(() => {
          /* ignore errors */
        })
      )
    );
  }
}

// ================================
// Singleton Instance
// ================================

export const scoBridge = new SCOBridge();

// ================================
// High-level API
// ================================

/**
 * Analyze text corpus for symbolic compression events
 */
export async function detectCompressionEvents(
  texts: string[],
  lexicon: SCOLexiconEntry[],
  domain: string = "general"
): Promise<SymbolicCompressionEvent[]> {
  const records: SCORecord[] = texts.map((text, i) => ({
    id: `rec-${i}`,
    text,
  }));

  const result = await scoBridge.analyze({ records, lexicon, domain });
  return result.events;
}

/**
 * Extract compression pressure signals for Weather Engine
 */
export function extractWeatherSignals(events: SymbolicCompressionEvent[]): {
  compressionPressure: number;
  driftIntensity: number;
  rdvVector: Record<string, number>;
  tierDistribution: { eco_t1: number; sco_t2: number };
} {
  if (events.length === 0) {
    return {
      compressionPressure: 0,
      driftIntensity: 0,
      rdvVector: { humor: 0, aggression: 0, authority: 0, intimacy: 0, nihilism: 0, irony: 0 },
      tierDistribution: { eco_t1: 0, sco_t2: 0 },
    };
  }

  // Average compression pressure
  const totalCP = events.reduce((sum, e) => sum + e.compression_pressure, 0);
  const compressionPressure = totalCP / events.length;

  // Drift intensity (transparency delta)
  const totalDelta = events.reduce((sum, e) => sum + e.semantic_transparency_delta, 0);
  const driftIntensity = totalDelta / events.length;

  // Aggregate RDV
  const rdvVector: Record<string, number> = {
    humor: 0,
    aggression: 0,
    authority: 0,
    intimacy: 0,
    nihilism: 0,
    irony: 0,
  };

  for (const event of events) {
    for (const [axis, val] of Object.entries(event.replacement_direction_vector)) {
      rdvVector[axis] += val;
    }
  }

  // Normalize RDV
  for (const axis of Object.keys(rdvVector)) {
    rdvVector[axis] /= events.length;
  }

  // Tier distribution
  const eco_t1 = events.filter((e) => e.tier === "ECO_T1").length / events.length;
  const sco_t2 = events.filter((e) => e.tier === "SCO_T2").length / events.length;

  return {
    compressionPressure: +compressionPressure.toFixed(4),
    driftIntensity: +driftIntensity.toFixed(4),
    rdvVector,
    tierDistribution: { eco_t1: +eco_t1.toFixed(2), sco_t2: +sco_t2.toFixed(2) },
  };
}
