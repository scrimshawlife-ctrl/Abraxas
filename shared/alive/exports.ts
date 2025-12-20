import { z } from "zod";
import { ALIVETier } from "./tier-policy";

/**
 * ALIVE Export Manifests
 *
 * Defines export formats and integration payloads per tier.
 */

// ═══════════════════════════════════════════════════════════════════════════
// EXPORT FORMAT SCHEMAS
// ═══════════════════════════════════════════════════════════════════════════

export const exportRequestSchema = z.object({
  analysisId: z.string(),
  format: z.enum(["json", "csv", "pdf"]),
  tier: z.enum(["psychonaut", "academic", "enterprise"]),
  options: z.object({
    includeProvenance: z.boolean().default(false),
    includeStrainReport: z.boolean().default(false),
  }).optional(),
});

export const exportResponseSchema = z.object({
  exportId: z.string(),
  format: z.string(),
  downloadUrl: z.string(),
  expiresAt: z.string().datetime(),
  createdAt: z.string().datetime(),
});

// ═══════════════════════════════════════════════════════════════════════════
// INTEGRATION SCHEMAS
// ═══════════════════════════════════════════════════════════════════════════

// Slack integration (enterprise only)
export const slackIntegrationSchema = z.object({
  enabled: z.boolean(),
  webhookUrl: z.string().url(),
  channel: z.string(),
  notifyOn: z.object({
    analysisComplete: z.boolean().default(true),
    metricStrain: z.boolean().default(true),
    anomalyDetected: z.boolean().default(false),
  }),
});

// Email integration (enterprise only)
export const emailIntegrationSchema = z.object({
  enabled: z.boolean(),
  recipients: z.array(z.string().email()),
  notifyOn: z.object({
    analysisComplete: z.boolean().default(true),
    metricStrain: z.boolean().default(true),
  }),
});

// Webhook integration (enterprise only)
export const webhookIntegrationSchema = z.object({
  enabled: z.boolean(),
  url: z.string().url(),
  secret: z.string().optional(),
  events: z.array(z.enum(["analysis.complete", "metric.strain", "export.ready"])),
});

// ═══════════════════════════════════════════════════════════════════════════
// INTEGRATION MANIFEST
// ═══════════════════════════════════════════════════════════════════════════

export const integrationManifestSchema = z.object({
  userId: z.string(),
  tier: z.enum(["psychonaut", "academic", "enterprise"]),
  slack: slackIntegrationSchema.optional(),
  email: emailIntegrationSchema.optional(),
  webhook: webhookIntegrationSchema.optional(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});

// ═══════════════════════════════════════════════════════════════════════════
// EXPORT TYPES
// ═══════════════════════════════════════════════════════════════════════════

export type ExportRequest = z.infer<typeof exportRequestSchema>;
export type ExportResponse = z.infer<typeof exportResponseSchema>;
export type SlackIntegration = z.infer<typeof slackIntegrationSchema>;
export type EmailIntegration = z.infer<typeof emailIntegrationSchema>;
export type WebhookIntegration = z.infer<typeof webhookIntegrationSchema>;
export type IntegrationManifest = z.infer<typeof integrationManifestSchema>;
