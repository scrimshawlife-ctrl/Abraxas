/**
 * ABX-Core - SCO Analyzer Pipeline
 * Symbolic Compression Analysis Pipeline
 * @module abraxas/pipelines/sco-analyzer
 */

import {
  scoBridge,
  detectCompressionEvents,
  extractWeatherSignals,
  type SymbolicCompressionEvent,
  type SCOLexiconEntry,
} from "../integrations/sco-bridge";

// ================================
// Default Lexicons
// ================================

const DEFAULT_LEXICONS: Record<string, SCOLexiconEntry[]> = {
  music: [
    { canonical: "aphex twin", variants: ["aphex twins", "apex twin"] },
    { canonical: "boards of canada", variants: ["boards", "boc"] },
    { canonical: "autechre", variants: ["ae", "autecker"] },
  ],
  idiom: [
    { canonical: "nick of time", variants: ["nit of time"] },
    { canonical: "for all intents and purposes", variants: ["for all intensive purposes"] },
    { canonical: "old-timer's disease", variants: ["alzheimer's disease"] },
  ],
  crypto: [
    { canonical: "ethereum", variants: ["etherium"] },
    { canonical: "cryptocurrency", variants: ["crypto currency"] },
  ],
  general: [],
};

// ================================
// Pipeline
// ================================

export interface SCOAnalysisInput {
  texts: string[];
  domain?: string;
  customLexicon?: SCOLexiconEntry[];
  stiLexiconPath?: string;
}

export interface SCOAnalysisOutput {
  events: SymbolicCompressionEvent[];
  signals: {
    compressionPressure: number;
    driftIntensity: number;
    rdvVector: Record<string, number>;
    tierDistribution: { eco_t1: number; sco_t2: number };
  };
  metadata: {
    provenance: string;
    domain: string;
    eventCount: number;
    textsAnalyzed: number;
  };
}

/**
 * Run SCO analysis on text corpus
 */
export async function analyzeSCO(input: SCOAnalysisInput): Promise<SCOAnalysisOutput> {
  const domain = input.domain || "general";
  const lexicon = input.customLexicon || DEFAULT_LEXICONS[domain] || DEFAULT_LEXICONS.general;

  // Detect compression events
  const events = await detectCompressionEvents(input.texts, lexicon, domain);

  // Extract weather signals
  const signals = extractWeatherSignals(events);

  // Compute provenance (hash of all event hashes)
  const provenance = computeProvenanceHash(events);

  return {
    events,
    signals,
    metadata: {
      provenance,
      domain,
      eventCount: events.length,
      textsAnalyzed: input.texts.length,
    },
  };
}

/**
 * Compute aggregate provenance hash
 */
function computeProvenanceHash(events: SymbolicCompressionEvent[]): string {
  const crypto = require("crypto");
  const hashes = events.map((e) => e.provenance_sha256).sort();
  const combined = hashes.join("");
  return crypto.createHash("sha256").update(combined).digest("hex");
}

// ================================
// Batch Processing
// ================================

/**
 * Analyze multiple domains in parallel
 */
export async function batchAnalyzeSCO(
  corpora: Array<{ domain: string; texts: string[] }>
): Promise<Map<string, SCOAnalysisOutput>> {
  const results = await Promise.all(
    corpora.map(async ({ domain, texts }) => {
      const output = await analyzeSCO({ texts, domain });
      return [domain, output] as const;
    })
  );

  return new Map(results);
}

// ================================
// Weather Engine Integration
// ================================

/**
 * Convert SCO signals to Weather Engine input format
 */
export interface WeatherEngineSignal {
  metric: string;
  value: number;
  source: string;
  timestamp: string;
}

export function scoToWeatherSignals(
  output: SCOAnalysisOutput,
  timestamp: string = new Date().toISOString()
): WeatherEngineSignal[] {
  const signals: WeatherEngineSignal[] = [];

  // Compression pressure -> Symbolic drift
  signals.push({
    metric: "symbolic_drift",
    value: output.signals.compressionPressure,
    source: "sco",
    timestamp,
  });

  // Drift intensity -> Transparency flux
  signals.push({
    metric: "transparency_flux",
    value: output.signals.driftIntensity,
    source: "sco",
    timestamp,
  });

  // RDV axes -> Memetic weather components
  for (const [axis, value] of Object.entries(output.signals.rdvVector)) {
    signals.push({
      metric: `rdv_${axis}`,
      value,
      source: "sco",
      timestamp,
    });
  }

  // Tier distribution -> Compression stability
  signals.push({
    metric: "compression_stability",
    value: output.signals.tierDistribution.eco_t1,
    source: "sco",
    timestamp,
  });

  return signals;
}
