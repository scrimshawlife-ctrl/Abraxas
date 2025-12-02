/**
 * ABX-Core v1.3 - Weather Engine Tests
 * SEED Framework Compliant
 *
 * @module abraxas/tests/weather-engine
 * @deterministic true
 */

import { describe, it, expect } from "vitest";
import { FIXED_RITUAL, ALT_RITUAL } from "./fixtures";
import { ritualToContext } from "../integrations/runes-adapter";

// Import all weather modules
import { detectEventMicrobursts } from "../weather_engine/modules/event-microbursts";
import { detectGeometricDrift } from "../weather_engine/modules/geometric-drift";
import { scanBodyTemperature } from "../weather_engine/modules/body-temperature";
import { detectForecastInversion } from "../weather_engine/modules/forecast-inversion";
import { detectBifurcation } from "../weather_engine/modules/bifurcation";
import { detectSymbolicChimera } from "../weather_engine/modules/symbolic-chimera";
import { computeTemporalDecay } from "../weather_engine/modules/temporal-decay";
import { detectShadowPressure } from "../weather_engine/modules/shadow-predictive";
import { forecastSlangMutation } from "../weather_engine/modules/slang-mutation";
import { computeMemeBarometer } from "../weather_engine/modules/meme-barometric";
import { computeMythicGateIndex } from "../weather_engine/modules/mythic-gate";
import { calculateSymbolicJetStream } from "../weather_engine/modules/symbolic-jetstream";
import { detectArchetypalCrosswinds } from "../weather_engine/modules/archetypal-crosswinds";
import { computeVeilbreakerGravity } from "../weather_engine/modules/veilbreaker-gravity";
import { trackIdentityPhase } from "../weather_engine/modules/identity-phase";

// Import orchestrator
import { generateSemioticWeather, weatherToJSON, weatherToMarkdown } from "../weather_engine/core/orchestrator";
import type { WeatherEngineInput } from "../weather_engine/core/types";
import type { SymbolicVector } from "../core/kernel";

// ═══════════════════════════════════════════════════════════════════════════
// Test Helpers
// ═══════════════════════════════════════════════════════════════════════════

function createTestVector(): SymbolicVector {
  return {
    features: {
      price_momentum: 0.65,
      volume_trend: 0.72,
      volatility: 0.38,
    },
    timestamp: Date.now(),
    seed: FIXED_RITUAL.seed,
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Module Tests
// ═══════════════════════════════════════════════════════════════════════════

describe("Weather Engine Modules", () => {
  const vector = createTestVector();
  const context = ritualToContext(FIXED_RITUAL);

  describe("Event Microbursts", () => {
    it("detects micro events deterministically", () => {
      const result = detectEventMicrobursts(vector, context);

      expect(result.events).toBeDefined();
      expect(Array.isArray(result.events)).toBe(true);
      expect(result.burstIntensity).toBeGreaterThanOrEqual(0);
      expect(result.burstIntensity).toBeLessThanOrEqual(1);
      expect(result.dominantCategory).toBeDefined();
    });

    it("produces same output for same input", () => {
      const result1 = detectEventMicrobursts(vector, context);
      const result2 = detectEventMicrobursts(vector, context);

      expect(result1.burstIntensity).toBe(result2.burstIntensity);
      expect(result1.dominantCategory).toBe(result2.dominantCategory);
      expect(result1.events.length).toBe(result2.events.length);
    });
  });

  describe("Geometric Drift", () => {
    it("detects geometric shapes", () => {
      const result = detectGeometricDrift(vector, context);

      expect(result.shapes).toHaveLength(5);
      expect(result.dominantShape).toBeDefined();
      expect(result.complexity).toBeGreaterThanOrEqual(0);
      expect(result.stability).toBeGreaterThanOrEqual(0);
    });

    it("is deterministic", () => {
      const result1 = detectGeometricDrift(vector, context);
      const result2 = detectGeometricDrift(vector, context);

      expect(result1.dominantShape).toBe(result2.dominantShape);
      expect(result1.complexity).toBe(result2.complexity);
    });
  });

  describe("Body Temperature Scanner", () => {
    it("measures collective affect", () => {
      const result = scanBodyTemperature(vector, context);

      expect(result.emotions).toHaveLength(6);
      expect(result.dominantAffect).toBeDefined();
      expect(result.temperature).toBeGreaterThanOrEqual(0);
      expect(result.temperature).toBeLessThanOrEqual(1);
    });
  });

  describe("Forecast Inversion", () => {
    it("detects negative space", () => {
      const result = detectForecastInversion(vector, context);

      expect(result.absences).toBeDefined();
      expect(result.suppressionIndex).toBeGreaterThanOrEqual(0);
      expect(result.shadowStrength).toBeGreaterThanOrEqual(0);
    });
  });

  describe("Bifurcation Engine", () => {
    it("detects narrative splits", () => {
      const result = detectBifurcation(vector, context);

      expect(result.pathA).toBeDefined();
      expect(result.pathB).toBeDefined();
      expect(result.divergenceAngle).toBeGreaterThanOrEqual(0);
      expect(result.divergenceAngle).toBeLessThanOrEqual(180);
    });
  });

  describe("Symbolic Chimera Detector", () => {
    it("detects hybrid symbols", () => {
      const result = detectSymbolicChimera(vector, context);

      expect(result.hybrids).toBeDefined();
      expect(result.mutationRate).toBeGreaterThanOrEqual(0);
      expect(result.stability).toBeGreaterThanOrEqual(0);
    });
  });

  describe("Temporal Decay", () => {
    it("computes symbolic decay", () => {
      const result = computeTemporalDecay(vector, context);

      expect(result.symbols).toBeDefined();
      expect(result.averageHalfLife).toBeGreaterThan(0);
      expect(result.decayRate).toBeGreaterThan(0);
    });
  });

  describe("Shadow Predictive Field", () => {
    it("detects shadow topics", () => {
      const result = detectShadowPressure(vector, context);

      expect(result.shadowTopics).toBeDefined();
      expect(result.pressureIndex).toBeGreaterThanOrEqual(0);
      expect(result.emergenceRisk).toBeGreaterThanOrEqual(0);
    });
  });

  describe("Slang Mutation", () => {
    it("forecasts slang evolution", () => {
      const result = forecastSlangMutation(vector, context);

      expect(result.terms).toBeDefined();
      expect(result.terms.length).toBeGreaterThan(0);
      expect(result.averageMutationRate).toBeGreaterThanOrEqual(0);
    });
  });

  describe("Meme Barometric Pressure", () => {
    it("computes meme pressure", () => {
      const result = computeMemeBarometer(vector, context);

      expect(result.memes).toBeDefined();
      expect(result.overallPressure).toBeGreaterThanOrEqual(0);
      expect(["stable", "volatile", "collapsing"]).toContain(result.stability);
    });
  });

  describe("Mythic Gate Index", () => {
    it("rates archetype strength", () => {
      const result = computeMythicGateIndex(vector, context);

      expect(result.archetypes).toHaveLength(6);
      expect(result.dominantArchetype).toBeDefined();
      expect(result.gateStrength).toBeGreaterThanOrEqual(0);
    });
  });

  describe("Symbolic Jet Stream", () => {
    it("calculates symbolic velocity", () => {
      const result = calculateSymbolicJetStream(vector, context);

      expect(result.velocity).toBeGreaterThanOrEqual(0);
      expect(result.direction).toBeGreaterThanOrEqual(0);
      expect(result.direction).toBeLessThanOrEqual(360);
      expect(result.carriers).toBeDefined();
    });
  });

  describe("Archetypal Crosswinds", () => {
    it("detects misalignment", () => {
      const result = detectArchetypalCrosswinds(vector, context);

      expect(result.crosswinds).toBeDefined();
      expect(result.misalignmentIndex).toBeGreaterThanOrEqual(0);
      expect(result.turbulence).toBeGreaterThanOrEqual(0);
    });
  });

  describe("Veilbreaker Gravity Well", () => {
    it("models synchronicity clustering", () => {
      const result = computeVeilbreakerGravity(vector, context);

      expect(result.synchronicities).toBeDefined();
      expect(result.gravityStrength).toBeGreaterThanOrEqual(0);
      expect(result.centeredOn).toBe("Daniel");
    });
  });

  describe("Identity Phase Tracker", () => {
    it("tracks identity phase", () => {
      const result = trackIdentityPhase(vector, context);

      expect(["gate", "threshold", "trial", "expansion", "integration", "renewal"]).toContain(
        result.currentPhase
      );
      expect(result.progress).toBeGreaterThanOrEqual(0);
      expect(result.progress).toBeLessThanOrEqual(1);
      expect(result.nextPhase).toBeDefined();
    });
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// Orchestrator Tests
// ═══════════════════════════════════════════════════════════════════════════

describe("Weather Engine Orchestrator", () => {
  it("generates complete weather forecast", async () => {
    const context = ritualToContext(FIXED_RITUAL);
    const input: WeatherEngineInput = {
      oracleOutput: null,
      symbolicMetrics: {
        SDR: 0.5,
        MSI: 0.6,
        ARF: 0.3,
        NMC: 0.4,
        RFR: 0.5,
        Hσ: 0.7,
        λN: 0.8,
        ITC: 0.6,
      },
      context,
      timestamp: Date.now(),
    };

    const weather = await generateSemioticWeather(input);

    expect(weather.macro_pressure_systems).toBeDefined();
    expect(weather.meso_cognitive_weather).toBeDefined();
    expect(weather.micro_local_field).toBeDefined();
    expect(weather.slang_front_entries).toBeDefined();
    expect(weather.meme_front_templates).toBeDefined();
    expect(weather.short_term_symbolic_forecast).toBeDefined();
    expect(weather.metadata).toBeDefined();
    expect(weather.provenance).toBeDefined();
  });

  it("produces deterministic output", async () => {
    const context = ritualToContext(FIXED_RITUAL);
    const input: WeatherEngineInput = {
      oracleOutput: null,
      symbolicMetrics: {
        SDR: 0.5,
        MSI: 0.6,
        ARF: 0.3,
        NMC: 0.4,
        RFR: 0.5,
        Hσ: 0.7,
        λN: 0.8,
        ITC: 0.6,
      },
      context,
      timestamp: 1000000,
    };

    const weather1 = await generateSemioticWeather(input);
    const weather2 = await generateSemioticWeather(input);

    expect(weather1.macro_pressure_systems.dominant).toBe(
      weather2.macro_pressure_systems.dominant
    );
    expect(weather1.micro_local_field.veilbreakerInfluence).toBe(
      weather2.micro_local_field.veilbreakerInfluence
    );
  });

  it("exports to JSON", async () => {
    const context = ritualToContext(FIXED_RITUAL);
    const input: WeatherEngineInput = {
      oracleOutput: null,
      symbolicMetrics: {
        SDR: 0.5,
        MSI: 0.6,
        ARF: 0.3,
        NMC: 0.4,
        RFR: 0.5,
        Hσ: 0.7,
        λN: 0.8,
        ITC: 0.6,
      },
      context,
      timestamp: Date.now(),
    };

    const weather = await generateSemioticWeather(input);
    const json = weatherToJSON(weather);

    expect(json).toBeDefined();
    expect(typeof json).toBe("string");
    expect(JSON.parse(json)).toEqual(weather);
  });

  it("exports to Markdown", async () => {
    const context = ritualToContext(FIXED_RITUAL);
    const input: WeatherEngineInput = {
      oracleOutput: null,
      symbolicMetrics: {
        SDR: 0.5,
        MSI: 0.6,
        ARF: 0.3,
        NMC: 0.4,
        RFR: 0.5,
        Hσ: 0.7,
        λN: 0.8,
        ITC: 0.6,
      },
      context,
      timestamp: Date.now(),
    };

    const weather = await generateSemioticWeather(input);
    const markdown = weatherToMarkdown(weather);

    expect(markdown).toBeDefined();
    expect(typeof markdown).toBe("string");
    expect(markdown).toContain("# Semiotic Weather Forecast");
    expect(markdown).toContain("## Macro Pressure Systems");
    expect(markdown).toContain("## Short-term Forecast");
  });

  it("includes quality metadata", async () => {
    const context = ritualToContext(FIXED_RITUAL);
    const input: WeatherEngineInput = {
      oracleOutput: null,
      symbolicMetrics: {
        SDR: 0.5,
        MSI: 0.6,
        ARF: 0.3,
        NMC: 0.4,
        RFR: 0.5,
        Hσ: 0.7,
        λN: 0.8,
        ITC: 0.6,
      },
      context,
      timestamp: Date.now(),
    };

    const weather = await generateSemioticWeather(input);

    expect(weather.metadata.qualityScore).toBeGreaterThanOrEqual(0);
    expect(weather.metadata.qualityScore).toBeLessThanOrEqual(1);
    expect(weather.metadata.processingTime).toBeGreaterThan(0);
    expect(weather.metadata.entropyClass).toBe("high");
  });

  it("includes provenance", async () => {
    const context = ritualToContext(FIXED_RITUAL);
    const input: WeatherEngineInput = {
      oracleOutput: null,
      symbolicMetrics: {
        SDR: 0.5,
        MSI: 0.6,
        ARF: 0.3,
        NMC: 0.4,
        RFR: 0.5,
        Hσ: 0.7,
        λN: 0.8,
        ITC: 0.6,
      },
      context,
      timestamp: Date.now(),
    };

    const weather = await generateSemioticWeather(input);

    expect(weather.provenance.seed).toBe(FIXED_RITUAL.seed);
    expect(weather.provenance.runes).toEqual(FIXED_RITUAL.runes.map((r) => r.id));
    expect(weather.provenance.version).toBe("4.2.0");
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// Integration Tests
// ═══════════════════════════════════════════════════════════════════════════

describe("Weather Engine Integration", () => {
  it("different rituals produce different forecasts", async () => {
    const context1 = ritualToContext(FIXED_RITUAL);
    const context2 = ritualToContext(ALT_RITUAL);

    const input1: WeatherEngineInput = {
      oracleOutput: null,
      symbolicMetrics: {
        SDR: 0.5,
        MSI: 0.6,
        ARF: 0.3,
        NMC: 0.4,
        RFR: 0.5,
        Hσ: 0.7,
        λN: 0.8,
        ITC: 0.6,
      },
      context: context1,
      timestamp: Date.now(),
    };

    const input2: WeatherEngineInput = {
      ...input1,
      context: context2,
    };

    const weather1 = await generateSemioticWeather(input1);
    const weather2 = await generateSemioticWeather(input2);

    // Seeds are different, so outputs should differ
    expect(weather1.provenance.seed).not.toBe(weather2.provenance.seed);
  });

  it("handles edge case: zero metrics", async () => {
    const context = ritualToContext(FIXED_RITUAL);
    const input: WeatherEngineInput = {
      oracleOutput: null,
      symbolicMetrics: {
        SDR: 0,
        MSI: 0,
        ARF: 0,
        NMC: 0,
        RFR: 0,
        Hσ: 0,
        λN: 0,
        ITC: 0,
      },
      context,
      timestamp: Date.now(),
    };

    const weather = await generateSemioticWeather(input);
    expect(weather).toBeDefined();
    expect(weather.metadata.qualityScore).toBe(0);
  });

  it("handles edge case: maximum metrics", async () => {
    const context = ritualToContext(FIXED_RITUAL);
    const input: WeatherEngineInput = {
      oracleOutput: null,
      symbolicMetrics: {
        SDR: 1,
        MSI: 1,
        ARF: 1,
        NMC: 1,
        RFR: 1,
        Hσ: 1,
        λN: 1,
        ITC: 1,
      },
      context,
      timestamp: Date.now(),
    };

    const weather = await generateSemioticWeather(input);
    expect(weather).toBeDefined();
    expect(weather.metadata.qualityScore).toBe(1);
  });
});
