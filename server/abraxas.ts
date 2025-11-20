/**
 * ABX-Core v1.2 - Abraxas Scoring Engine
 * SEED Framework Compliant
 *
 * @module abraxas
 * @entropy_class medium
 * @deterministic true
 * @capabilities { read: ["weights", "features"], write: ["scores"], network: false }
 */

import crypto from "crypto";
import { evalDynamicIndicators } from "./indicators";

// Default weights for mystical trading features
const DEFAULT_WEIGHTS = {
  nightlights_z: 0.8,
  port_dwell_delta: -0.6,
  sam_mod_scope_delta: 0.9,
  ptab_ipr_burst: -0.7,
  fr_waiver_absence: 0.4,
  jobs_clearance_burst: 0.5,
  hs_code_volume_z: 0.6,
  fx_basis_z: -0.4,
  numerology_reduced: 0.08,
  numerology_master: 0.12,
  gematria_alignment: 0.1,
  astro_rul_align: 0.1,
  astro_waxing: 0.05
};

let CURRENT_WEIGHTS: Record<string, number> = { ...DEFAULT_WEIGHTS };

export function getWeights() {
  return { ...CURRENT_WEIGHTS };
}

// Allow dynamic keys (prefix "ind:")
export function setWeights(next: Record<string, number>) {
  const w: Record<string, number> = { ...CURRENT_WEIGHTS };
  for (const k of Object.keys(next || {})) {
    const allow = (k in DEFAULT_WEIGHTS) || k.startsWith("ind:");
    const v = next[k];
    if (allow && typeof v === "number" && isFinite(v) && Math.abs(v) <= 5) {
      w[k] = +v;
    }
  }
  CURRENT_WEIGHTS = w;
  return getWeights();
}

function hseed(str: string): number {
  return parseInt(crypto.createHash("sha256").update(str).digest("hex").slice(0, 8), 16);
}

function applyTransientDelta(base: Record<string, number>, fmap: string[], delta: number): Record<string, number> {
  const w: Record<string, number> = { ...base };
  fmap.forEach(f => {
    if (w[f] !== undefined) {
      w[f] = +(w[f] + delta).toFixed(4);
    }
  });
  return w;
}

// Generate demo features for stock tickers
function demoFeaturesForTicker(ticker: string, seed: string): Record<string, number> {
  const r = (x: string) => (((hseed(ticker + x + seed) % 200) - 100) / 50);
  return {
    nightlights_z: r("nl") / 2,
    port_dwell_delta: r("pd") / 3,
    sam_mod_scope_delta: Math.max(0, r("sam")),
    ptab_ipr_burst: r("ipr") / 4,
    fr_waiver_absence: r("fr") > 0 ? 1 : 0,
    jobs_clearance_burst: r("jobs") > 0.5 ? 1 : 0,
    hs_code_volume_z: r("hs") / 2
  };
}

// Generate demo features for FX pairs
function demoFeaturesForPair(pair: string, seed: string): Record<string, number> {
  const r = (x: string) => (((hseed(pair + x + seed) % 200) - 100) / 50);
  return {
    fx_basis_z: r("basis") / 2,
    port_dwell_delta: r("port") / 3,
    hs_code_volume_z: r("hs") / 2,
    nightlights_z: r("nl") / 3
  };
}

// Esoteric features (mystical calculations)
function esotericFeatures({ name, sector, now }: { name: string; sector: string; now: Date }): Record<string, number> {
  const nameHash = hseed(name);
  const dayOfYear = Math.floor((now.getTime() - new Date(now.getFullYear(), 0, 0).getTime()) / (1000 * 60 * 60 * 24));
  
  // Numerology
  const numerology_reduced = (nameHash % 9) + 1;
  const numerology_master = [11, 22, 33].includes(numerology_reduced) ? 1 : 0;
  
  // Gematria alignment
  const gematria_alignment = Math.sin(nameHash / 100) * 0.5;
  
  // Astrological ruler alignment
  const astro_rul_align = Math.cos((dayOfYear + nameHash) / 30) * 0.3;
  
  // Waxing moon influence
  const moonPhase = (dayOfYear % 29.5) / 29.5;
  const astro_waxing = moonPhase < 0.5 ? moonPhase * 2 : (1 - moonPhase) * 2;
  
  return {
    numerology_reduced: numerology_reduced / 9,
    numerology_master,
    gematria_alignment,
    astro_rul_align,
    astro_waxing
  };
}

// Score an entity based on features and weights
function scoreEntity(feats: Record<string, number>, w: Record<string, number>): number {
  let s = 0;
  for (const k in feats) {
    s += (w[k] || 0) * (feats[k] ?? 0);
  }
  return s;
}

// Guess sector based on ticker
function sectorGuess(t: string): string {
  if (/(LMT|NOC|RTX|GD|BA)/.test(t)) return "Aerospace & Defense";
  if (/(CVX|XOM|VLO|MPC)/.test(t)) return "Energy";
  if (/(JPM|GS|MS|BAC)/.test(t)) return "Financials";
  if (/(AMGN|PFE|UNH)/.test(t)) return "Healthcare";
  return "Tech";
}

export interface Ritual {
  seed: string;
  date: string;
  deltas: Array<{ feature_map: string[]; delta: number }>;
}

export interface WatchlistResult {
  ticker?: string;
  pair?: string;
  sector?: string;
  edge: number;
  confidence: number;
  riskClass?: string;
  features: Record<string, number>;
}

export interface ScoredWatchlists {
  equities: {
    conservative: WatchlistResult[];
    risky: WatchlistResult[];
  };
  fx: {
    conservative: WatchlistResult[];
    risky: WatchlistResult[];
  };
}

export async function scoreWatchlists(
  { equities = [], fx = [] }: { equities?: string[]; fx?: string[] },
  ritual: Ritual
): Promise<ScoredWatchlists> {
  const seed = ritual.seed.toString();
  let weights: Record<string, number> = { ...CURRENT_WEIGHTS };
  
  // Apply transient deltas from ritual
  ritual.deltas.forEach(({ feature_map, delta }) => {
    weights = applyTransientDelta(weights, feature_map, delta);
  });

  // Score equities
  const eq = await Promise.all(
    equities.map(async (ticker) => {
      const feats = demoFeaturesForTicker(ticker, seed);
      const sector = sectorGuess(ticker);
      const esoteric = esotericFeatures({ name: ticker, sector, now: new Date() });
      
      // Get dynamic indicator values
      const dyn = await evalDynamicIndicators(ticker, { date: ritual.date, seed });
      
      const merged = { ...feats, ...esoteric, ...dyn };
      const edge = +scoreEntity(merged, weights).toFixed(3);
      const conf = Math.max(
        0.1,
        Math.min(0.95, Math.abs(edge) / 3 + 0.05 * esoteric.numerology_master + 0.05 * esoteric.gematria_alignment)
      );
      const risk = edge > 0 ? 1 / (1 + feats.ptab_ipr_burst ** 2) : 1.15 + Math.max(0, feats.ptab_ipr_burst);
      
      return {
        ticker,
        sector,
        edge,
        confidence: +conf.toFixed(2),
        riskClass: risk < 1 ? "low" : "high",
        features: merged
      };
    })
  );

  const sortedEq = [...eq].sort((a, b) => b.edge - a.edge);
  const conservative = sortedEq.filter(x => x.confidence >= 0.6).slice(0, 6);
  const risky = sortedEq.filter(x => !conservative.includes(x)).slice(0, 6);

  // Score FX pairs
  const fxList = await Promise.all(
    fx.map(async (pair) => {
      const feats = demoFeaturesForPair(pair, seed);
      const base = pair.slice(0, 3);
      const quote = pair.slice(3);
      const eBase = esotericFeatures({ name: base, sector: "Financials", now: new Date() });
      const eQuote = esotericFeatures({ name: quote, sector: "Financials", now: new Date() });
      const eTilt = 
        eBase.astro_rul_align - eQuote.astro_rul_align + 
        0.05 * (eBase.numerology_master - eQuote.numerology_master);
      
      // Get dynamic indicator values
      const dyn = await evalDynamicIndicators(pair, { date: ritual.date, seed });
      
      const merged = { ...feats, astro_rul_align: eTilt, gematria_alignment: 0, ...dyn };
      const edge = +scoreEntity(merged, weights).toFixed(3);
      const conf = Math.max(0.1, Math.min(0.95, Math.abs(edge) / 3 + Math.max(0, eTilt) / 3));
      
      return {
        pair,
        edge,
        confidence: +conf.toFixed(2),
        features: merged
      };
    })
  );

  const sortedFx = [...fxList].sort((a, b) => b.edge - a.edge);
  const conservativeFx = sortedFx.filter(x => x.confidence >= 0.65).slice(0, 4);
  const riskyFx = sortedFx.filter(x => !conservativeFx.includes(x)).slice(0, 4);

  return {
    equities: { conservative, risky },
    fx: { conservative: conservativeFx, risky: riskyFx }
  };
}