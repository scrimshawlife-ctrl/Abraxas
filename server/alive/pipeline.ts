/**
 * ALIVE Pipeline
 *
 * Orchestrates the flow: ingest → normalize → call Python core → persist → return tier-filtered view
 */

import type { AliveRunInput, AliveRunResult, AliveTier } from "@shared/alive/schema";
import { ALIVE_ENGINE_VERSION, ALIVE_SCHEMA_VERSION } from "@shared/alive/schema";
import { applyTierPolicy } from "./policy";
import { createHash } from "crypto";
import { promisify } from "util";

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

  // Step 3: Persist raw results (TODO: add DB storage)
  // await persistRunResult(run);

  // Step 4: Apply tier-based filtering
  const filtered = applyTierPolicy(run, input.tier);

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
 *
 * TODO: Consider using a persistent Python worker or HTTP bridge for better performance.
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

    // For now, return stub data on error
    // TODO: Implement proper error handling
    return createStubRunResult(input);
  }
}

/**
 * Create stub run result (fallback).
 */
function createStubRunResult(input: AliveRunInput): AliveRunResult {
  const now = new Date().toISOString();
  const inputHash = createHash("sha256")
    .update(JSON.stringify(input.artifact))
    .digest("hex");
  const profileHash = input.profile
    ? createHash("sha256").update(JSON.stringify(input.profile)).digest("hex")
    : undefined;
  const signature = {
    influence: [],
    vitality: [],
    life_logistics: [],
  };

  return {
    provenance: {
      run_id: `stub_${Date.now()}`,
      created_at: now,
      schema_version: ALIVE_SCHEMA_VERSION,
      engine_version: ALIVE_ENGINE_VERSION,
      metric_registry_hash: "unwired",
      input_hash: inputHash,
      profile_hash: profileHash,
      corpus_context: {
        corpus_version: "unwired",
        decay_policy_hash: "unwired",
      },
    },
    artifact: input.artifact,
    signature,
    view: {
      tier: input.tier,
      metrics: input.tier === "psychonaut" ? null : signature,
    },
  };
}
