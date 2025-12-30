/**
 * ABRAXAS SLANG ENGINE - Validation Gates
 * Quality filters for signal ingestion and validation
 *
 * @module abraxas/slang_engine/gates
 * @deterministic true
 * @capabilities { read: ["signals"], write: ["validation"], network: false }
 */

import type { SlangSignal, GateResult, GateValidation } from "./schema";

// ═══════════════════════════════════════════════════════════════════════════
// Compression Gate
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Validates that definition compresses meaning effectively
 *
 * Rules:
 * 1. Definition must be ≤280 characters
 * 2. Must contain semantic density (not just restatement)
 * 3. Should replace a paragraph of explanation
 */
export function compressionGate(signal: SlangSignal): GateResult {
  const def = signal.definition;

  // Rule 1: Length check
  if (def.length > 280) {
    return {
      passed: false,
      gate_name: "compression_gate",
      reason: `Definition exceeds 280 characters (${def.length} chars)`,
      score: 0,
    };
  }

  // Rule 2: Semantic density heuristics
  const wordCount = def.split(/\s+/).length;
  const avgWordLength = def.length / wordCount;

  // Too short = likely not explanatory enough
  if (def.length < 30 || wordCount < 5) {
    return {
      passed: false,
      gate_name: "compression_gate",
      reason: "Definition too brief to provide meaningful compression",
      score: def.length / 280,
    };
  }

  // Check for substantive words (not just "the", "a", "is", etc.)
  const substantiveWords = def
    .toLowerCase()
    .split(/\s+/)
    .filter((w) => !["the", "a", "an", "is", "are", "of", "to", "in", "for", "on", "with"].includes(w));

  const substantiveRatio = substantiveWords.length / wordCount;

  if (substantiveRatio < 0.4) {
    return {
      passed: false,
      gate_name: "compression_gate",
      reason: "Definition lacks semantic density",
      score: substantiveRatio,
    };
  }

  // Rule 3: Compression score
  // Good compression: concise but substantive
  const compressionScore =
    (substantiveRatio * 0.5) +
    (Math.min(1, def.length / 200) * 0.3) +
    (Math.min(1, wordCount / 30) * 0.2);

  const passed = compressionScore >= 0.5;

  return {
    passed,
    gate_name: "compression_gate",
    reason: passed ? "Definition meets compression criteria" : "Insufficient compression quality",
    score: compressionScore,
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Noise Gate
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Filters out low-strength, noisy signals
 *
 * Auto-suppresses signals with:
 * 1. signal_strength < threshold
 * 2. Low frequency + low pressure
 * 3. Very low confidence
 */
export function noiseGate(
  signal: SlangSignal,
  threshold: number = 0.15
): GateResult {
  const strength = signal.signal_strength;
  const frequency = signal.frequency_index;
  const confidence = signal.confidence;

  // Condition 1: Signal strength threshold
  if (strength < threshold) {
    return {
      passed: false,
      gate_name: "noise_gate",
      reason: `Signal strength ${strength.toFixed(3)} below threshold ${threshold}`,
      score: strength,
    };
  }

  // Condition 2: Low frequency AND low pressure
  const pressureMag = Math.sqrt(
    signal.pressure_vector.cognitive ** 2 +
    signal.pressure_vector.social ** 2 +
    signal.pressure_vector.economic ** 2 +
    signal.pressure_vector.temporal ** 2 +
    signal.pressure_vector.identity ** 2
  );

  if (frequency < 0.1 && pressureMag < 0.3) {
    return {
      passed: false,
      gate_name: "noise_gate",
      reason: "Low frequency and low pressure combination",
      score: Math.max(frequency, pressureMag),
    };
  }

  // Condition 3: Very low confidence
  if (confidence < 0.2) {
    return {
      passed: false,
      gate_name: "noise_gate",
      reason: `Confidence ${confidence.toFixed(3)} too low`,
      score: confidence,
    };
  }

  // Calculate overall noise score
  const noiseScore = (strength * 0.5) + (confidence * 0.3) + (frequency * 0.2);

  return {
    passed: true,
    gate_name: "noise_gate",
    reason: "Signal passes noise filters",
    score: noiseScore,
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Adoption Gate (Disabled by Default)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Checks if signal should be promoted/adopted
 * DISABLED BY DEFAULT - no promotion philosophy
 *
 * Only use if explicitly enabled for specific use cases
 */
export function adoptionGate(
  signal: SlangSignal,
  enabled: boolean = false
): GateResult {
  if (!enabled) {
    return {
      passed: false,
      gate_name: "adoption_gate",
      reason: "Adoption gate disabled by default (no promotion)",
      score: 0,
    };
  }

  // If enabled, check adoption worthiness
  const strength = signal.signal_strength;
  const confidence = signal.confidence;
  const frequency = signal.frequency_index;

  const adoptionScore = (strength * 0.4) + (confidence * 0.4) + (frequency * 0.2);

  // Very high bar for adoption
  const passed = adoptionScore >= 0.8;

  return {
    passed,
    gate_name: "adoption_gate",
    reason: passed ? "Signal meets adoption criteria" : "Below adoption threshold",
    score: adoptionScore,
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Unified Validation
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Runs all validation gates on a signal
 */
export function validateSignal(
  signal: SlangSignal,
  options: {
    noiseThreshold?: number;
    enableAdoption?: boolean;
  } = {}
): GateValidation {
  const compressionResult = compressionGate(signal);
  const noiseResult = noiseGate(signal, options.noiseThreshold);
  const adoptionResult = options.enableAdoption
    ? adoptionGate(signal, true)
    : undefined;

  return {
    compression_gate: compressionResult,
    noise_gate: noiseResult,
    adoption_gate: adoptionResult,
  };
}

/**
 * Checks if signal passes all required gates
 */
export function passesValidation(validation: GateValidation): boolean {
  const requiredGates = [validation.compression_gate, validation.noise_gate];

  return requiredGates.every((gate) => gate.passed);
}

// ═══════════════════════════════════════════════════════════════════════════
// Batch Validation
// ═══════════════════════════════════════════════════════════════════════════

export interface BatchValidationResult {
  passed: SlangSignal[];
  failed: Array<{
    signal: SlangSignal;
    validation: GateValidation;
    failures: string[];
  }>;
  stats: {
    totalProcessed: number;
    passRate: number;
    compressionFailures: number;
    noiseFailures: number;
  };
}

/**
 * Validates a batch of signals
 */
export function validateBatch(
  signals: SlangSignal[],
  options: {
    noiseThreshold?: number;
    enableAdoption?: boolean;
  } = {}
): BatchValidationResult {
  const passed: SlangSignal[] = [];
  const failed: BatchValidationResult["failed"] = [];
  let compressionFailures = 0;
  let noiseFailures = 0;

  for (const signal of signals) {
    const validation = validateSignal(signal, options);

    if (passesValidation(validation)) {
      passed.push(signal);
    } else {
      const failures: string[] = [];

      if (!validation.compression_gate.passed) {
        failures.push(validation.compression_gate.reason || "Compression gate failed");
        compressionFailures++;
      }

      if (!validation.noise_gate.passed) {
        failures.push(validation.noise_gate.reason || "Noise gate failed");
        noiseFailures++;
      }

      failed.push({ signal, validation, failures });
    }
  }

  return {
    passed,
    failed,
    stats: {
      totalProcessed: signals.length,
      passRate: signals.length > 0 ? passed.length / signals.length : 0,
      compressionFailures,
      noiseFailures,
    },
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Custom Gate Builder
// ═══════════════════════════════════════════════════════════════════════════

export type CustomGateFunction = (signal: SlangSignal) => GateResult;

/**
 * Creates a custom gate with specified criteria
 */
export function createCustomGate(
  name: string,
  validateFn: (signal: SlangSignal) => { passed: boolean; reason?: string; score?: number }
): CustomGateFunction {
  return (signal: SlangSignal): GateResult => {
    const result = validateFn(signal);
    return {
      gate_name: name,
      ...result,
    };
  };
}
