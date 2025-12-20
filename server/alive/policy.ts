/**
 * ALIVE Tier Policy Enforcement
 *
 * CRITICAL: Server-side enforcement. Client NEVER decides what a tier can see.
 * 
 * Non-negotiable rule: server decides visibility.
 */

import type { AliveRunResult, AliveTier } from "@shared/alive/schema";

/**
 * Apply tier-based filtering to ALIVE run result.
 *
 * SECURITY: This function MUST be called before returning data to client.
 *
 * @param result - Full ALIVE run result
 * @param tier - User's tier level (validated server-side)
 * @returns Tier-filtered result
 */
export function applyTierPolicy(result: AliveRunResult, tier: AliveTier): AliveRunResult {
  // Deep clone to avoid mutations
  const r: AliveRunResult = structuredClone(result);

  // Always set view.tier
  r.view.tier = tier;

  if (tier === "psychonaut") {
    // Psychonaut: translated states only, no raw metrics by default
    if (r.view.metrics) {
      // Redact: keep only aggregates, drop per-metric list
      r.view.metrics = {
        influence: [],
        vitality: [],
        life_logistics: [],
        aggregates: r.signature.aggregates,
      };
    }

    // Hide strain details (show gentle notes only)
    if (r.strain) {
      r.strain = {
        signals: [],
        notes: ["Metric strain detected (details reserved by tier)."],
      };
    }
  }

  if (tier === "academic") {
    // Academic: full metrics + strain visibility
    // (No filtering needed - they see everything)
  }

  if (tier === "enterprise") {
    // Enterprise: full metrics, redacted strain
    if (r.strain) {
      // Enterprise sees strain exists but not full analysis
      r.strain = {
        signals: [],
        notes: r.strain.notes || ["Strain analysis available in academic tier."],
      };
    }
  }

  return r;
}

/**
 * Validate tier string against allowed values.
 *
 * SECURITY: Always validate tier before using it.
 */
export function validateTier(tier: string): tier is AliveTier {
  return ["psychonaut", "academic", "enterprise"].includes(tier);
}

/**
 * Get user's tier from session/database.
 *
 * TODO: Implement actual user tier lookup from database.
 * For now, returns psychonaut as default.
 *
 * SECURITY: NEVER trust tier from client request. Always look it up server-side.
 */
export async function getUserTier(userId: string): Promise<AliveTier> {
  // TODO: Look up from database
  // const user = await db.users.findOne({ id: userId });
  // return user.tier || "psychonaut";

  return "psychonaut";
}
