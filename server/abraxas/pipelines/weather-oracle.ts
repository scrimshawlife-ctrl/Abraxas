/**
 * ABX-Core v1.3 - Weather Oracle Pipeline
 * Integrates Semiotic Weather Engine with Daily Oracle
 * Weather Engine runs after Oracle, using Oracle output as input
 *
 * @module abraxas/pipelines/weather-oracle
 * @entropy_class high
 * @deterministic true
 * @capabilities { read: ["oracle_output"], write: ["weather_forecast"], network: false }
 * @version 4.2.0
 */

import type { RitualInput } from "../models/ritual";
import type { DailyOracleOutput } from "../models/oracle";
import { generateDailyCiphergram } from "./daily-oracle";
import {
  generateSemioticWeather,
  weatherToJSON,
  weatherToMarkdown,
} from "../weather_engine/core/orchestrator";
import type {
  WeatherEngineInput,
  WeatherEngineOutput,
} from "../weather_engine/core/types";
import { ritualToContext } from "../integrations/runes-adapter";

export interface WeatherOracleOutput {
  oracle: DailyOracleOutput;
  weather: WeatherEngineOutput;
  combined: {
    timestamp: number;
    seed: string;
    version: string;
  };
}

/**
 * Run Oracle → Weather Engine pipeline
 * The Weather Engine uses the Oracle's output and symbolic metrics as input
 */
export async function generateWeatherOracle(
  ritual: RitualInput
): Promise<WeatherOracleOutput> {
  // Step 1: Generate daily oracle
  const oracle = await generateDailyCiphergram(ritual);

  // Step 2: Prepare Weather Engine input using Oracle's output
  const context = ritualToContext(ritual);
  const weatherInput: WeatherEngineInput = {
    oracleOutput: oracle,
    symbolicMetrics: oracle.symbolicMetrics,
    context,
    timestamp: Date.now(),
  };

  // Step 3: Generate weather forecast
  const weather = await generateSemioticWeather(weatherInput);

  // Step 4: Return combined output
  return {
    oracle,
    weather,
    combined: {
      timestamp: Date.now(),
      seed: ritual.seed,
      version: "4.2.0",
    },
  };
}

/**
 * Standalone weather generation (without oracle)
 * Useful for manual weather checks
 */
export async function generateStandaloneWeather(
  ritual: RitualInput
): Promise<WeatherEngineOutput> {
  const context = ritualToContext(ritual);

  const weatherInput: WeatherEngineInput = {
    oracleOutput: null,
    symbolicMetrics: {
      SDR: 0.5,
      MSI: 0.5,
      ARF: 0,
      NMC: 0,
      RFR: 0.5,
      Hσ: 0.5,
      λN: 0.5,
      ITC: 0.5,
    },
    context,
    timestamp: Date.now(),
  };

  return await generateSemioticWeather(weatherInput);
}

/**
 * Export weather in different formats
 */
export function exportWeather(
  weather: WeatherEngineOutput,
  format: "json" | "markdown" = "json"
): string {
  return format === "json" ? weatherToJSON(weather) : weatherToMarkdown(weather);
}
