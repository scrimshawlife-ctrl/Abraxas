/**
 * ABX-Core v1.3 - Semiotic Weather Engine Type Definitions
 * SEED Framework Compliant
 *
 * @module abraxas/weather_engine/core/types
 * @deterministic true
 * @version 4.2.0
 */

import type { SymbolicMetrics, SymbolicVector, KernelContext } from "../../core/kernel";

// ═══════════════════════════════════════════════════════════════════════════
// Core Weather Types
// ═══════════════════════════════════════════════════════════════════════════

export interface WeatherEngineInput {
  oracleOutput: any; // Output from daily oracle or other pipeline
  symbolicMetrics: SymbolicMetrics;
  context: KernelContext;
  timestamp: number;
}

export interface WeatherEngineOutput {
  macro_pressure_systems: MacroPressureSystems;
  meso_cognitive_weather: MesoCognitiveWeather;
  micro_local_field: MicroLocalField;
  slang_front_entries: SlangFrontEntry[];
  meme_front_templates: MemeFrontTemplate[];
  short_term_symbolic_forecast: ShortTermForecast;
  metadata: WeatherMetadata;
  provenance: WeatherProvenance;
}

export interface WeatherMetadata {
  generatedAt: number;
  processingTime: number;
  qualityScore: number;
  entropyClass: string;
}

export interface WeatherProvenance {
  seed: string;
  runes: string[];
  oracleId?: string;
  timestamp: number;
  version: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Module Output Types
// ═══════════════════════════════════════════════════════════════════════════

// 1. Event Microbursts
export interface MicroEventVector {
  events: MicroEvent[];
  burstIntensity: number;
  volatility: number;
  dominantCategory: string;
}

export interface MicroEvent {
  type: "meme_spike" | "scandal_burst" | "niche_news" | "creator_lore" | "symbolic_flashpoint";
  intensity: number;
  velocity: number;
  description: string;
  timestamp: number;
}

// 2. Geometric Drift
export interface GeometricShapeIndex {
  shapes: DetectedShape[];
  dominantShape: string;
  complexity: number;
  stability: number;
}

export interface DetectedShape {
  type: "circle" | "triangle" | "spiral" | "grid" | "fractal";
  strength: number;
  resonance: number;
  interpretation: string;
}

// 3. Digital Body Temperature
export interface CollectiveAffectProfile {
  emotions: EmotionalState[];
  dominantAffect: string;
  volatility: number;
  temperature: number; // Normalized 0-1
}

export interface EmotionalState {
  type: "anxiety" | "irony" | "sincerity" | "nostalgia" | "villain_arc" | "attention_volatility";
  intensity: number;
  trend: "rising" | "stable" | "falling";
}

// 4. Forecast Inversion
export interface NegativeSpaceReading {
  absences: AbsenceSignal[];
  suppressionIndex: number;
  shadowStrength: number;
}

export interface AbsenceSignal {
  missing: string;
  expectedPresence: number;
  significance: number;
  interpretation: string;
}

// 5. Bifurcation
export interface DualVectorMap {
  pathA: NarrativePath;
  pathB: NarrativePath;
  divergenceAngle: number;
  stability: number;
}

export interface NarrativePath {
  direction: string;
  momentum: number;
  attractorStrength: number;
  keySymbols: string[];
}

// 6. Symbolic Chimera
export interface ChimeraSignal {
  hybrids: ChimeraEntity[];
  mutationRate: number;
  stability: number;
}

export interface ChimeraEntity {
  components: string[];
  strength: number;
  coherence: number;
  interpretation: string;
}

// 7. Temporal Decay
export interface SymbolicDecayModel {
  symbols: DecayingSymbol[];
  averageHalfLife: number;
  decayRate: number;
}

export interface DecayingSymbol {
  symbol: string;
  currentStrength: number;
  halfLife: number; // in days
  timeRemaining: number;
}

// 8. Shadow Predictive Field
export interface ShadowPressureField {
  shadowTopics: ShadowTopic[];
  pressureIndex: number;
  emergenceRisk: number;
}

export interface ShadowTopic {
  topic: string;
  suppressionStrength: number;
  emergenceProbability: number;
  timeToSurface: number; // in days
}

// 9. Slang Mutation
export interface SlangMutationForecast {
  terms: SlangTerm[];
  averageMutationRate: number;
  volatility: number;
}

export interface SlangTerm {
  term: string;
  mutationProbability: number;
  driftMobility: number;
  viralStability: number;
  semanticHalfLife: number; // in days
}

// 10. Meme Barometric Pressure
export interface MemeBarometricPressure {
  memes: MemeReading[];
  overallPressure: number;
  stability: "stable" | "volatile" | "collapsing";
}

export interface MemeReading {
  meme: string;
  pressure: number;
  likelihood: "stable" | "mutating" | "collapsing";
  confidence: number;
}

// 11. Mythic Gate Index
export interface ArchetypeGateIndex {
  archetypes: ArchetypeGate[];
  dominantArchetype: string;
  gateStrength: number;
}

export interface ArchetypeGate {
  type: "trickster" | "hero" | "witness" | "scapegoat" | "oracle" | "sovereign";
  strength: number;
  openness: number;
  resonance: number;
}

// 12. Symbolic Jet Stream
export interface SymbolicJetStreamValue {
  velocity: number;
  direction: number; // degrees
  turbulence: number;
  carriers: string[]; // Top symbols riding the stream
}

// 13. Archetypal Crosswinds
export interface CrosswindVector {
  crosswinds: Crosswind[];
  misalignmentIndex: number;
  turbulence: number;
}

export interface Crosswind {
  archetype: string;
  event: string;
  misalignment: number;
  friction: number;
}

// 14. Veilbreaker Gravity Well
export interface LocalSynchronicityField {
  synchronicities: SynchronicityCluster[];
  gravityStrength: number;
  fieldRadius: number;
  centeredOn: string; // "Daniel" or subject
}

export interface SynchronicityCluster {
  events: string[];
  clusterStrength: number;
  proximity: number; // to Daniel
  significance: number;
}

// 15. Identity Phase
export interface IdentityPhaseState {
  currentPhase: "gate" | "threshold" | "trial" | "expansion" | "integration" | "renewal";
  progress: number; // 0-1 within phase
  nextPhase: string;
  duration: number; // days in current phase
  influences: string[];
}

// ═══════════════════════════════════════════════════════════════════════════
// Aggregate Weather Outputs
// ═══════════════════════════════════════════════════════════════════════════

export interface MacroPressureSystems {
  dominant: string;
  pressure: number;
  systems: PressureSystem[];
}

export interface PressureSystem {
  name: string;
  strength: number;
  coverage: number;
  trend: "strengthening" | "stable" | "weakening";
}

export interface MesoCognitiveWeather {
  patterns: CognitivePattern[];
  coherence: number;
  volatility: number;
}

export interface CognitivePattern {
  name: string;
  intensity: number;
  spread: number;
  duration: number;
}

export interface MicroLocalField {
  localEffects: LocalEffect[];
  personalResonance: number;
  veilbreakerInfluence: number;
}

export interface LocalEffect {
  effect: string;
  strength: number;
  proximity: number;
  timeframe: string;
}

export interface SlangFrontEntry {
  term: string;
  front: "advancing" | "stable" | "retreating";
  velocity: number;
  impact: number;
}

export interface MemeFrontTemplate {
  meme: string;
  template: string;
  propagation: number;
  stability: number;
}

export interface ShortTermForecast {
  horizon: number; // days
  predictions: Prediction[];
  confidence: number;
}

export interface Prediction {
  type: string;
  description: string;
  probability: number;
  timeframe: string;
  impact: number;
}
