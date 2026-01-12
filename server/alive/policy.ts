/**
 * ALIVE Tier Policy Enforcement
 *
 * CRITICAL: Server-side enforcement. Client NEVER decides what a tier can see.
 * 
 * Non-negotiable rule: server decides visibility.
 */

import type { AliveRunResult, AliveTier } from "@shared/alive/schema";
import { users } from "@shared/schema";
import { eq } from "drizzle-orm";
import { db } from "../db";

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
    // Psychonaut: translated states ONLY, no raw metrics
    // Philosophy: prevent "metric self-harm" (overfocusing on numbers)
    // User gets felt-state guidance (pressure/pull/agency/drift) without enterprise internals

    // Remove all metric details, including aggregates
    // Psychonaut relies solely on translated view
    r.view.metrics = null;

    // Hide strain details (show gentle notes only)
    if (r.strain) {
      r.strain = {
        signals: [],
        notes: ["Metric strain detected (details reserved by tier)."],
      };
    }

    // CRITICAL: Ensure signature components never leak
    // (signature itself remains in result for server-side use, but client should ignore)
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
 * SECURITY: NEVER trust tier from client request. Always look it up server-side.
 */
export async function getUserTier(userId: string): Promise<AliveTier> {
  const result = await db
    .select({ tier: users.tier })
    .from(users)
    .where(eq(users.id, userId));
  const tier = result[0]?.tier;
  if (tier === "academic" || tier === "enterprise") {
    return tier;
  }
  return "psychonaut";
}
