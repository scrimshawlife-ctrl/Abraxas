/**
 * ALIVE Tier Policy Enforcement
 *
 * Applies tier-based filtering to field signatures.
 * Same analysis, different lens.
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
 * @param signature - Full ALIVE field signature
 * @param tier - User's tier level
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
    compositeScore: signature.compositeScore,
  };

  // Filter metrics based on tier policy
  filtered.influence = filterMetrics(
    signature.influence,
    policy.canViewProvisionalMetrics
  );
  filtered.vitality = filterMetrics(
    signature.vitality,
    policy.canViewProvisionalMetrics
  );
  filtered.lifeLogistics = filterMetrics(
    signature.lifeLogistics,
    policy.canViewProvisionalMetrics
  );

  // Provenance (conditional)
  if (policy.canViewFullProvenance) {
    filtered.corpusProvenance = signature.corpusProvenance;
  } else {
    // Redacted provenance
    filtered.corpusProvenance = signature.corpusProvenance.map((p) => ({
      sourceId: "[redacted]",
      sourceType: p.sourceType,
      weight: p.weight,
      timestamp: p.timestamp,
    }));
  }

  // Metric strain (conditional)
  if (policy.canViewStrainReports && signature.metricStrain) {
    filtered.metricStrain = signature.metricStrain;
  }

  return filtered;
}

/**
 * Filter metrics based on status visibility.
 */
function filterMetrics<T extends { status: string }>(
  metrics: T[],
  includeProvisional: boolean
): T[] {
  if (includeProvisional) {
    return metrics;
  }
  return metrics.filter((m) => m.status === "promoted");
}

/**
 * Check if user can export in given format.
 */
export function canExport(tier: string, format: string): boolean {
  const tierEnum = tier as ALIVETier;
  const policy = getTierExport(tierEnum);
  return policy.allowedFormats.includes(format as any);
}

/**
 * Check if user can use integration.
 */
export function canIntegrate(
  tier: string,
  integration: "slack" | "email" | "webhook" | "api"
): boolean {
  const tierEnum = tier as ALIVETier;
  const integrations = getTierIntegrations(tierEnum);
  return integrations[integration];
}
