/**
 * ABRAXAS SLANG ENGINE - Main Orchestrator
 * Operating modes: OPEN, ALIGN, ASCEND, CLEAR, SEAL
 *
 * @module abraxas/slang_engine
 * @deterministic true
 * @capabilities { read: ["signals", "archive"], write: ["signals", "ledger"], network: false }
 * @version 1.0.0
 *
 * Philosophy: Passive organ. Observes. Does not speak unless queried.
 */

import crypto from "crypto";
import type {
  SlangSignal,
  ArchivedSignal,
  EngineState,
  OperatingMode,
  SlangProvenance,
  NarrativeDebtIndex,
  DriftAlert,
  SlangClass,
} from "./schema";
import { DEFAULT_DECAY_PROFILES, getDefaultHalfLife } from "./schema";
import {
  enrichSignal,
  computeSignalFields,
  generatePressureVector,
  computeFrequencyIndex,
  computeConfidence,
  type ObservationWindow,
} from "./signal-processor";
import {
  applyDecay,
  processDecayBatch,
  archiveSignal,
  shouldResurrect,
  resurrectSignal,
  applySurvivalBoost,
  type SurvivalFactors,
} from "./decay";
import {
  validateSignal,
  validateBatch,
  passesValidation,
  type BatchValidationResult,
} from "./gates";
import {
  modulateOracleConfidence,
  generateDriftAlerts,
  computeNarrativeDebt,
  generateMemeticPressureTrends,
  validateCompressionEfficacy,
} from "./kernel-hooks";

// Re-export types for external use
export * from "./schema";
export * from "./signal-processor";
export * from "./decay";
export * from "./gates";
export * from "./kernel-hooks";

// ═══════════════════════════════════════════════════════════════════════════
// Engine State Management
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Initializes a new engine state
 */
export function initializeEngine(mode: OperatingMode = "OPEN"): EngineState {
  return {
    mode,
    active_signals: [],
    archived_signals: [],
    narrative_debt: {
      timestamp: new Date().toISOString(),
      total_unspoken_load: 0,
      system_stress_level: 0,
      critical_signals: [],
      trend: "stable",
    },
    drift_alerts: [],
  };
}

/**
 * Generates deterministic hash for provenance
 */
function generateProvenanceHash(state: EngineState, seed: string): string {
  const stateString = JSON.stringify({
    active_signals: state.active_signals.map((s) => s.term).sort(),
    archived_count: state.archived_signals.length,
    narrative_debt: state.narrative_debt.system_stress_level,
    seed,
  });

  return crypto.createHash("sha256").update(stateString).digest("hex");
}

// ═══════════════════════════════════════════════════════════════════════════
// OPERATING MODE: OPEN
// Detect new signals with strict gates
// ═══════════════════════════════════════════════════════════════════════════

export interface OpenModeInput {
  candidate_signals: Partial<SlangSignal>[];
  seed: string;
  noise_threshold?: number;
}

export interface OpenModeOutput {
  accepted: SlangSignal[];
  rejected: Array<{
    signal: Partial<SlangSignal>;
    reason: string;
  }>;
  validation_stats: BatchValidationResult["stats"];
}

/**
 * OPEN mode: Detect and validate new slang signals
 */
export function executeOpenMode(
  state: EngineState,
  input: OpenModeInput
): { state: EngineState; output: OpenModeOutput } {
  const { candidate_signals, seed, noise_threshold } = input;

  // Enrich candidates with computed fields
  const enrichedCandidates: SlangSignal[] = candidate_signals.map((candidate) => {
    // Ensure required fields
    const term = candidate.term || "unknown";
    const signalClass = candidate.class || "meaning_inflation";
    const definition = candidate.definition || "";
    const origin_context = candidate.origin_context || "unknown";
    const timestamp_first_seen = candidate.timestamp_first_seen || new Date().toISOString();
    const frequency_index = candidate.frequency_index ?? 0.5;
    const pressure_vector = candidate.pressure_vector || generatePressureVector(term, seed);
    const decay_halflife_days =
      candidate.decay_halflife_days ?? getDefaultHalfLife(signalClass);

    const signal: SlangSignal = {
      term,
      class: signalClass,
      definition,
      origin_context,
      pressure_vector,
      symptoms: candidate.symptoms || [],
      hygiene: candidate.hygiene,
      timestamp_first_seen,
      decay_halflife_days,
      frequency_index,
      signal_strength: 0, // Will be computed
      confidence: 0, // Will be computed
      novelty: 0, // Will be computed
      links: candidate.links,
      id: candidate.id || `${term}-${Date.now()}`,
    };

    return enrichSignal(signal, seed, state.active_signals);
  });

  // Validate batch
  const validationResult = validateBatch(enrichedCandidates, {
    noiseThreshold: noise_threshold,
    enableAdoption: false, // Always disabled
  });

  // Update confidence for accepted signals
  const accepted = validationResult.passed.map((signal) => {
    const confidence = computeConfidence(signal, 10, 1); // Default values
    return { ...signal, confidence };
  });

  const rejected = validationResult.failed.map((failure) => ({
    signal: failure.signal,
    reason: failure.failures.join("; "),
  }));

  // Update state
  const newState: EngineState = {
    ...state,
    active_signals: [...state.active_signals, ...accepted],
  };

  return {
    state: newState,
    output: {
      accepted,
      rejected,
      validation_stats: validationResult.stats,
    },
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// OPERATING MODE: ALIGN
// Validate pressure vectors and compression
// ═══════════════════════════════════════════════════════════════════════════

export interface AlignModeOutput {
  revalidated: SlangSignal[];
  compression_issues: Array<{
    signal_id: string;
    term: string;
    issue: string;
  }>;
  pressure_anomalies: Array<{
    signal_id: string;
    term: string;
    anomaly: string;
  }>;
}

/**
 * ALIGN mode: Validate pressure vectors and compression quality
 */
export function executeAlignMode(
  state: EngineState,
  seed: string
): { state: EngineState; output: AlignModeOutput } {
  const compressionValidations = validateCompressionEfficacy(state.active_signals);

  const compression_issues = compressionValidations
    .filter((v) => v.is_bloated)
    .map((v) => ({
      signal_id: v.signal_id,
      term: v.term,
      issue: v.recommendation,
    }));

  // Check for pressure anomalies (unusually low or high pressure)
  const pressure_anomalies: AlignModeOutput["pressure_anomalies"] = [];

  state.active_signals.forEach((signal) => {
    const pressureMag = Math.sqrt(
      signal.pressure_vector.cognitive ** 2 +
        signal.pressure_vector.social ** 2 +
        signal.pressure_vector.economic ** 2 +
        signal.pressure_vector.temporal ** 2 +
        signal.pressure_vector.identity ** 2
    );

    if (pressureMag < 0.1) {
      pressure_anomalies.push({
        signal_id: signal.id || signal.term,
        term: signal.term,
        anomaly: "Pressure magnitude unusually low",
      });
    } else if (pressureMag > 2.0) {
      pressure_anomalies.push({
        signal_id: signal.id || signal.term,
        term: signal.term,
        anomaly: "Pressure magnitude unusually high",
      });
    }
  });

  // Revalidate all signals
  const revalidated = state.active_signals.map((signal) =>
    enrichSignal(signal, seed, state.active_signals)
  );

  const newState: EngineState = {
    ...state,
    active_signals: revalidated,
  };

  return {
    state: newState,
    output: {
      revalidated,
      compression_issues,
      pressure_anomalies,
    },
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// OPERATING MODE: ASCEND
// Wire into forecasts and drift metrics
// ═══════════════════════════════════════════════════════════════════════════

export interface AscendModeInput {
  oracle_metrics?: any; // SymbolicMetrics from Oracle
  prior_snapshot?: SlangSignal[];
  forecast_horizon_days?: number;
}

export interface AscendModeOutput {
  oracle_modulation: ReturnType<typeof modulateOracleConfidence>;
  drift_alerts: DriftAlert[];
  narrative_debt: NarrativeDebtIndex;
  memetic_pressure_trends: ReturnType<typeof generateMemeticPressureTrends>;
}

/**
 * ASCEND mode: Integrate with Oracle, Memetic, and forecast systems
 */
export function executeAscendMode(
  state: EngineState,
  input: AscendModeInput
): { state: EngineState; output: AscendModeOutput } {
  const oracle_modulation = modulateOracleConfidence(
    input.oracle_metrics || ({} as any),
    state.active_signals
  );

  const drift_alerts = generateDriftAlerts(
    state.active_signals,
    input.prior_snapshot
  );

  const narrative_debt = computeNarrativeDebt(state.active_signals);

  const memetic_pressure_trends = generateMemeticPressureTrends(
    state.active_signals,
    input.forecast_horizon_days || 30
  );

  // Update state with new metrics
  const newState: EngineState = {
    ...state,
    drift_alerts: [...state.drift_alerts, ...drift_alerts],
    narrative_debt,
  };

  return {
    state: newState,
    output: {
      oracle_modulation,
      drift_alerts,
      narrative_debt,
      memetic_pressure_trends,
    },
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// OPERATING MODE: CLEAR
// Decay, suppress, archive
// ═══════════════════════════════════════════════════════════════════════════

export interface ClearModeOutput {
  decayed: SlangSignal[];
  archived: ArchivedSignal[];
  resurrected: Array<{
    signal: SlangSignal;
    event: any;
  }>;
  decay_stats: ReturnType<typeof processDecayBatch>["decayStats"];
}

/**
 * CLEAR mode: Apply decay, archive weak signals, resurrect if needed
 */
export function executeClearMode(
  state: EngineState
): { state: EngineState; output: ClearModeOutput } {
  // Process decay
  const { updated, toArchive, decayStats } = processDecayBatch(state.active_signals);

  // Archive weak signals
  const archived = toArchive.map((signal) =>
    archiveSignal(signal, "Auto-archive: signal strength below threshold")
  );

  // Check for resurrections (simplified - would need actual new data)
  const resurrected: ClearModeOutput["resurrected"] = [];

  const newState: EngineState = {
    ...state,
    active_signals: updated,
    archived_signals: [...state.archived_signals, ...archived],
  };

  return {
    state: newState,
    output: {
      decayed: updated,
      archived,
      resurrected,
      decay_stats: decayStats,
    },
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// OPERATING MODE: SEAL
// Ledger write, provenance hash, version bump
// ═══════════════════════════════════════════════════════════════════════════

export interface SealModeInput {
  seed: string;
  sources: string[];
  version?: string;
}

export interface SealModeOutput {
  provenance: SlangProvenance;
  ledger_entry: {
    timestamp: string;
    hash: string;
    active_signal_count: number;
    archived_signal_count: number;
  };
}

/**
 * SEAL mode: Finalize state with provenance and ledger entry
 */
export function executeSealMode(
  state: EngineState,
  input: SealModeInput
): { state: EngineState; output: SealModeOutput } {
  const { seed, sources, version = "1.0.0" } = input;

  const timestamp = new Date().toISOString();
  const deterministicHash = generateProvenanceHash(state, seed);

  const provenance: SlangProvenance = {
    seed,
    timestamp,
    sources,
    version,
    deterministic_hash: deterministicHash,
  };

  const ledger_entry = {
    timestamp,
    hash: deterministicHash,
    active_signal_count: state.active_signals.length,
    archived_signal_count: state.archived_signals.length,
  };

  const newState: EngineState = {
    ...state,
    last_seal_timestamp: timestamp,
    provenance_hash: deterministicHash,
  };

  return {
    state: newState,
    output: {
      provenance,
      ledger_entry,
    },
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Unified Engine Execution
// ═══════════════════════════════════════════════════════════════════════════

export interface EngineExecutionInput {
  mode: OperatingMode;
  state: EngineState;
  params: any; // Mode-specific parameters
}

export interface EngineExecutionOutput {
  state: EngineState;
  result: any; // Mode-specific output
  mode: OperatingMode;
}

/**
 * Unified engine execution across all modes
 */
export function executeEngine(input: EngineExecutionInput): EngineExecutionOutput {
  const { mode, state, params } = input;

  switch (mode) {
    case "OPEN": {
      const result = executeOpenMode(state, params);
      return { state: result.state, result: result.output, mode };
    }

    case "ALIGN": {
      const result = executeAlignMode(state, params.seed);
      return { state: result.state, result: result.output, mode };
    }

    case "ASCEND": {
      const result = executeAscendMode(state, params);
      return { state: result.state, result: result.output, mode };
    }

    case "CLEAR": {
      const result = executeClearMode(state);
      return { state: result.state, result: result.output, mode };
    }

    case "SEAL": {
      const result = executeSealMode(state, params);
      return { state: result.state, result: result.output, mode };
    }

    default:
      throw new Error(`Unknown operating mode: ${mode}`);
  }
}
