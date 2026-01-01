import { z } from "zod";

/**
 * ALIVE Tier Policy
 *
 * Defines what each tier may see, export, and integrate.
 * Same analysis, different lens.
 */

// ═══════════════════════════════════════════════════════════════════════════
// TIER DEFINITIONS
// ═══════════════════════════════════════════════════════════════════════════

export enum ALIVETier {
  PSYCHONAUT = "psychonaut",
  ACADEMIC = "academic",
  ENTERPRISE = "enterprise",
}

// ═══════════════════════════════════════════════════════════════════════════
// VISIBILITY POLICY
// ═══════════════════════════════════════════════════════════════════════════

export interface TierVisibilityPolicy {
  // Metric visibility
  canViewProvisionalMetrics: boolean;
  canViewMetricVersions: boolean;
  canViewStrainReports: boolean;

  // Corpus visibility
  canViewFullProvenance: boolean;
  canViewDecayWeights: boolean;

  // UI depth
  explanationDepth: "minimal" | "moderate" | "comprehensive";
  showInternalMetricIds: boolean;
}

export const TIER_VISIBILITY: Record<ALIVETier, TierVisibilityPolicy> = {
  [ALIVETier.PSYCHONAUT]: {
    canViewProvisionalMetrics: false,
    canViewMetricVersions: false,
    canViewStrainReports: false,
    canViewFullProvenance: false,
    canViewDecayWeights: false,
    explanationDepth: "minimal",
    showInternalMetricIds: false,
  },

  [ALIVETier.ACADEMIC]: {
    canViewProvisionalMetrics: true,
    canViewMetricVersions: true,
    canViewStrainReports: true,
    canViewFullProvenance: true,
    canViewDecayWeights: true,
    explanationDepth: "comprehensive",
    showInternalMetricIds: true,
  },

  [ALIVETier.ENTERPRISE]: {
    canViewProvisionalMetrics: false,
    canViewMetricVersions: false,
    canViewStrainReports: false,
    canViewFullProvenance: false,
    canViewDecayWeights: false,
    explanationDepth: "moderate",
    showInternalMetricIds: false,
  },
};

// ═══════════════════════════════════════════════════════════════════════════
// EXPORT POLICY
// ═══════════════════════════════════════════════════════════════════════════

export interface TierExportPolicy {
  allowedFormats: ("json" | "csv" | "pdf")[];
  allowIntegrations: boolean;
  maxExportsPerDay: number | null; // null = unlimited
}

export const TIER_EXPORT: Record<ALIVETier, TierExportPolicy> = {
  [ALIVETier.PSYCHONAUT]: {
    allowedFormats: ["json"],
    allowIntegrations: false,
    maxExportsPerDay: 10,
  },

  [ALIVETier.ACADEMIC]: {
    allowedFormats: ["json", "csv"],
    allowIntegrations: false,
    maxExportsPerDay: 100,
  },

  [ALIVETier.ENTERPRISE]: {
    allowedFormats: ["json", "csv", "pdf"],
    allowIntegrations: true,
    maxExportsPerDay: null, // unlimited
  },
};

// ═══════════════════════════════════════════════════════════════════════════
// INTEGRATION POLICY
// ═══════════════════════════════════════════════════════════════════════════

export interface TierIntegrationPolicy {
  slack: boolean;
  email: boolean;
  webhook: boolean;
  api: boolean;
}

export const TIER_INTEGRATIONS: Record<ALIVETier, TierIntegrationPolicy> = {
  [ALIVETier.PSYCHONAUT]: {
    slack: false,
    email: false,
    webhook: false,
    api: false,
  },

  [ALIVETier.ACADEMIC]: {
    slack: false,
    email: false,
    webhook: false,
    api: true, // API access for research
  },

  [ALIVETier.ENTERPRISE]: {
    slack: true,
    email: true,
    webhook: true,
    api: true,
  },
};

// ═══════════════════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

export function getTierVisibility(tier: ALIVETier): TierVisibilityPolicy {
  return TIER_VISIBILITY[tier];
}

export function getTierExport(tier: ALIVETier): TierExportPolicy {
  return TIER_EXPORT[tier];
}

export function getTierIntegrations(tier: ALIVETier): TierIntegrationPolicy {
  return TIER_INTEGRATIONS[tier];
}

export function canExportFormat(tier: ALIVETier, format: string): boolean {
  return TIER_EXPORT[tier].allowedFormats.includes(format as any);
}

export function canUseIntegration(tier: ALIVETier, integration: keyof TierIntegrationPolicy): boolean {
  return TIER_INTEGRATIONS[tier][integration];
}
