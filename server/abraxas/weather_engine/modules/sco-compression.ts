/**
 * ABX-Core - SCO Compression Weather Module
 * Symbolic compression events as memetic weather patterns
 * @module abraxas/weather_engine/modules/sco-compression
 */

import type { SymbolicCompressionEvent } from "../../integrations/sco-bridge";

export interface SCOCompressionSignal {
  type: "sco_compression";
  intensity: number; // 0-1
  pressure: number; // Compression pressure
  drift: number; // Transparency drift
  affect: {
    humor: number;
    aggression: number;
    authority: number;
    intimacy: number;
    nihilism: number;
    irony: number;
  };
  tierDistribution: {
    eco_t1: number; // High-fidelity eggcorns
    sco_t2: number; // General compression
  };
  eventCount: number;
  dominantAxis: string;
  forecast: string;
}

/**
 * Compute SCO compression weather signal
 */
export function computeSCOCompression(events: SymbolicCompressionEvent[]): SCOCompressionSignal {
  if (events.length === 0) {
    return {
      type: "sco_compression",
      intensity: 0,
      pressure: 0,
      drift: 0,
      affect: {
        humor: 0,
        aggression: 0,
        authority: 0,
        intimacy: 0,
        nihilism: 0,
        irony: 0,
      },
      tierDistribution: { eco_t1: 0, sco_t2: 0 },
      eventCount: 0,
      dominantAxis: "none",
      forecast: "Stable symbolic terrain. No compression detected.",
    };
  }

  // Average compression pressure
  const avgPressure =
    events.reduce((sum, e) => sum + e.compression_pressure, 0) / events.length;

  // Average transparency drift
  const avgDrift =
    events.reduce((sum, e) => sum + e.semantic_transparency_delta, 0) / events.length;

  // Aggregate affect (RDV)
  const affect = {
    humor: 0,
    aggression: 0,
    authority: 0,
    intimacy: 0,
    nihilism: 0,
    irony: 0,
  };

  for (const event of events) {
    for (const [axis, value] of Object.entries(event.replacement_direction_vector)) {
      affect[axis as keyof typeof affect] += value;
    }
  }

  // Normalize affect
  for (const axis of Object.keys(affect) as Array<keyof typeof affect>) {
    affect[axis] /= events.length;
  }

  // Find dominant axis
  const dominantAxis = Object.entries(affect).reduce((max, [axis, value]) =>
    value > max[1] ? [axis, value] : max
  )[0];

  // Tier distribution
  const eco_t1 = events.filter((e) => e.tier === "ECO_T1").length / events.length;
  const sco_t2 = events.filter((e) => e.tier === "SCO_T2").length / events.length;

  // Intensity (0-1 scale based on pressure and event frequency)
  const frequencyFactor = Math.min(1, events.length / 20);
  const pressureFactor = Math.min(1, avgPressure / 2.0);
  const intensity = (frequencyFactor + pressureFactor) / 2;

  // Generate forecast
  const forecast = generateForecast(intensity, avgPressure, dominantAxis, eco_t1);

  return {
    type: "sco_compression",
    intensity: +intensity.toFixed(4),
    pressure: +avgPressure.toFixed(4),
    drift: +avgDrift.toFixed(4),
    affect,
    tierDistribution: { eco_t1: +eco_t1.toFixed(2), sco_t2: +sco_t2.toFixed(2) },
    eventCount: events.length,
    dominantAxis,
    forecast,
  };
}

/**
 * Generate human-readable forecast from SCO metrics
 */
function generateForecast(
  intensity: number,
  pressure: number,
  dominantAxis: string,
  eco_t1: number
): string {
  let base = "";

  // Intensity classification
  if (intensity < 0.3) {
    base = "Mild symbolic compression.";
  } else if (intensity < 0.6) {
    base = "Moderate compression pressure building.";
  } else if (intensity < 0.85) {
    base = "Strong symbolic drift detected.";
  } else {
    base = "Severe memetic compression event.";
  }

  // Tier quality
  let quality = "";
  if (eco_t1 > 0.6) {
    quality = " High-fidelity eggcorn formation dominant.";
  } else if (eco_t1 > 0.3) {
    quality = " Mixed compression tiers.";
  } else {
    quality = " General symbolic substitution patterns.";
  }

  // Affective tilt
  let affective = "";
  if (dominantAxis !== "none") {
    const axisMap: Record<string, string> = {
      humor: "Humorous affect amplifying spread.",
      aggression: "Aggressive tonality driving compression.",
      authority: "Authoritative framing emerging.",
      intimacy: "Intimate/communal resonance detected.",
      nihilism: "Nihilistic drift accelerating.",
      irony: "Ironic distancing in effect.",
    };
    affective = ` ${axisMap[dominantAxis] || ""}`;
  }

  return base + quality + affective;
}

/**
 * Convert SCO signal to Weather Engine narrative
 */
export function scoToWeatherNarrative(signal: SCOCompressionSignal): string {
  const { intensity, pressure, drift, dominantAxis, tierDistribution } = signal;

  const lines: string[] = [];

  lines.push(`**Symbolic Compression Weather**`);
  lines.push(``);
  lines.push(`Intensity: ${(intensity * 100).toFixed(1)}%`);
  lines.push(`Compression Pressure: ${pressure.toFixed(2)}`);
  lines.push(`Transparency Drift: ${drift.toFixed(2)}`);
  lines.push(``);
  lines.push(`**Tier Distribution:**`);
  lines.push(`- ECO-T1 (Eggcorns): ${(tierDistribution.eco_t1 * 100).toFixed(0)}%`);
  lines.push(`- SCO-T2 (General): ${(tierDistribution.sco_t2 * 100).toFixed(0)}%`);
  lines.push(``);
  lines.push(`**Dominant Affective Axis:** ${dominantAxis}`);
  lines.push(``);
  lines.push(`**Forecast:**`);
  lines.push(signal.forecast);

  return lines.join("\n");
}
