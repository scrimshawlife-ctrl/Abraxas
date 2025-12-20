/**
 * ALIVE Pipeline
 *
 * Orchestrates the flow: ingest → normalize → call Python core → persist → return tier-filtered view
 */

import type { ALIVERunInput, ALIVEFieldSignature } from "@shared/alive/schema";
import { applyTierFilter } from "./policy";
import { spawn } from "child_process";
import { promisify } from "util";

const execFile = promisify(require("child_process").execFile);

export interface ALIVEPipelineResult {
  fieldSignature: ALIVEFieldSignature;
  tier: string;
  filteredView: Partial<ALIVEFieldSignature>;
}

/**
 * Run ALIVE analysis pipeline.
 *
 * @param input - Analysis input configuration
 * @returns Promise resolving to tier-filtered field signature
 */
export async function runALIVEPipeline(
  input: ALIVERunInput
): Promise<ALIVEPipelineResult> {
  // Step 1: Normalize and validate input
  const normalizedInput = normalizeInput(input);

  // Step 2: Call Python core engine
  const fieldSignature = await callPythonEngine(normalizedInput);

  // Step 3: Persist raw results (TODO: add DB storage)
  // await persistFieldSignature(fieldSignature);

  // Step 4: Apply tier-based filtering
  const filteredView = applyTierFilter(fieldSignature, input.tier);

  return {
    fieldSignature,
    tier: input.tier,
    filteredView,
  };
}

/**
 * Normalize input data before processing.
 */
function normalizeInput(input: ALIVERunInput): ALIVERunInput {
  // Add default timestamp if not present
  const normalized = { ...input };

  if (!normalized.corpusConfig.timeRange) {
    // Default to last 30 days
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);

    normalized.corpusConfig.timeRange = {
      start: start.toISOString(),
      end: end.toISOString(),
    };
  }

  return normalized;
}

/**
 * Call Python ALIVE engine via subprocess.
 *
 * TODO: Consider using a persistent Python worker or HTTP bridge for better performance.
 */
async function callPythonEngine(
  input: ALIVERunInput
): Promise<ALIVEFieldSignature> {
  try {
    // Serialize input to JSON
    const inputJson = JSON.stringify(input);

    // Call Python module
    const { stdout, stderr } = await execFile("python3", [
      "-m",
      "abraxas.alive.core",
      "--input",
      inputJson,
    ]);

    if (stderr) {
      console.warn("Python stderr:", stderr);
    }

    // Parse output
    const result = JSON.parse(stdout);
    return result as ALIVEFieldSignature;
  } catch (error) {
    console.error("Error calling Python engine:", error);

    // For now, return stub data on error
    // TODO: Implement proper error handling
    return createStubFieldSignature(input);
  }
}

/**
 * Create stub field signature (fallback).
 */
function createStubFieldSignature(input: ALIVERunInput): ALIVEFieldSignature {
  const now = new Date().toISOString();

  return {
    analysisId: `stub_${Date.now()}`,
    subjectId: input.subjectId,
    timestamp: now,
    influence: [
      {
        metricId: "influence.network_position",
        metricVersion: "1.0.0",
        status: "promoted",
        value: 0.65,
        confidence: 0.8,
        timestamp: now,
      },
    ],
    vitality: [
      {
        metricId: "vitality.creative_momentum",
        metricVersion: "1.0.0",
        status: "promoted",
        value: 0.58,
        confidence: 0.7,
        timestamp: now,
      },
    ],
    lifeLogistics: [
      {
        metricId: "life_logistics.time_debt",
        metricVersion: "1.0.0",
        status: "promoted",
        value: 0.45,
        confidence: 0.65,
        timestamp: now,
      },
    ],
    compositeScore: {
      overall: 0.62,
      influenceWeight: 0.33,
      vitalityWeight: 0.34,
      lifeLogisticsWeight: 0.33,
    },
    corpusProvenance: [
      {
        sourceId: "stub_source",
        sourceType: "twitter",
        weight: 1.0,
        timestamp: now,
      },
    ],
  };
}
