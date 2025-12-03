/**
 * ABX-Core v1.3 - Semiotic Weather Engine Orchestrator
 * Combines all weather modules into comprehensive forecast
 *
 * @module abraxas/weather_engine/core/orchestrator
 * @entropy_class high
 * @deterministic true
 * @capabilities { read: ["all_modules"], write: ["weather_forecast"], network: false }
 * @version 4.2.0
 */

import type {
  WeatherEngineInput,
  WeatherEngineOutput,
  MacroPressureSystems,
  MesoCognitiveWeather,
  MicroLocalField,
  SlangFrontEntry,
  MemeFrontTemplate,
  ShortTermForecast,
  WeatherMetadata,
  WeatherProvenance,
  PressureSystem,
  CognitivePattern,
  LocalEffect,
  Prediction,
} from "./types";
import type { SymbolicVector } from "../../core/kernel";

// Import all weather modules
import { detectEventMicrobursts } from "../modules/event-microbursts";
import { detectGeometricDrift } from "../modules/geometric-drift";
import { scanBodyTemperature } from "../modules/body-temperature";
import { detectForecastInversion } from "../modules/forecast-inversion";
import { detectBifurcation } from "../modules/bifurcation";
import { detectSymbolicChimera } from "../modules/symbolic-chimera";
import { computeTemporalDecay } from "../modules/temporal-decay";
import { detectShadowPressure } from "../modules/shadow-predictive";
import { forecastSlangMutation } from "../modules/slang-mutation";
import { computeMemeBarometer } from "../modules/meme-barometric";
import { computeMythicGateIndex } from "../modules/mythic-gate";
import { calculateSymbolicJetStream } from "../modules/symbolic-jetstream";
import { detectArchetypalCrosswinds } from "../modules/archetypal-crosswinds";
import { computeVeilbreakerGravity } from "../modules/veilbreaker-gravity";
import { trackIdentityPhase } from "../modules/identity-phase";

/**
 * Main Weather Engine - Orchestrates all modules
 */
export async function generateSemioticWeather(
  input: WeatherEngineInput
): Promise<WeatherEngineOutput> {
  const startTime = Date.now();

  // Create symbolic vector from input
  const vector: SymbolicVector = {
    features: extractFeatures(input),
    timestamp: input.timestamp,
    seed: input.context.seed,
  };

  // Execute all weather modules
  const microEvents = detectEventMicrobursts(vector, input.context);
  const geometricShapes = detectGeometricDrift(vector, input.context);
  const bodyTemp = scanBodyTemperature(vector, input.context);
  const negativeSpace = detectForecastInversion(vector, input.context);
  const bifurcation = detectBifurcation(vector, input.context);
  const chimera = detectSymbolicChimera(vector, input.context);
  const decay = computeTemporalDecay(vector, input.context);
  const shadowField = detectShadowPressure(vector, input.context);
  const slangMutation = forecastSlangMutation(vector, input.context);
  const memeBarometer = computeMemeBarometer(vector, input.context);
  const mythicGates = computeMythicGateIndex(vector, input.context);
  const jetStream = calculateSymbolicJetStream(vector, input.context);
  const crosswinds = detectArchetypalCrosswinds(vector, input.context);
  const veilbreakerGravity = computeVeilbreakerGravity(vector, input.context);
  const identityPhase = trackIdentityPhase(vector, input.context);

  // Aggregate into macro pressure systems
  const macro_pressure_systems = aggregateMacroPressure({
    microEvents,
    bodyTemp,
    memeBarometer,
    shadowField,
    bifurcation,
  });

  // Aggregate into meso cognitive weather
  const meso_cognitive_weather = aggregateMesoCognitive({
    geometricShapes,
    mythicGates,
    chimera,
    crosswinds,
  });

  // Aggregate into micro local field
  const micro_local_field = aggregateMicroLocal({
    veilbreakerGravity,
    identityPhase,
    jetStream,
  });

  // Generate slang front entries
  const slang_front_entries = generateSlangFronts(slangMutation);

  // Generate meme front templates
  const meme_front_templates = generateMemeFronts(memeBarometer);

  // Generate short-term forecast
  const short_term_symbolic_forecast = generateShortTermForecast({
    microEvents,
    bifurcation,
    decay,
    shadowField,
    identityPhase,
  });

  // Calculate metadata
  const processingTime = Date.now() - startTime;
  const qualityScore = input.symbolicMetrics
    ? (input.symbolicMetrics.MSI + input.symbolicMetrics.ITC) / 2
    : 0.5;

  const metadata: WeatherMetadata = {
    generatedAt: Date.now(),
    processingTime,
    qualityScore,
    entropyClass: "high",
  };

  const provenance: WeatherProvenance = {
    seed: input.context.seed,
    runes: input.context.runes || [],
    timestamp: Date.now(),
    version: "4.2.0",
  };

  return {
    macro_pressure_systems,
    meso_cognitive_weather,
    micro_local_field,
    slang_front_entries,
    meme_front_templates,
    short_term_symbolic_forecast,
    metadata,
    provenance,
  };
}

/**
 * Extract features from input for vector creation
 */
function extractFeatures(input: WeatherEngineInput): Record<string, number> {
  const features: Record<string, number> = {
    timestamp: input.timestamp,
  };

  // Include symbolic metrics as features
  if (input.symbolicMetrics) {
    features.SDR = input.symbolicMetrics.SDR;
    features.MSI = input.symbolicMetrics.MSI;
    features.ARF = input.symbolicMetrics.ARF;
    features.NMC = input.symbolicMetrics.NMC;
    features.RFR = input.symbolicMetrics.RFR;
    features.Hσ = input.symbolicMetrics.Hσ;
    features.λN = input.symbolicMetrics.λN;
    features.ITC = input.symbolicMetrics.ITC;
  }

  return features;
}

/**
 * Aggregate macro pressure systems
 */
function aggregateMacroPressure(modules: any): MacroPressureSystems {
  const systems: PressureSystem[] = [
    {
      name: "Memetic Pressure",
      strength: modules.memeBarometer.overallPressure,
      coverage: 0.8,
      trend: modules.memeBarometer.stability === "stable"
        ? "stable"
        : modules.memeBarometer.stability === "volatile"
        ? "strengthening"
        : "weakening",
    },
    {
      name: "Affective Temperature",
      strength: modules.bodyTemp.temperature,
      coverage: 0.7,
      trend: modules.bodyTemp.volatility > 0.5 ? "strengthening" : "stable",
    },
    {
      name: "Shadow Pressure",
      strength: modules.shadowField.pressureIndex,
      coverage: 0.6,
      trend: modules.shadowField.emergenceRisk > 0.5 ? "strengthening" : "stable",
    },
  ];

  const sortedSystems = [...systems].sort((a, b) => b.strength - a.strength);
  const dominant = sortedSystems[0].name;
  const pressure = sortedSystems[0].strength;

  return { dominant, pressure, systems };
}

/**
 * Aggregate meso cognitive weather
 */
function aggregateMesoCognitive(modules: any): MesoCognitiveWeather {
  const patterns: CognitivePattern[] = [
    {
      name: "Geometric Complexity",
      intensity: modules.geometricShapes.complexity,
      spread: 0.7,
      duration: 14,
    },
    {
      name: "Mythic Resonance",
      intensity: modules.mythicGates.gateStrength,
      spread: 0.6,
      duration: 21,
    },
    {
      name: "Chimeric Mutation",
      intensity: modules.chimera.mutationRate,
      spread: 0.5,
      duration: 7,
    },
  ];

  const coherence = 1 - modules.crosswinds.misalignmentIndex;
  const volatility = modules.crosswinds.turbulence;

  return { patterns, coherence, volatility };
}

/**
 * Aggregate micro local field
 */
function aggregateMicroLocal(modules: any): MicroLocalField {
  const localEffects: LocalEffect[] = [
    {
      effect: "Synchronicity Clustering",
      strength: modules.veilbreakerGravity.gravityStrength,
      proximity: modules.veilbreakerGravity.fieldRadius,
      timeframe: "1-7 days",
    },
    {
      effect: "Identity Phase Transition",
      strength: modules.identityPhase.progress,
      proximity: 1.0,
      timeframe: `${Math.round(modules.identityPhase.duration)} days`,
    },
    {
      effect: "Symbolic Jet Stream",
      strength: modules.jetStream.velocity,
      proximity: 0.8,
      timeframe: "immediate",
    },
  ];

  const personalResonance =
    modules.identityPhase.progress * modules.veilbreakerGravity.gravityStrength;
  const veilbreakerInfluence = modules.veilbreakerGravity.gravityStrength;

  return { localEffects, personalResonance, veilbreakerInfluence };
}

/**
 * Generate slang front entries
 */
function generateSlangFronts(slangMutation: any): SlangFrontEntry[] {
  return slangMutation.terms
    .slice(0, 5) // Top 5 terms
    .map((term: any) => {
      let front: "advancing" | "stable" | "retreating";
      if (term.viralStability > 0.6) front = "advancing";
      else if (term.viralStability > 0.3) front = "stable";
      else front = "retreating";

      return {
        term: term.term,
        front,
        velocity: term.driftMobility,
        impact: term.mutationProbability,
      };
    });
}

/**
 * Generate meme front templates
 */
function generateMemeFronts(memeBarometer: any): MemeFrontTemplate[] {
  return memeBarometer.memes
    .filter((m: any) => m.pressure > 0.4) // Only significant memes
    .slice(0, 5)
    .map((meme: any) => ({
      meme: meme.meme,
      template: `[${meme.meme}]`,
      propagation: meme.pressure,
      stability: meme.likelihood === "stable" ? 0.8 : 0.3,
    }));
}

/**
 * Generate short-term forecast
 */
function generateShortTermForecast(modules: any): ShortTermForecast {
  const predictions: Prediction[] = [];

  // Event microburst prediction
  if (modules.microEvents.burstIntensity > 0.5) {
    predictions.push({
      type: "micro_event",
      description: `High ${modules.microEvents.dominantCategory} activity expected`,
      probability: modules.microEvents.burstIntensity,
      timeframe: "24-48 hours",
      impact: modules.microEvents.volatility,
    });
  }

  // Bifurcation prediction
  if (modules.bifurcation.stability > 0.5) {
    predictions.push({
      type: "narrative_split",
      description: `Bifurcation along ${modules.bifurcation.pathA.direction} vs ${modules.bifurcation.pathB.direction}`,
      probability: modules.bifurcation.stability,
      timeframe: "3-7 days",
      impact: modules.bifurcation.divergenceAngle / 180,
    });
  }

  // Shadow emergence prediction
  if (modules.shadowField.emergenceRisk > 0.6) {
    predictions.push({
      type: "shadow_emergence",
      description: "Suppressed topics likely to surface",
      probability: modules.shadowField.emergenceRisk,
      timeframe: "7-14 days",
      impact: modules.shadowField.pressureIndex,
    });
  }

  // Identity phase prediction
  predictions.push({
    type: "identity_phase",
    description: `Transition from ${modules.identityPhase.currentPhase} to ${modules.identityPhase.nextPhase}`,
    probability: modules.identityPhase.progress,
    timeframe: `${Math.round(modules.identityPhase.duration * (1 - modules.identityPhase.progress))} days`,
    impact: 0.8,
  });

  const avgProbability =
    predictions.reduce((sum, p) => sum + p.probability, 0) / predictions.length;

  return {
    horizon: 14, // 14 days
    predictions,
    confidence: avgProbability,
  };
}

/**
 * Convert weather output to JSON
 */
export function weatherToJSON(weather: WeatherEngineOutput): string {
  return JSON.stringify(weather, null, 2);
}

/**
 * Convert weather output to Markdown
 */
export function weatherToMarkdown(weather: WeatherEngineOutput): string {
  let md = "# Semiotic Weather Forecast\n\n";
  md += `*Generated: ${new Date(weather.metadata.generatedAt).toISOString()}*\n`;
  md += `*Quality Score: ${(weather.metadata.qualityScore * 100).toFixed(1)}%*\n\n`;

  // Macro Pressure
  md += "## Macro Pressure Systems\n\n";
  md += `**Dominant System:** ${weather.macro_pressure_systems.dominant}\n`;
  md += `**Pressure Level:** ${(weather.macro_pressure_systems.pressure * 100).toFixed(1)}%\n\n`;
  weather.macro_pressure_systems.systems.forEach((sys) => {
    md += `- **${sys.name}**: ${(sys.strength * 100).toFixed(1)}% (${sys.trend})\n`;
  });

  // Meso Cognitive
  md += "\n## Meso Cognitive Weather\n\n";
  md += `**Coherence:** ${(weather.meso_cognitive_weather.coherence * 100).toFixed(1)}%\n`;
  md += `**Volatility:** ${(weather.meso_cognitive_weather.volatility * 100).toFixed(1)}%\n\n`;
  weather.meso_cognitive_weather.patterns.forEach((pat) => {
    md += `- **${pat.name}**: Intensity ${(pat.intensity * 100).toFixed(1)}%, Duration ~${pat.duration} days\n`;
  });

  // Micro Local Field
  md += "\n## Micro Local Field\n\n";
  md += `**Personal Resonance:** ${(weather.micro_local_field.personalResonance * 100).toFixed(1)}%\n`;
  md += `**Veilbreaker Influence:** ${(weather.micro_local_field.veilbreakerInfluence * 100).toFixed(1)}%\n\n`;
  weather.micro_local_field.localEffects.forEach((eff) => {
    md += `- **${eff.effect}**: ${(eff.strength * 100).toFixed(1)}% (${eff.timeframe})\n`;
  });

  // Slang Fronts
  md += "\n## Slang Fronts\n\n";
  weather.slang_front_entries.forEach((slang) => {
    md += `- **${slang.term}**: ${slang.front} (velocity ${(slang.velocity * 100).toFixed(0)}%)\n`;
  });

  // Meme Fronts
  md += "\n## Meme Fronts\n\n";
  weather.meme_front_templates.forEach((meme) => {
    md += `- **${meme.meme}**: ${(meme.propagation * 100).toFixed(1)}% propagation\n`;
  });

  // Short-term Forecast
  md += "\n## Short-term Forecast (14 days)\n\n";
  md += `**Overall Confidence:** ${(weather.short_term_symbolic_forecast.confidence * 100).toFixed(1)}%\n\n`;
  weather.short_term_symbolic_forecast.predictions.forEach((pred, i) => {
    md += `${i + 1}. **${pred.type}** (${(pred.probability * 100).toFixed(1)}%)\n`;
    md += `   - ${pred.description}\n`;
    md += `   - Timeframe: ${pred.timeframe}\n`;
    md += `   - Impact: ${(pred.impact * 100).toFixed(1)}%\n\n`;
  });

  md += `---\n*Abraxas Weather Engine v${weather.provenance.version}*\n`;

  return md;
}
