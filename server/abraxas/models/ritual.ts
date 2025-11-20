/**
 * ABX-Core v1.2 - Ritual Type Definitions
 * SEED Framework Compliant
 *
 * @module abraxas/models/ritual
 * @deterministic true
 */

export interface Rune {
  id: string;
  name: string;
  color: string;
  meaning: string;
}

export interface RitualInput {
  date: string;
  seed: string;
  runes: Rune[];
  deltas?: RitualDelta[];
}

export interface RitualDelta {
  feature_map: string[];
  delta: number;
}

export interface RitualContext {
  seed: string;
  date: string;
  runes: string[];
  timestamp: number;
  userId?: string;
}

export interface RitualExecution {
  id: string;
  ritual: RitualInput;
  results: any;
  sealed: RitualSeal;
  timestamp: number;
  userId?: string;
}

export interface RitualSeal {
  hash: string;
  timestamp: number;
  signature: string;
}
