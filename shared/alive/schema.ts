import { z } from "zod";

/**
 * ALIVE: Autonomous Life-Influence Vitality Engine
 *
 * Core schema definitions for ALIVE field signatures.
 * Same engine, different lens across tiers (Psychonaut/Academic/Enterprise).
 */

// ═══════════════════════════════════════════════════════════════════════════
// AXIS DEFINITIONS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * I = Influence (social gravity ↔ network position ↔ persuasive reach)
 * Measures capacity to shape opinion, activate networks, and move discourse.
 */
export const influenceMetricSchema = z.object({
  metricId: z.string(),
  metricVersion: z.string(),
  status: z.enum(["provisional", "shadowed", "promoted"]),
  value: z.number(),
  confidence: z.number().min(0).max(1),
  timestamp: z.string().datetime(),
});

/**
 * V = Vitality (creative momentum ↔ discourse velocity ↔ engagement coherence)
 * Measures sustained creative output and resonance across time.
 */
export const vitalityMetricSchema = z.object({
  metricId: z.string(),
  metricVersion: z.string(),
  status: z.enum(["provisional", "shadowed", "promoted"]),
  value: z.number(),
  confidence: z.number().min(0).max(1),
  timestamp: z.string().datetime(),
});

/**
 * L = Life-Logistics (lived cost ↔ material condition ↔ operational constraint)
 * Measures material reality: time debt, financial runway, resource access.
 */
export const lifeLogisticsMetricSchema = z.object({
  metricId: z.string(),
  metricVersion: z.string(),
  status: z.enum(["provisional", "shadowed", "promoted"]),
  value: z.number(),
  confidence: z.number().min(0).max(1),
  timestamp: z.string().datetime(),
});

// ═══════════════════════════════════════════════════════════════════════════
// FIELD SIGNATURE (canonical output shape)
// ═══════════════════════════════════════════════════════════════════════════

export const aliveFieldSignatureSchema = z.object({
  analysisId: z.string(),
  subjectId: z.string(),
  timestamp: z.string().datetime(),

  // The three axes
  influence: z.array(influenceMetricSchema),
  vitality: z.array(vitalityMetricSchema),
  lifeLogistics: z.array(lifeLogisticsMetricSchema),

  // Composite scores
  compositeScore: z.object({
    overall: z.number().min(0).max(1),
    influenceWeight: z.number(),
    vitalityWeight: z.number(),
    lifeLogisticsWeight: z.number(),
  }),

  // Provenance & strain
  corpusProvenance: z.array(z.object({
    sourceId: z.string(),
    sourceType: z.string(),
    weight: z.number(),
    timestamp: z.string().datetime(),
  })),

  metricStrain: z.object({
    detected: z.boolean(),
    strainReport: z.string().optional(),
  }).optional(),
});

// ═══════════════════════════════════════════════════════════════════════════
// INPUT SCHEMA
// ═══════════════════════════════════════════════════════════════════════════

export const aliveRunInputSchema = z.object({
  subjectId: z.string(),
  tier: z.enum(["psychonaut", "academic", "enterprise"]),
  corpusConfig: z.object({
    sources: z.array(z.string()),
    timeRange: z.object({
      start: z.string().datetime(),
      end: z.string().datetime(),
    }).optional(),
  }),
  metricConfig: z.object({
    enableProvisional: z.boolean().default(false),
    enableStrain: z.boolean().default(false),
  }).optional(),
});

// ═══════════════════════════════════════════════════════════════════════════
// EXPORT TYPES
// ═══════════════════════════════════════════════════════════════════════════

export type InfluenceMetric = z.infer<typeof influenceMetricSchema>;
export type VitalityMetric = z.infer<typeof vitalityMetricSchema>;
export type LifeLogisticsMetric = z.infer<typeof lifeLogisticsMetricSchema>;
export type ALIVEFieldSignature = z.infer<typeof aliveFieldSignatureSchema>;
export type ALIVERunInput = z.infer<typeof aliveRunInputSchema>;
