/**
 * ABX-Core v1.2 - Sigil Forge Pipeline
 * SEED Framework Compliant
 *
 * @module abraxas/pipelines/sigil-forge
 * @entropy_class low
 * @deterministic true
 * @capabilities { read: [], write: [], network: false }
 *
 * Sigil generation using symbolic kernel:
 * - Deterministic glyph generation
 * - Ritual sealing and verification
 * - Provenance embedding
 * - Cryptographic attestation
 */

import crypto from "crypto";
import type { RitualInput } from "../models/ritual";
import { aggregateQualityScore } from "../core/kernel";
import { computeSymbolicMetricsOptimized } from "../core/kernel-optimized";
import { ritualToContext, createPipelineVector } from "../integrations/runes-adapter";
import { selectArchetypesForRunes } from "../core/archetype";

export interface SigilInput {
  ritual: RitualInput;
  subject: string; // What the sigil represents (ticker, entity, concept)
  context?: Record<string, any>; // Additional context data
}

export interface Sigil {
  id: string;
  core: string; // The visual/textual sigil representation
  seal: string; // Cryptographic seal
  method: "runic" | "symbolic" | "hybrid";
  subject: string;
  glyphs: string[];
  resonance: number;
  quality: number;
  provenance: {
    seed: string;
    runes: string[];
    archetypes: string[];
    timestamp: number;
  };
  verification: {
    hash: string;
    signature: string;
  };
}

/**
 * Forge a sigil from ritual and subject
 */
export function forgeSigil(input: SigilInput): Sigil {
  const { ritual, subject, context = {} } = input;
  const ritualContext = ritualToContext(ritual);

  // Create feature vector for subject
  const subjectHash = hashString(subject, ritual.seed);
  const features = {
    subject_resonance: (subjectHash % 100) / 100,
    contextual_depth: Object.keys(context).length / 10,
    runic_alignment: (subjectHash % ritual.runes.length) / ritual.runes.length,
    ...normalizeContext(context),
  };

  const vector = createPipelineVector(
    features,
    `sigil-${subject}`,
    ritual.seed,
    "pipelines/sigil-forge",
    ritualContext.timestamp
  );

  // Compute symbolic metrics
  const metrics = computeSymbolicMetricsOptimized(vector, ritualContext);
  const quality = aggregateQualityScore(metrics);

  // Select archetypes
  const archetypes = selectArchetypesForRunes(ritual.runes.map((r) => r.id));
  const archetypeNames = archetypes.map((a) => a.name);

  // Determine sigil method
  const method = determineSigilMethod(metrics, quality);

  // Generate glyphs
  const glyphs = generateGlyphs(subject, ritual, metrics, method);

  // Generate core sigil
  const core = assembleSigil(glyphs, ritual.runes.map((r) => r.id), archetypeNames);

  // Generate cryptographic seal
  const seal = generateSeal(core, ritual.seed, subject, ritualContext.timestamp);

  // Generate verification
  const verification = generateVerification(core, seal, ritual);

  return {
    id: crypto.randomUUID(),
    core,
    seal,
    method,
    subject,
    glyphs,
    resonance: Math.round(metrics.ARF * 100) / 100,
    quality: Math.round(quality * 100) / 100,
    provenance: {
      seed: ritual.seed,
      runes: ritual.runes.map((r) => r.id),
      archetypes: archetypeNames,
      timestamp: ritualContext.timestamp,
    },
    verification,
  };
}

/**
 * Determine optimal sigil generation method
 */
function determineSigilMethod(
  metrics: any,
  quality: number
): "runic" | "symbolic" | "hybrid" {
  // High quality + strong resonance = symbolic
  if (quality > 0.7 && Math.abs(metrics.ARF) > 0.5) {
    return "symbolic";
  }

  // Low drift + high coherence = runic
  if (metrics.SDR < 0.3 && metrics.ITC > 0.7) {
    return "runic";
  }

  // Default: hybrid approach
  return "hybrid";
}

/**
 * Generate sigil glyphs based on method
 */
function generateGlyphs(
  subject: string,
  ritual: RitualInput,
  metrics: any,
  method: "runic" | "symbolic" | "hybrid"
): string[] {
  const glyphs: string[] = [];

  if (method === "runic" || method === "hybrid") {
    // Runic glyphs from runes
    const runicGlyphs = ritual.runes.map((rune) => runeToGlyph(rune.id));
    glyphs.push(...runicGlyphs);
  }

  if (method === "symbolic" || method === "hybrid") {
    // Symbolic glyphs from metrics
    const symbolicGlyphs = metricsToGlyphs(metrics);
    glyphs.push(...symbolicGlyphs);
  }

  // Subject-derived glyph
  const subjectGlyph = subjectToGlyph(subject, ritual.seed);
  glyphs.push(subjectGlyph);

  return glyphs;
}

/**
 * Convert rune to glyph symbol
 */
function runeToGlyph(rune: string): string {
  const runeGlyphMap: Record<string, string> = {
    aether: "⟁",
    flux: "⟂",
    glyph: "⟃",
    nexus: "⟄",
    tide: "⟅",
    ward: "⟆",
    whisper: "⟇",
    void: "⟈",
  };

  return runeGlyphMap[rune] || "⟉";
}

/**
 * Convert metrics to symbolic glyphs
 */
function metricsToGlyphs(metrics: any): string[] {
  const glyphs: string[] = [];

  // Drift glyph
  if (metrics.SDR < 0.3) {
    glyphs.push("◬"); // Low drift: stable
  } else if (metrics.SDR > 0.7) {
    glyphs.push("◭"); // High drift: volatile
  }

  // Resonance glyph
  if (Math.abs(metrics.ARF) > 0.5) {
    glyphs.push(metrics.ARF > 0 ? "◮" : "◯"); // Positive/negative resonance
  }

  // Entropy glyph
  if (metrics.Hσ > 0.6) {
    glyphs.push("◰"); // High entropy
  } else if (metrics.Hσ < 0.3) {
    glyphs.push("◱"); // Low entropy
  }

  return glyphs;
}

/**
 * Convert subject to glyph using deterministic hash
 */
function subjectToGlyph(subject: string, seed: string): string {
  const hash = hashString(subject, seed);
  const glyphs = ["◲", "◳", "◴", "◵", "◶", "◷", "◸", "◹", "◺", "◻", "◼", "◽", "◾", "◿"];
  return glyphs[hash % glyphs.length];
}

/**
 * Assemble final sigil from components
 */
function assembleSigil(
  glyphs: string[],
  runes: string[],
  archetypes: string[]
): string {
  // Create multi-layered sigil structure
  const glyphSequence = glyphs.join("·");
  const runeMarkers = runes.map((r) => r.charAt(0).toUpperCase()).join("");
  const archetypeInitials = archetypes.map((a) => a.charAt(4)).join(""); // 5th char for uniqueness

  return `⟦${glyphSequence}⟧·${runeMarkers}·${archetypeInitials}`;
}

/**
 * Generate cryptographic seal
 */
function generateSeal(core: string, seed: string, subject: string, timestamp: number): string {
  const payload = { core, seed, subject, timestamp };
  const hash = crypto
    .createHash("sha256")
    .update(JSON.stringify(payload))
    .digest("hex");

  return hash.substring(0, 16);
}

/**
 * Generate verification data
 */
function generateVerification(core: string, seal: string, ritual: RitualInput) {
  const verificationPayload = {
    core,
    seal,
    seed: ritual.seed,
    runes: ritual.runes,
    date: ritual.date,
  };

  const hash = crypto
    .createHash("sha256")
    .update(JSON.stringify(verificationPayload))
    .digest("hex");

  const signature = `⟟Σ${crypto
    .createHash("md5")
    .update(hash)
    .digest("hex")
    .substring(0, 8)}Σ⟟`;

  return {
    hash: hash.substring(0, 16),
    signature,
  };
}

/**
 * Verify sigil authenticity
 */
export function verifySigil(sigil: Sigil, expectedSeed: string): boolean {
  // Regenerate seal
  const regeneratedSeal = generateSeal(
    sigil.core,
    expectedSeed,
    sigil.subject,
    sigil.provenance.timestamp
  );

  return regeneratedSeal === sigil.seal;
}

/**
 * Normalize context to features (0-1 range)
 */
function normalizeContext(context: Record<string, any>): Record<string, number> {
  const normalized: Record<string, number> = {};

  for (const [key, value] of Object.entries(context)) {
    if (typeof value === "number") {
      normalized[`ctx_${key}`] = Math.min(1, Math.max(0, value));
    } else if (typeof value === "boolean") {
      normalized[`ctx_${key}`] = value ? 1 : 0;
    } else if (typeof value === "string") {
      const hash = hashString(value, key);
      normalized[`ctx_${key}`] = (hash % 100) / 100;
    }
  }

  return normalized;
}

/**
 * Deterministic hash function
 */
function hashString(str: string, seed: string): number {
  const combined = `${str}-${seed}`;
  const hash = crypto.createHash("md5").update(combined).digest("hex");
  return parseInt(hash.substring(0, 8), 16);
}
