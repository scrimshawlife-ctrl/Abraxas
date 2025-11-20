/**
 * ABX-Core v1.2 - Oracle Type Definitions
 * SEED Framework Compliant
 *
 * @module abraxas/models/oracle
 * @deterministic true
 */

import type { SymbolicMetrics } from "../core/kernel";

export interface OracleResult {
  ticker?: string;
  pair?: string;
  sector?: string;
  edge: number;
  confidence: number;
  riskClass?: string;
  features: Record<string, number>;
  symbolicMetrics?: SymbolicMetrics;
  qualityScore?: number;
  rationale?: string[];
}

export interface WatchlistOracleOutput {
  equities: {
    conservative: OracleResult[];
    risky: OracleResult[];
  };
  fx: {
    conservative: OracleResult[];
    risky: OracleResult[];
  };
  metadata: {
    totalProcessed: number;
    avgQualityScore: number;
    timestamp: number;
  };
}

export interface DailyOracleOutput {
  ciphergram: string;
  note: string;
  tone: string;
  confidence: number;
  symbolicMetrics: SymbolicMetrics;
  timestamp: number;
}

export interface VCOracleOutput {
  industry: string;
  region: string;
  horizon: number;
  forecast: {
    dealVolume: {
      prediction: number;
      confidence: number;
      factors: string[];
    };
    hotSectors: Array<{
      name: string;
      score: number;
      reasoning: string;
    }>;
    riskFactors: string[];
    opportunities: string[];
  };
  symbolicMetrics?: SymbolicMetrics;
  timestamp: number;
}
