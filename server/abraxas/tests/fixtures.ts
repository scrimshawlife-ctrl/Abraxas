/**
 * ABX-Core v1.2 - Test Fixtures
 * SEED Framework Compliant
 *
 * @module abraxas/tests/fixtures
 * @entropy_class low
 * @deterministic true
 *
 * Deterministic test fixtures for golden tests
 */

import type { RitualInput, Rune } from "../models/ritual";
import type { OracleSnapshot } from "../pipelines/daily-oracle";
import type { VCAnalysisInput } from "../pipelines/vc-analyzer";

/**
 * Fixed ritual for deterministic testing
 */
export const FIXED_RITUAL: RitualInput = {
  date: "2025-01-15",
  seed: "test-seed-12345",
  runes: [
    { id: "aether", name: "Aether" },
    { id: "flux", name: "Flux" },
    { id: "nexus", name: "Nexus" },
  ] as Rune[],
};

/**
 * Alternative ritual for variation testing
 */
export const ALT_RITUAL: RitualInput = {
  date: "2025-02-20",
  seed: "alt-seed-67890",
  runes: [
    { id: "ward", name: "Ward" },
    { id: "whisper", name: "Whisper" },
    { id: "void", name: "Void" },
  ] as Rune[],
};

/**
 * Fixed metrics snapshot for oracle testing
 */
export const FIXED_METRICS_SNAPSHOT: OracleSnapshot = {
  sources: 50,
  signals: 25,
  predictions: 10,
  accuracy: 0.75,
};

/**
 * Low confidence metrics snapshot
 */
export const LOW_CONFIDENCE_METRICS: OracleSnapshot = {
  sources: 10,
  signals: 5,
  predictions: 2,
  accuracy: 0.42,
};

/**
 * High confidence metrics snapshot
 */
export const HIGH_CONFIDENCE_METRICS: OracleSnapshot = {
  sources: 150,
  signals: 80,
  predictions: 50,
  accuracy: 0.88,
};

/**
 * Fixed VC analysis input
 */
export const FIXED_VC_INPUT: VCAnalysisInput = {
  industry: "Technology",
  region: "US",
  horizonDays: 90,
};

/**
 * Alternative VC analysis input
 */
export const ALT_VC_INPUT: VCAnalysisInput = {
  industry: "Healthcare",
  region: "EU",
  horizonDays: 180,
};

/**
 * Fixed watchlists for scoring tests
 */
export const FIXED_WATCHLISTS = {
  equities: ["AAPL", "MSFT", "GOOGL"],
  fx: ["USD/JPY", "EUR/USD"],
};

/**
 * Large watchlists for performance tests
 */
export const LARGE_WATCHLISTS = {
  equities: [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "NVDA",
    "META",
    "TSLA",
    "BRK.B",
    "V",
    "JPM",
  ],
  fx: ["USD/JPY", "EUR/USD", "GBP/USD", "AUD/USD", "USD/CAD"],
};

/**
 * Fixed feature vector for kernel tests
 */
export const FIXED_FEATURE_VECTOR = {
  price_momentum: 0.65,
  volume_trend: 0.72,
  volatility: 0.38,
  sentiment: 0.55,
  technical_strength: 0.68,
};

/**
 * Edge case: All zeros
 */
export const ZERO_FEATURE_VECTOR = {
  feature_a: 0,
  feature_b: 0,
  feature_c: 0,
  feature_d: 0,
};

/**
 * Edge case: All ones
 */
export const MAX_FEATURE_VECTOR = {
  feature_a: 1,
  feature_b: 1,
  feature_c: 1,
  feature_d: 1,
};

/**
 * Negative features (testing ARF with negative polarities)
 */
export const NEGATIVE_FEATURE_VECTOR = {
  decline: -0.5,
  risk: -0.3,
  uncertainty: -0.7,
};
