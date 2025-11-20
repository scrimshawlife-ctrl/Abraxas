/**
 * ABX-Core v1.2 - Symbolic Metrics Kernel
 * Abraxas Kernel v1.2 Implementation
 *
 * @module abraxas/core/kernel
 * @entropy_class low
 * @deterministic true
 * @capabilities { read: ["features", "weights", "archetypes"], write: ["metrics"], network: false }
 *
 * Implements the 8 core symbolic metrics:
 * - SDR: Symbolic Drift Ratio
 * - MSI: Memetic Saturation Index
 * - ARF: Archetype Resonance Factor
 * - NMC: Narrative Momentum Coefficient
 * - RFR: Runic Flux Ratio
 * - Hσ:  Entropy Sigma
 * - λN:  Narrative Lambda
 * - ITC: Inter-Temporal Coherence
 */

import crypto from "crypto";

// ═══════════════════════════════════════════════════════════════════════════
// Symbolic Metric Interfaces
// ═══════════════════════════════════════════════════════════════════════════

export interface SymbolicVector {
  features: Record<string, number>;
  timestamp: number;
  seed: string;
}

export interface SymbolicMetrics {
  SDR: number;  // Symbolic Drift Ratio [0, 1]
  MSI: number;  // Memetic Saturation Index [0, 1]
  ARF: number;  // Archetype Resonance Factor [-1, 1]
  NMC: number;  // Narrative Momentum Coefficient [-1, 1]
  RFR: number;  // Runic Flux Ratio [0, 1]
  Hσ: number;   // Entropy Sigma [0, ∞)
  λN: number;   // Narrative Lambda [0, 1]
  ITC: number;  // Inter-Temporal Coherence [0, 1]
}

export interface KernelContext {
  seed: string;
  date: string;
  runes?: string[];
  archetypes?: string[];
  priorVector?: SymbolicVector;
}

// ═══════════════════════════════════════════════════════════════════════════
// Hash Utilities (Deterministic)
// ═══════════════════════════════════════════════════════════════════════════

function deterministicHash(input: string): number {
  return parseInt(
    crypto.createHash("sha256").update(input).digest("hex").slice(0, 8),
    16
  );
}

function normalizedHash(input: string, min = 0, max = 1): number {
  const hash = deterministicHash(input);
  return min + ((hash % 10000) / 10000) * (max - min);
}

// ═══════════════════════════════════════════════════════════════════════════
// SDR: Symbolic Drift Ratio
// ═══════════════════════════════════════════════════════════════════════════
/**
 * Measures deviation from expected symbolic trajectory.
 * Higher values indicate greater drift from narrative coherence.
 *
 * Formula: SDR = |Σ(f_i - f̄_i)²| / n
 * Where f_i are features and f̄_i are expected values
 */
export function computeSDR(
  vector: SymbolicVector,
  context: KernelContext
): number {
  const features = Object.values(vector.features);
  if (features.length === 0) return 0;

  // Compute expected baseline from seed
  const expectedMean = normalizedHash(context.seed + "baseline", -0.5, 0.5);

  // Calculate mean squared deviation
  const deviations = features.map(f => Math.pow(f - expectedMean, 2));
  const msd = deviations.reduce((sum, d) => sum + d, 0) / features.length;

  // Normalize to [0, 1]
  return Math.min(1, Math.sqrt(msd));
}

// ═══════════════════════════════════════════════════════════════════════════
// MSI: Memetic Saturation Index
// ═══════════════════════════════════════════════════════════════════════════
/**
 * Quantifies informational density and pattern saturation.
 * Indicates how "full" the symbolic space is with meaningful patterns.
 *
 * Formula: MSI = (unique_patterns / total_capacity) * coherence_factor
 */
export function computeMSI(
  vector: SymbolicVector,
  context: KernelContext
): number {
  const features = Object.keys(vector.features);
  const uniquePatterns = new Set(
    features.map(k => deterministicHash(k + context.seed) % 100)
  ).size;

  // Maximum capacity (fixed at 100 for normalization)
  const maxCapacity = 100;

  // Coherence factor based on feature magnitudes
  const magnitudes = Object.values(vector.features);
  const coherence = magnitudes.reduce((sum, m) => sum + Math.abs(m), 0) / Math.max(1, magnitudes.length);

  // MSI = density * coherence
  const density = uniquePatterns / maxCapacity;
  return Math.min(1, density * Math.min(1, coherence));
}

// ═══════════════════════════════════════════════════════════════════════════
// ARF: Archetype Resonance Factor
// ═══════════════════════════════════════════════════════════════════════════
/**
 * Measures alignment with archetypal patterns.
 * Positive values indicate constructive resonance, negative indicate dissonance.
 *
 * Formula: ARF = Σ(cos(θ_i)) / n
 * Where θ_i is the angle between feature and archetype vectors
 */
export function computeARF(
  vector: SymbolicVector,
  context: KernelContext
): number {
  const archetypes = context.archetypes || ["warrior", "sage", "fool", "monarch"];
  const features = Object.entries(vector.features);

  if (features.length === 0) return 0;

  // Compute resonance with each archetype
  const resonances = archetypes.map(archetype => {
    // Create archetype vector from seed
    const archetypeHash = deterministicHash(archetype + context.seed);
    const archetypeAngle = (archetypeHash % 360) * (Math.PI / 180);

    // Compute dot product with feature vector
    const featureAngle = features.reduce((sum, [k, v]) => {
      const keyHash = deterministicHash(k + context.seed);
      return sum + v * Math.cos((keyHash % 360) * (Math.PI / 180));
    }, 0) / features.length;

    // Cosine similarity
    return Math.cos(archetypeAngle - featureAngle);
  });

  // Average resonance across all archetypes
  const avgResonance = resonances.reduce((sum, r) => sum + r, 0) / archetypes.length;

  // Clamp to [-1, 1]
  return Math.max(-1, Math.min(1, avgResonance));
}

// ═══════════════════════════════════════════════════════════════════════════
// NMC: Narrative Momentum Coefficient
// ═══════════════════════════════════════════════════════════════════════════
/**
 * Tracks directional flow of narrative development.
 * Positive indicates forward momentum, negative indicates regression.
 *
 * Formula: NMC = Δv / Δt * coherence
 * Where Δv is change in feature magnitude and Δt is time delta
 */
export function computeNMC(
  vector: SymbolicVector,
  context: KernelContext
): number {
  const priorVector = context.priorVector;

  if (!priorVector) {
    // No prior vector, use seed-based baseline
    return normalizedHash(context.seed + "momentum", -0.3, 0.3);
  }

  // Compute feature delta
  const currentMag = Object.values(vector.features).reduce((sum, v) => sum + Math.abs(v), 0);
  const priorMag = Object.values(priorVector.features).reduce((sum, v) => sum + Math.abs(v), 0);

  const deltaMag = currentMag - priorMag;

  // Time delta (milliseconds)
  const deltaTime = Math.max(1, vector.timestamp - priorVector.timestamp);

  // Momentum = rate of change
  const momentum = (deltaMag / Math.max(1, priorMag)) * (3600000 / deltaTime); // Normalize to per-hour

  // Clamp to [-1, 1]
  return Math.max(-1, Math.min(1, momentum));
}

// ═══════════════════════════════════════════════════════════════════════════
// RFR: Runic Flux Ratio
// ═══════════════════════════════════════════════════════════════════════════
/**
 * Quantifies volatility in runic influences.
 * Higher values indicate unstable symbolic conditions.
 *
 * Formula: RFR = σ(rune_energies) / μ(rune_energies)
 */
export function computeRFR(
  vector: SymbolicVector,
  context: KernelContext
): number {
  const runes = context.runes || [];

  if (runes.length === 0) return 0;

  // Compute runic energies from features
  const runeEnergies = runes.map(rune => {
    const runeHash = deterministicHash(rune + context.seed);
    // Correlate rune with feature magnitudes
    return Object.values(vector.features).reduce((sum, v) => {
      return sum + v * Math.sin((runeHash % 360) * (Math.PI / 180));
    }, 0) / Math.max(1, Object.keys(vector.features).length);
  });

  // Compute mean and standard deviation
  const mean = runeEnergies.reduce((sum, e) => sum + e, 0) / runeEnergies.length;
  const variance = runeEnergies.reduce((sum, e) => sum + Math.pow(e - mean, 2), 0) / runeEnergies.length;
  const stdDev = Math.sqrt(variance);

  // Coefficient of variation (normalized)
  const cv = Math.abs(mean) > 0.01 ? stdDev / Math.abs(mean) : stdDev;

  // Normalize to [0, 1]
  return Math.min(1, cv);
}

// ═══════════════════════════════════════════════════════════════════════════
// Hσ: Entropy Sigma
// ═══════════════════════════════════════════════════════════════════════════
/**
 * Measures informational entropy and unpredictability.
 * Higher values indicate greater chaos/disorder in the symbolic system.
 *
 * Formula: Hσ = -Σ(p_i * log₂(p_i))
 * Where p_i is the probability distribution of feature values
 */
export function computeHσ(
  vector: SymbolicVector,
  context: KernelContext
): number {
  const features = Object.values(vector.features);

  if (features.length === 0) return 0;

  // Normalize to probability distribution
  const total = features.reduce((sum, f) => sum + Math.abs(f), 0);

  if (total < 0.0001) return 0; // Near-zero entropy for zero vector

  const probabilities = features.map(f => Math.abs(f) / total);

  // Shannon entropy
  const entropy = probabilities.reduce((sum, p) => {
    if (p < 0.0001) return sum; // Avoid log(0)
    return sum - p * Math.log2(p);
  }, 0);

  // Normalize by max entropy (log₂(n))
  const maxEntropy = Math.log2(features.length);

  return maxEntropy > 0 ? entropy / maxEntropy : 0;
}

// ═══════════════════════════════════════════════════════════════════════════
// λN: Narrative Lambda
// ═══════════════════════════════════════════════════════════════════════════
/**
 * Decay factor for narrative relevance over time.
 * Quantifies how quickly symbolic meaning degrades.
 *
 * Formula: λN = e^(-k * Δt)
 * Where k is decay constant and Δt is time since initialization
 */
export function computeλN(
  vector: SymbolicVector,
  context: KernelContext
): number {
  // Reference timestamp from context (date)
  const referenceTime = new Date(context.date).getTime();
  const deltaTime = vector.timestamp - referenceTime;

  // Decay constant (tuned for daily cycles)
  const k = 1 / (24 * 3600000); // Decay over 24 hours

  // Exponential decay
  const lambda = Math.exp(-k * Math.abs(deltaTime));

  return lambda;
}

// ═══════════════════════════════════════════════════════════════════════════
// ITC: Inter-Temporal Coherence
// ═══════════════════════════════════════════════════════════════════════════
/**
 * Measures consistency of symbolic patterns across time.
 * Higher values indicate stable, predictable evolution.
 *
 * Formula: ITC = 1 - |Δθ| / π
 * Where Δθ is angular difference between current and prior vectors
 */
export function computeITC(
  vector: SymbolicVector,
  context: KernelContext
): number {
  const priorVector = context.priorVector;

  if (!priorVector) {
    // No prior vector, assume maximum coherence
    return 0.95;
  }

  // Compute feature vectors
  const current = Object.values(vector.features);
  const prior = Object.values(priorVector.features);

  if (current.length === 0 || prior.length === 0) return 0.5;

  // Align vector lengths (pad with zeros)
  const maxLen = Math.max(current.length, prior.length);
  const currentPadded = [...current, ...Array(maxLen - current.length).fill(0)];
  const priorPadded = [...prior, ...Array(maxLen - prior.length).fill(0)];

  // Compute cosine similarity
  const dotProduct = currentPadded.reduce((sum, c, i) => sum + c * priorPadded[i], 0);
  const magCurrent = Math.sqrt(currentPadded.reduce((sum, c) => sum + c * c, 0));
  const magPrior = Math.sqrt(priorPadded.reduce((sum, p) => sum + p * p, 0));

  if (magCurrent < 0.0001 || magPrior < 0.0001) return 0.5;

  const cosSim = dotProduct / (magCurrent * magPrior);

  // Convert to coherence [0, 1]
  // cos(0) = 1 (perfect alignment) → ITC = 1
  // cos(π) = -1 (opposite) → ITC = 0
  const coherence = (cosSim + 1) / 2;

  return coherence;
}

// ═══════════════════════════════════════════════════════════════════════════
// Unified Kernel Computation
// ═══════════════════════════════════════════════════════════════════════════

export function computeSymbolicMetrics(
  vector: SymbolicVector,
  context: KernelContext
): SymbolicMetrics {
  return {
    SDR: computeSDR(vector, context),
    MSI: computeMSI(vector, context),
    ARF: computeARF(vector, context),
    NMC: computeNMC(vector, context),
    RFR: computeRFR(vector, context),
    Hσ: computeHσ(vector, context),
    λN: computeλN(vector, context),
    ITC: computeITC(vector, context),
  };
}

/**
 * Aggregate symbolic metrics into a single quality score
 * Used for ranking and filtering oracle outputs
 */
export function aggregateQualityScore(metrics: SymbolicMetrics): number {
  // Weighted combination of metrics
  // Higher = better quality
  const score =
    0.2 * (1 - metrics.SDR) +      // Lower drift is better
    0.15 * metrics.MSI +            // Higher saturation is better
    0.15 * (metrics.ARF + 1) / 2 +  // Normalize ARF to [0,1]
    0.1 * (metrics.NMC + 1) / 2 +   // Normalize NMC to [0,1]
    0.1 * (1 - metrics.RFR) +       // Lower flux is better
    0.1 * (1 - metrics.Hσ) +        // Lower entropy is better
    0.1 * metrics.λN +              // Higher relevance is better
    0.1 * metrics.ITC;              // Higher coherence is better

  return Math.max(0, Math.min(1, score));
}

// ═══════════════════════════════════════════════════════════════════════════
// Diagnostic & Monitoring
// ═══════════════════════════════════════════════════════════════════════════

export interface KernelDiagnostics {
  vector: SymbolicVector;
  metrics: SymbolicMetrics;
  qualityScore: number;
  warnings: string[];
  timestamp: number;
}

export function diagnoseVector(
  vector: SymbolicVector,
  context: KernelContext
): KernelDiagnostics {
  const metrics = computeSymbolicMetrics(vector, context);
  const qualityScore = aggregateQualityScore(metrics);
  const warnings: string[] = [];

  // Generate warnings for anomalous conditions
  if (metrics.SDR > 0.7) warnings.push("High symbolic drift detected");
  if (metrics.MSI < 0.2) warnings.push("Low memetic saturation");
  if (metrics.ARF < -0.5) warnings.push("Strong archetype dissonance");
  if (metrics.RFR > 0.8) warnings.push("High runic flux volatility");
  if (metrics.Hσ > 0.9) warnings.push("Excessive entropy");
  if (metrics.λN < 0.3) warnings.push("Narrative relevance decay");
  if (metrics.ITC < 0.4) warnings.push("Low temporal coherence");

  return {
    vector,
    metrics,
    qualityScore,
    warnings,
    timestamp: Date.now(),
  };
}
