/**
 * ABX-Core v1.2 - Vector Type Definitions (ABX-Runes IR Compatible)
 * SEED Framework Compliant
 *
 * @module abraxas/models/vector
 * @deterministic true
 *
 * Defines input/output vectors compatible with ABX-Runes IR
 */

export interface FeatureVector {
  id: string;
  type: "equity" | "fx" | "sector" | "aggregate";
  subject: string;  // ticker, pair, or identifier
  features: Record<string, number>;
  timestamp: number;
  seed: string;
  provenance: VectorProvenance;
}

export interface VectorProvenance {
  source: string;
  module: string;
  operation: string;
  parentId?: string;
  generatedAt: number;
}

export interface AggregateVector {
  vectors: FeatureVector[];
  weights: Record<string, number>;
  context: {
    seed: string;
    date: string;
    runes: string[];
  };
}

export interface ScoredVector extends FeatureVector {
  score: number;
  confidence: number;
  riskClass?: string;
  symbolicMetrics?: {
    SDR: number;
    MSI: number;
    ARF: number;
    NMC: number;
    RFR: number;
    Hσ: number;
    λN: number;
    ITC: number;
  };
  qualityScore?: number;
}
