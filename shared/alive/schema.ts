import { z } from "zod";

/**
 * ALIVE: Autonomous Life-Influence Vitality Engine
 *
 * SCHEMA VERSION: 1.0.0
 * LOCKED: 2025-12-20
 *
 * BREAKING CHANGE POLICY:
 * - Do NOT modify existing fields without major version bump
 * - Add new optional fields only
 * - Deprecate fields with warnings, remove in next major version
 * - Version format: MAJOR.MINOR.PATCH
 *
 * ARCHITECTURE:
 * - signature = raw computed metrics (deterministic core)
 * - view = tier-filtered presentation (same computation, different lens)
 */

export const ALIVE_SCHEMA_VERSION = "alive-schema@1.0.0" as const;
export const ALIVE_ENGINE_VERSION = "alive-core@0.1.0" as const;

// ═══════════════════════════════════════════════════════════════════════════
// TIER & AXIS ENUMS
// ═══════════════════════════════════════════════════════════════════════════

export type AliveTier = "psychonaut" | "academic" | "enterprise";

export type AliveMetricAxis = "influence" | "vitality" | "life_logistics";

export type AliveMetricStatus = "promoted" | "shadow" | "provisional" | "deprecated";

export type AliveSeverity = "info" | "notice" | "warning" | "critical";

// ═══════════════════════════════════════════════════════════════════════════
// PROVENANCE (deterministic reproducibility anchors)
// ═══════════════════════════════════════════════════════════════════════════

export const aliveProvenanceSchema = z.object({
  run_id: z.string(), // uuid or content-hash derived
  created_at: z.string(), // ISO timestamp
  schema_version: z.string(), // e.g. alive-schema@1.0.0
  engine_version: z.string(), // e.g. alive-core@0.1.0
  metric_registry_hash: z.string(), // hash of metric registry snapshot
  input_hash: z.string(), // hash of normalized artifact bundle
  profile_hash: z.string().optional(), // hash of onboarding/profile weights
  corpus_context: z
    .object({
      corpus_version: z.string().optional(), // e.g. meta-corpus@1.0
      decay_policy_hash: z.string().optional(), // half-life config hash
    })
    .optional(),
});

export type AliveProvenance = z.infer<typeof aliveProvenanceSchema>;

// ═══════════════════════════════════════════════════════════════════════════
// ARTIFACT REFERENCE
// ═══════════════════════════════════════════════════════════════════════════

export const aliveArtifactRefSchema = z.object({
  artifact_id: z.string(), // internal id
  kind: z.enum(["text", "url", "pdf", "image", "audio", "multi"]),
  source: z.string().optional(), // e.g. "user_upload", "web", "internal"
  title: z.string().optional(),
  url: z.string().optional(),
  language: z.string().optional(), // "en", etc
  timestamp: z.string().optional(), // ISO if known (publication or capture time)
  notes: z.string().optional(),
  content: z.string().optional(), // normalized analysis-ready content (text or serialized payload)
  payload: z.unknown().optional(), // raw artifact payload for non-text items
});

export type AliveArtifactRef = z.infer<typeof aliveArtifactRefSchema>;

// ═══════════════════════════════════════════════════════════════════════════
// METRIC VALUE
// ═══════════════════════════════════════════════════════════════════════════

export const aliveMetricValueSchema = z.object({
  metric_id: z.string(), // e.g. "IM.NCR"
  axis: z.enum(["influence", "vitality", "life_logistics"]),
  name: z.string(), // human-readable
  value: z.number(), // 0..1 normalized
  confidence: z.number(), // 0..1 epistemic confidence (not "truth")
  status: z.enum(["promoted", "shadow", "provisional", "deprecated"]),
  version: z.string(), // metric semantic version, e.g. "1.0.0"
  evidence: z
    .object({
      spans: z.array(z.object({ start: z.number(), end: z.number(), note: z.string().optional() })).optional(),
      cues: z.array(z.string()).optional(),
      references: z.array(z.string()).optional(),
    })
    .optional(),
  explanation: z
    .object({
      operational_definition: z.string().optional(),
      failure_modes: z.array(z.string()).optional(),
    })
    .optional(),
});

export type AliveMetricValue = z.infer<typeof aliveMetricValueSchema>;

// ═══════════════════════════════════════════════════════════════════════════
// FIELD SIGNATURE (radar-friendly: axis -> metric values)
// ═══════════════════════════════════════════════════════════════════════════

export const aliveFieldSignatureSchema = z.object({
  influence: z.array(aliveMetricValueSchema),
  vitality: z.array(aliveMetricValueSchema),
  life_logistics: z.array(aliveMetricValueSchema),
  aggregates: z
    .object({
      influence_intensity: z.object({ value: z.number(), confidence: z.number() }).optional(),
      vitality_charge: z.object({ value: z.number(), confidence: z.number() }).optional(),
      logistics_friction: z.object({ value: z.number(), confidence: z.number() }).optional(),
    })
    .optional(),
});

export type AliveFieldSignature = z.infer<typeof aliveFieldSignatureSchema>;

// ═══════════════════════════════════════════════════════════════════════════
// LENS VIEW (tier-filtered presentation)
// ═══════════════════════════════════════════════════════════════════════════

export const aliveLensViewSchema = z.object({
  tier: z.enum(["psychonaut", "academic", "enterprise"]),
  translated: z
    .object({
      pressure: z.number().optional(), // 0..1
      pull: z.number().optional(), // 0..1
      agency_delta: z.number().optional(), // -1..1
      drift_risk: z.number().optional(), // 0..1
      notes: z.array(z.string()).optional(),
    })
    .optional(),
  metrics: aliveFieldSignatureSchema.nullish(), // Psychonaut tier receives null
  explanations: z
    .array(
      z.object({
        metric_id: z.string(),
        summary: z.string(),
        details: z.array(z.string()).optional(),
      })
    )
    .optional(),
  alerts: z
    .array(
      z.object({
        code: z.string(),
        severity: z.enum(["info", "notice", "warning", "critical"]),
        message: z.string(),
        recommended_next: z.array(z.string()).optional(),
      })
    )
    .optional(),
});

export type AliveLensView = z.infer<typeof aliveLensViewSchema>;

// ═══════════════════════════════════════════════════════════════════════════
// STRAIN SIGNAL
// ═══════════════════════════════════════════════════════════════════════════

export const aliveStrainSignalSchema = z.object({
  signal_id: z.string(), // uuid
  severity: z.enum(["info", "notice", "warning", "critical"]),
  description: z.string(),
  conflicting_metrics: z.array(z.string()).optional(),
  unexplained_variance: z.number().optional(), // 0..1
  suggested_new_dimension: z
    .object({
      working_name: z.string(),
      measures: z.string(),
      candidate_axis: z.enum(["influence", "vitality", "life_logistics", "cross_axis"]),
      candidate_buckets: z.array(z.string()).optional(),
    })
    .optional(),
});

export type AliveStrainSignal = z.infer<typeof aliveStrainSignalSchema>;

// ═══════════════════════════════════════════════════════════════════════════
// RUN RESULT (canonical output)
// ═══════════════════════════════════════════════════════════════════════════

export const aliveRunResultSchema = z.object({
  provenance: aliveProvenanceSchema,
  artifact: aliveArtifactRefSchema,
  signature: aliveFieldSignatureSchema,
  view: aliveLensViewSchema,
  strain: z
    .object({
      signals: z.array(aliveStrainSignalSchema),
      notes: z.array(z.string()).optional(),
    })
    .optional(),
});

export type AliveRunResult = z.infer<typeof aliveRunResultSchema>;

// ═══════════════════════════════════════════════════════════════════════════
// INPUT SCHEMA
// ═══════════════════════════════════════════════════════════════════════════

export const aliveRunInputSchema = z.object({
  artifact: aliveArtifactRefSchema,
  tier: z.enum(["psychonaut", "academic", "enterprise"]),
  profile: z.record(z.any()).optional(), // Onboarding-derived weights
});

export type AliveRunInput = z.infer<typeof aliveRunInputSchema>;
