/**
 * ALIVE Tier Policy Enforcement
 *
 * CRITICAL: Server-side enforcement. Client NEVER decides what a tier can see.
 * This protects against accidental overexposure and client-side tampering.
 *
 * Tier filtering must happen server-side before data leaves the API.
 */

import type { ALIVEFieldSignature } from "@shared/alive/schema";
import {
  getTierVisibility,
  getTierExport,
  getTierIntegrations,
  ALIVETier,
} from "@shared/alive/tier-policy";

/**
 * Apply tier-based filtering to field signature.
 *
 * SECURITY: This function MUST be called before returning data to client.
 *
 * @param signature - Full ALIVE field signature
 * @param tier - User's tier level (validated server-side)
 * @returns Filtered view according to tier policy
 */
export function applyTierFilter(
  signature: ALIVEFieldSignature,
  tier: string
): Partial<ALIVEFieldSignature> {
  const tierEnum = tier as ALIVETier;
  const policy = getTierVisibility(tierEnum);

  // Base fields (always included)
  const filtered: Partial<ALIVEFieldSignature> = {
    analysisId: signature.analysisId,
    subjectId: signature.subjectId,
    timestamp: signature.timestamp,
    schemaVersion: signature.schemaVersion,
    compositeScore: signature.compositeScore,
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // METRIC FILTERING (status-based)
  // ═══════════════════════════════════════════════════════════════════════════

  filtered.influence = filterMetrics(
    signature.influence,
    policy.canViewProvisionalMetrics,
    policy.showInternalMetricIds
  );

  filtered.vitality = filterMetrics(
    signature.vitality,
    policy.canViewProvisionalMetrics,
    policy.showInternalMetricIds
  );

  filtered.lifeLogistics = filterMetrics(
    signature.lifeLogistics,
    policy.canViewProvisionalMetrics,
    policy.showInternalMetricIds
  );

  // ═══════════════════════════════════════════════════════════════════════════
  // PROVENANCE FILTERING (redaction for non-academic tiers)
  // ═══════════════════════════════════════════════════════════════════════════

  if (policy.canViewFullProvenance) {
    // Academic: full provenance visibility
    filtered.corpusProvenance = signature.corpusProvenance;
  } else {
    // Psychonaut/Enterprise: redacted provenance
    filtered.corpusProvenance = signature.corpusProvenance.map((p) => ({
      sourceId: "[redacted]",
      sourceType: p.sourceType,
      weight: p.weight,
      timestamp: p.timestamp,
    }));
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // METRIC STRAIN (academic only)
  // ═══════════════════════════════════════════════════════════════════════════

  if (policy.canViewStrainReports && signature.metricStrain) {
    filtered.metricStrain = signature.metricStrain;
  } else {
    // Strip metric strain for non-academic tiers
    filtered.metricStrain = undefined;
  }

  return filtered;
}

/**
 * Filter metrics based on status visibility and internal ID exposure.
 *
 * @param metrics - Array of metrics
 * @param includeProvisional - Include provisional/shadowed metrics
 * @param showMetricIds - Show full metric IDs (academic only)
 */
function filterMetrics<T extends { status: string; metricId?: string }>(
  metrics: T[],
  includeProvisional: boolean,
  showMetricIds: boolean
): T[] {
  let filtered = metrics;

  // Filter by status
  if (!includeProvisional) {
    filtered = filtered.filter((m) => m.status === "promoted");
  }

  // Redact metric IDs for non-academic tiers
  if (!showMetricIds) {
    filtered = filtered.map((m) => {
      const redacted = { ...m };
      if (redacted.metricId) {
        // Keep only the last part of the metric ID (e.g., "network_position")
        const parts = redacted.metricId.split(".");
        redacted.metricId = parts[parts.length - 1];
      }
      return redacted;
    });
  }

  return filtered;
}

/**
 * Check if user can export in given format.
 *
 * SECURITY: Validate export permissions server-side.
 */
export function canExport(tier: string, format: string): boolean {
  const tierEnum = tier as ALIVETier;
  const policy = getTierExport(tierEnum);
  return policy.allowedFormats.includes(format as any);
}

/**
 * Check if user can use integration.
 *
 * SECURITY: Validate integration permissions server-side.
 */
export function canIntegrate(
  tier: string,
  integration: "slack" | "email" | "webhook" | "api"
): boolean {
  const tierEnum = tier as ALIVETier;
  const integrations = getTierIntegrations(tierEnum);
  return integrations[integration];
}

/**
 * Validate tier string against allowed values.
 *
 * SECURITY: Always validate tier before using it.
 */
export function validateTier(tier: string): tier is ALIVETier {
  return ["psychonaut", "academic", "enterprise"].includes(tier);
}

/**
 * Get user's tier from session/database.
 *
 * TODO: Implement actual user tier lookup from database.
 * For now, returns psychonaut as default.
 *
 * SECURITY: NEVER trust tier from client request. Always look it up server-side.
 */
export async function getUserTier(userId: string): Promise<ALIVETier> {
  // TODO: Look up from database
  // const user = await db.users.findOne({ id: userId });
  // return user.tier || ALIVETier.PSYCHONAUT;

  return ALIVETier.PSYCHONAUT;
}
