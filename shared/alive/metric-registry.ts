/**
 * ALIVE Metric Registry
 *
 * Central registry of all ALIVE metrics with tier-specific copy.
 * This is the "grammar" that lets ALIVE explain metrics per tier.
 */

import type { AliveMetricAxis, AliveMetricStatus } from "./schema";

export interface AliveMetricRegistryEntry {
  metric_id: string; // "IM.NCR"
  axis: AliveMetricAxis;
  name: string;
  status: AliveMetricStatus;
  version: string; // semver
  normalize: { min: number; max: number }; // standardizing assumptions

  tier_copy: {
    psychonaut: { summary: string; prompts?: string[] };
    academic: { summary: string; operational_definition: string; failure_modes?: string[] };
    enterprise: { summary: string; business_risk_notes?: string[]; decision_uses?: string[] };
  };
}

/**
 * ALIVE Metric Registry
 *
 * Start with 2-3 metrics only:
 * - IM.NCR (Narrative Compression Ratio)
 * - VM.GI (Generativity Index) - TODO
 * - LL.LFC (Life-Logistics Friction Coefficient) - TODO
 */
export const ALIVE_METRIC_REGISTRY: AliveMetricRegistryEntry[] = [
  {
    metric_id: "IM.NCR",
    axis: "influence",
    name: "Narrative Compression Ratio",
    status: "promoted",
    version: "1.0.0",
    normalize: { min: 0, max: 1 },
    tier_copy: {
      psychonaut: {
        summary: "How much the message collapses complexity into one frame.",
        prompts: [
          "Notice urgency and certainty spikes.",
          "Track whether alternatives feel impossible.",
        ],
      },
      academic: {
        summary: "Compression of causal complexity into a single explanatory frame.",
        operational_definition:
          "Estimate proportion of claims explained by a single cause/agent; higher implies reduced causal plurality.",
        failure_modes: [
          "Dense but nuanced writing can look compressed.",
          "Satire can spike compression cues.",
        ],
      },
      enterprise: {
        summary: "Single-frame narratives increase short-term alignment but raise long-term brittleness.",
        business_risk_notes: [
          "High NCR can mask operational constraints.",
          "Raises backlash sensitivity if reality diverges.",
        ],
        decision_uses: ["Comms review", "Risk gating on public narratives"],
      },
    },
  },
];

export function getMetricDef(metric_id: string): AliveMetricRegistryEntry | undefined {
  return ALIVE_METRIC_REGISTRY.find((m) => m.metric_id === metric_id);
}

export function getMetricsByAxis(axis: AliveMetricAxis): AliveMetricRegistryEntry[] {
  return ALIVE_METRIC_REGISTRY.filter((m) => m.axis === axis);
}

export function getPromotedMetrics(): AliveMetricRegistryEntry[] {
  return ALIVE_METRIC_REGISTRY.filter((m) => m.status === "promoted");
}

export function getMetricCopy(
  metric_id: string,
  tier: "psychonaut" | "academic" | "enterprise"
): AliveMetricRegistryEntry["tier_copy"][typeof tier] | undefined {
  const metric = getMetricDef(metric_id);
  return metric?.tier_copy[tier];
}
