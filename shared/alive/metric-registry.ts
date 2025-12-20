import { z } from "zod";

/**
 * ALIVE Metric Registry
 *
 * Central registry of all ALIVE metrics with IDs, versions, and lifecycle status.
 * Supports metric evolution: provisional → shadowed → promoted.
 */

// ═══════════════════════════════════════════════════════════════════════════
// METRIC STATUS LIFECYCLE
// ═══════════════════════════════════════════════════════════════════════════

export enum MetricStatus {
  PROVISIONAL = "provisional", // New metric, under evaluation
  SHADOWED = "shadowed",       // Running in shadow mode, not affecting scores
  PROMOTED = "promoted",        // Promoted to production, affects composite scores
}

// ═══════════════════════════════════════════════════════════════════════════
// METRIC AXIS
// ═══════════════════════════════════════════════════════════════════════════

export enum MetricAxis {
  INFLUENCE = "influence",           // I axis
  VITALITY = "vitality",            // V axis
  LIFE_LOGISTICS = "life_logistics", // L axis
}

// ═══════════════════════════════════════════════════════════════════════════
// METRIC DEFINITION
// ═══════════════════════════════════════════════════════════════════════════

export interface MetricDefinition {
  metricId: string;           // e.g., "influence.network_position"
  metricVersion: string;      // Semver: "1.0.0", "1.1.0", etc.
  axis: MetricAxis;
  status: MetricStatus;
  name: string;
  description: string;

  // Computation metadata
  computationModule: string;  // Python module path
  dependencies: string[];     // Other metric IDs this depends on

  // Lifecycle
  createdAt: string;
  promotedAt?: string;
  deprecatedAt?: string;

  // Versioning
  previousVersion?: string;
  nextVersion?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// METRIC REGISTRY (seed with initial metrics)
// ═══════════════════════════════════════════════════════════════════════════

export const METRIC_REGISTRY: MetricDefinition[] = [
  // ─────────────────────────────────────────────────────────────────────────
  // INFLUENCE METRICS (I)
  // ─────────────────────────────────────────────────────────────────────────
  {
    metricId: "influence.network_position",
    metricVersion: "1.0.0",
    axis: MetricAxis.INFLUENCE,
    status: MetricStatus.PROMOTED,
    name: "Network Position",
    description: "Measures centrality and reach within social network graph",
    computationModule: "abraxas.alive.metrics.influence.network_position",
    dependencies: [],
    createdAt: new Date().toISOString(),
  },

  {
    metricId: "influence.persuasive_reach",
    metricVersion: "1.0.0",
    axis: MetricAxis.INFLUENCE,
    status: MetricStatus.PROMOTED,
    name: "Persuasive Reach",
    description: "Capacity to shift opinion and activate discourse",
    computationModule: "abraxas.alive.metrics.influence.persuasive_reach",
    dependencies: ["influence.network_position"],
    createdAt: new Date().toISOString(),
  },

  // ─────────────────────────────────────────────────────────────────────────
  // VITALITY METRICS (V)
  // ─────────────────────────────────────────────────────────────────────────
  {
    metricId: "vitality.creative_momentum",
    metricVersion: "1.0.0",
    axis: MetricAxis.VITALITY,
    status: MetricStatus.PROMOTED,
    name: "Creative Momentum",
    description: "Sustained creative output velocity and consistency",
    computationModule: "abraxas.alive.metrics.vitality.creative_momentum",
    dependencies: [],
    createdAt: new Date().toISOString(),
  },

  {
    metricId: "vitality.discourse_velocity",
    metricVersion: "1.0.0",
    axis: MetricAxis.VITALITY,
    status: MetricStatus.PROMOTED,
    name: "Discourse Velocity",
    description: "Rate of participation in active discourse threads",
    computationModule: "abraxas.alive.metrics.vitality.discourse_velocity",
    dependencies: [],
    createdAt: new Date().toISOString(),
  },

  {
    metricId: "vitality.engagement_coherence",
    metricVersion: "1.0.0",
    axis: MetricAxis.VITALITY,
    status: MetricStatus.PROMOTED,
    name: "Engagement Coherence",
    description: "Consistency and quality of engagement over time",
    computationModule: "abraxas.alive.metrics.vitality.engagement_coherence",
    dependencies: ["vitality.discourse_velocity"],
    createdAt: new Date().toISOString(),
  },

  // ─────────────────────────────────────────────────────────────────────────
  // LIFE-LOGISTICS METRICS (L)
  // ─────────────────────────────────────────────────────────────────────────
  {
    metricId: "life_logistics.time_debt",
    metricVersion: "1.0.0",
    axis: MetricAxis.LIFE_LOGISTICS,
    status: MetricStatus.PROMOTED,
    name: "Time Debt",
    description: "Obligation load vs. available capacity (inverted score)",
    computationModule: "abraxas.alive.metrics.life_logistics.time_debt",
    dependencies: [],
    createdAt: new Date().toISOString(),
  },

  {
    metricId: "life_logistics.material_runway",
    metricVersion: "1.0.0",
    axis: MetricAxis.LIFE_LOGISTICS,
    status: MetricStatus.PROMOTED,
    name: "Material Runway",
    description: "Financial stability and resource access horizon",
    computationModule: "abraxas.alive.metrics.life_logistics.material_runway",
    dependencies: [],
    createdAt: new Date().toISOString(),
  },

  {
    metricId: "life_logistics.operational_friction",
    metricVersion: "1.0.0",
    axis: MetricAxis.LIFE_LOGISTICS,
    status: MetricStatus.PROMOTED,
    name: "Operational Friction",
    description: "Drag from systemic constraints (health, care, bureaucracy)",
    computationModule: "abraxas.alive.metrics.life_logistics.operational_friction",
    dependencies: [],
    createdAt: new Date().toISOString(),
  },
];

// ═══════════════════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

export function getMetric(metricId: string, version?: string): MetricDefinition | undefined {
  if (version) {
    return METRIC_REGISTRY.find(m => m.metricId === metricId && m.metricVersion === version);
  }
  // Get latest promoted version
  const metrics = METRIC_REGISTRY.filter(m => m.metricId === metricId && m.status === MetricStatus.PROMOTED);
  return metrics.sort((a, b) => b.metricVersion.localeCompare(a.metricVersion))[0];
}

export function getMetricsByAxis(axis: MetricAxis, status?: MetricStatus): MetricDefinition[] {
  let metrics = METRIC_REGISTRY.filter(m => m.axis === axis);
  if (status) {
    metrics = metrics.filter(m => m.status === status);
  }
  return metrics;
}

export function getPromotedMetrics(): MetricDefinition[] {
  return METRIC_REGISTRY.filter(m => m.status === MetricStatus.PROMOTED);
}

export function getProvisionalMetrics(): MetricDefinition[] {
  return METRIC_REGISTRY.filter(m => m.status === MetricStatus.PROVISIONAL);
}
