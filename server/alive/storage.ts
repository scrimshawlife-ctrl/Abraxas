import type { AliveRunInput, AliveRunResult, AliveTier } from "@shared/alive/schema";
import { aliveRuns } from "@shared/schema";
import { db } from "../db";

export async function persistAliveRun(
  input: AliveRunInput,
  run: AliveRunResult,
  filtered: AliveRunResult,
  tier: AliveTier
) {
  const runId = run.provenance?.run_id || `alive_${Date.now()}`;
  const result = await db
    .insert(aliveRuns)
    .values({
      runId,
      tier,
      input,
      run,
      filtered,
    })
    .returning();
  return result[0];
}
