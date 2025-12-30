/**
 * ABRAXAS SLANG ENGINE - Core Schema Definition
 * Treats slang as pressure exhaust—language where reality leaks first.
 *
 * @module abraxas/slang_engine/schema
 * @entropy_class high
 * @deterministic true
 * @capabilities { read: ["linguistic_patterns"], write: ["slang_signals"], network: false }
 * @version 1.0.0
 */

// ═══════════════════════════════════════════════════════════════════════════
// Slang Signal Class Taxonomy
// ═══════════════════════════════════════════════════════════════════════════

export type SlangClass =
  | "unspoken_load"        // Pressure from things that can't be directly said
  | "cognitive_drift"      // Shift in how people think/process information
  | "ritual_avoidance"     // Euphemisms for uncomfortable realities
  | "meaning_inflation"    // Rapid semantic devaluation
  | "status_compression"   // Flattening of hierarchies via language
  | "temporal_fugue";      // Time perception distortions

// ═══════════════════════════════════════════════════════════════════════════
// Pressure Vector Components
// ═══════════════════════════════════════════════════════════════════════════

export interface PressureVector {
  cognitive: number;    // [0,1] Mental load/processing strain
  social: number;       // [0,1] Interpersonal/status pressure
  economic: number;     // [0,1] Financial/material stress
  temporal: number;     // [0,1] Time scarcity/urgency
  identity: number;     // [0,1] Self-concept instability
}

// ═══════════════════════════════════════════════════════════════════════════
// Core SlangSignal Entity
// ═══════════════════════════════════════════════════════════════════════════

export interface SlangSignal {
  // Identity
  term: string;                          // Canonical form, lowercase
  class: SlangClass;                     // Signal taxonomy

  // Definition & Context
  definition: string;                    // ≤280 chars (compression enforced)
  origin_context: string;                // Platform/scene/domain descriptor

  // Pressure Analysis
  pressure_vector: PressureVector;       // Multidimensional stress mapping
  symptoms: string[];                    // Behavioral tells
  hygiene?: string[];                    // Non-prescriptive interventions (optional)

  // Temporal Dynamics
  timestamp_first_seen: string;          // ISO timestamp
  decay_halflife_days: number;           // Class-specific or computed

  // Signal Metrics (some computed)
  frequency_index: number;               // Rolling window, normalized [0,1]
  signal_strength: number;               // Computed: freq × pressure × novelty
  confidence: number;                    // Bayesian posterior [0,1]
  novelty?: number;                      // 1 - semantic similarity to corpus

  // Cross-References
  links?: {
    oracle_refs?: string[];              // Links to Oracle outputs
    memetic_refs?: string[];             // Links to Memetic nodes
    related_signals?: string[];          // Other SlangSignal IDs
  };

  // Metadata
  id?: string;                           // Unique identifier (auto-generated)
  archived?: boolean;                    // Auto-archive flag
  lineage?: string;                      // Resurrection tracking
  last_updated?: string;                 // ISO timestamp
}

// ═══════════════════════════════════════════════════════════════════════════
// Computed Field Formulas
// ═══════════════════════════════════════════════════════════════════════════

export interface SignalComputedFields {
  signal_strength: number;        // frequency_index × pressure_magnitude × novelty
  pressure_magnitude: number;     // ||pressure_vector|| (L2 norm)
  novelty: number;                // 1 - semantic_similarity_to_corpus
}

// ═══════════════════════════════════════════════════════════════════════════
// Decay Dynamics
// ═══════════════════════════════════════════════════════════════════════════

export interface DecayProfile {
  class: SlangClass;
  default_halflife_days: number;
  survival_boost_multiplier: number;
  archive_threshold: number;          // signal_strength threshold for archival
}

export const DEFAULT_DECAY_PROFILES: Record<SlangClass, DecayProfile> = {
  meaning_inflation: {
    class: "meaning_inflation",
    default_halflife_days: 28,        // 21-35 day range, middle value
    survival_boost_multiplier: 1.5,
    archive_threshold: 0.05,
  },
  unspoken_load: {
    class: "unspoken_load",
    default_halflife_days: 90,        // 60-120 day range
    survival_boost_multiplier: 2.0,
    archive_threshold: 0.03,
  },
  cognitive_drift: {
    class: "cognitive_drift",
    default_halflife_days: 135,       // 90-180 day range
    survival_boost_multiplier: 2.5,
    archive_threshold: 0.02,
  },
  ritual_avoidance: {
    class: "ritual_avoidance",
    default_halflife_days: 45,
    survival_boost_multiplier: 1.8,
    archive_threshold: 0.04,
  },
  status_compression: {
    class: "status_compression",
    default_halflife_days: 60,
    survival_boost_multiplier: 1.7,
    archive_threshold: 0.04,
  },
  temporal_fugue: {
    class: "temporal_fugue",
    default_halflife_days: 30,
    survival_boost_multiplier: 1.6,
    archive_threshold: 0.05,
  },
};

// ═══════════════════════════════════════════════════════════════════════════
// Gate Validation
// ═══════════════════════════════════════════════════════════════════════════

export interface GateResult {
  passed: boolean;
  gate_name: string;
  reason?: string;
  score?: number;
}

export interface GateValidation {
  compression_gate: GateResult;
  noise_gate: GateResult;
  adoption_gate?: GateResult;     // Disabled by default
}

// ═══════════════════════════════════════════════════════════════════════════
// Signal Archive & Resurrection
// ═══════════════════════════════════════════════════════════════════════════

export interface ArchivedSignal extends SlangSignal {
  archived: true;
  archive_timestamp: string;
  archive_reason: string;
}

export interface ResurrectionEvent {
  signal_id: string;
  original_term: string;
  resurrection_timestamp: string;
  pressure_increase_percent: number;
  new_signal_strength: number;
  lineage_tag: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Aggregated Metrics
// ═══════════════════════════════════════════════════════════════════════════

export interface NarrativeDebtIndex {
  timestamp: string;
  total_unspoken_load: number;        // Aggregate of all unspoken_load signals
  system_stress_level: number;        // [0,1] normalized stress
  critical_signals: SlangSignal[];    // High-strength unspoken loads
  trend: "rising" | "stable" | "falling";
}

export interface DriftAlert {
  alert_id: string;
  timestamp: string;
  class: SlangClass;
  frequency_spike: number;            // Percentage increase
  affected_signals: string[];         // Signal IDs
  severity: "low" | "medium" | "high" | "critical";
  recommendation?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Engine Operating Modes
// ═══════════════════════════════════════════════════════════════════════════

export type OperatingMode =
  | "OPEN"      // Detect new signals (strict gates)
  | "ALIGN"     // Validate pressure vectors + compression
  | "ASCEND"    // Wire into forecasts and drift metrics
  | "CLEAR"     // Decay, suppress, archive
  | "SEAL";     // Ledger write, provenance hash, version bump

export interface EngineState {
  mode: OperatingMode;
  active_signals: SlangSignal[];
  archived_signals: ArchivedSignal[];
  narrative_debt: NarrativeDebtIndex;
  drift_alerts: DriftAlert[];
  last_seal_timestamp?: string;
  provenance_hash?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Provenance & Versioning
// ═══════════════════════════════════════════════════════════════════════════

export interface SlangProvenance {
  seed: string;
  timestamp: string;
  sources: string[];                  // Data sources used
  version: string;                    // Engine version
  deterministic_hash: string;         // SHA-256 of state
}

// ═══════════════════════════════════════════════════════════════════════════
// Cross-Feed Interfaces
// ═══════════════════════════════════════════════════════════════════════════

export interface OracleModulation {
  signal_class_pressures: Record<SlangClass, number>;
  confidence_adjustment: number;      // [-0.1, 0.1] adjustment to oracle confidence
  narrative_debt_influence: number;   // System-level stress feedback
}

export interface MemeticPressureTrend {
  class: SlangClass;
  pressure_trend: number[];           // Time series
  forecast_horizon_days: number;
  predicted_peak?: string;            // ISO timestamp
}

// ═══════════════════════════════════════════════════════════════════════════
// Helper Functions
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Gets default half-life for a signal class
 */
export function getDefaultHalfLife(signalClass: SlangClass): number {
  return DEFAULT_DECAY_PROFILES[signalClass].default_halflife_days;
}
