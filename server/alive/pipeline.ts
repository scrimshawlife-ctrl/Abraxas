/**
 * ALIVE Pipeline
 *
 * Orchestrates the flow: ingest → normalize → call Python core → persist → return tier-filtered view
 */

import type { AliveRunInput, AliveRunResult, AliveTier } from "@shared/alive/schema";
import { applyTierPolicy } from "./policy";
import { promisify } from "util";
import { persistAliveRun } from "./storage";

const execFile = promisify(require("child_process").execFile);

export interface ALIVEPipelineResult {
  run: AliveRunResult;
  tier: AliveTier;
  filtered: AliveRunResult;
}

/**
 * Run ALIVE analysis pipeline.
 *
 * @param input - Analysis input configuration
 * @returns Promise resolving to tier-filtered field signature
 */
export async function runALIVEPipeline(
  input: AliveRunInput
): Promise<ALIVEPipelineResult> {
  // Step 1: Normalize and validate input
  const normalizedInput = normalizeInput(input);

  // Step 2: Call Python core engine
  const run = await callPythonEngine(normalizedInput);

  // Step 3: Apply tier-based filtering
  const filtered = applyTierPolicy(run, input.tier);

  // Step 4: Persist raw results + filtered output
  try {
    await persistAliveRun(normalizedInput, run, filtered, input.tier);
  } catch (error) {
    console.warn("Failed to persist ALIVE run:", error);
  }

  return {
    run,
    tier: input.tier,
    filtered,
  };
}

/**
 * Normalize input data before processing.
 */
function normalizeInput(input: AliveRunInput): AliveRunInput {
  return { ...input };
}

/**
 * Call Python ALIVE engine via subprocess.
 */
async function callPythonEngine(
  input: AliveRunInput
): Promise<AliveRunResult> {
  try {
    // Call Python module
    const args = ["-m", "abraxas.alive.core", JSON.stringify(input.artifact), input.tier];

    if (input.profile) {
      args.push(JSON.stringify(input.profile));
    }

    const { stdout, stderr } = await execFile("python3", args);

    if (stderr) {
      console.warn("Python stderr:", stderr);
    }

    // Parse output
    const result = JSON.parse(stdout);
    return result as AliveRunResult;
  } catch (error) {
    console.error("Error calling Python engine:", error);
    throw error;
  }
}
