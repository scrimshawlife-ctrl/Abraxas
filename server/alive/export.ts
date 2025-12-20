/**
 * ALIVE Golden Artifact Export
 *
 * JSON export is the canonical format. All other exports (PDF, CSV, Slack, BI)
 * are views of this golden artifact.
 *
 * Signed exports include:
 * - Schema version
 * - Metric version hashes
 * - Timestamp
 * - Decay context (provenance weights)
 * - HMAC signature for integrity
 */

import crypto from "crypto";
import type { ALIVEFieldSignature } from "@shared/alive/schema";
import { ALIVE_SCHEMA_VERSION } from "@shared/alive/schema";

// ═══════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════

export interface SignedExport {
  // Payload
  fieldSignature: Partial<ALIVEFieldSignature>;

  // Metadata
  meta: {
    schemaVersion: string;
    metricVersions: Record<string, string>; // metricId → version
    exportedAt: string;
    expiresAt: string;
    tier: string;
  };

  // Decay context
  decayContext: {
    provenanceWeights: Array<{
      sourceId: string;
      sourceType: string;
      weight: number;
    }>;
    decayFactor?: number;
  };

  // Signature
  signature: string;
  signatureAlgorithm: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// EXPORT FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Create signed JSON export (golden artifact).
 *
 * This is the canonical export format. All other formats derive from this.
 *
 * @param fieldSignature - Tier-filtered field signature
 * @param tier - User's tier
 * @param options - Export options
 * @returns Signed export artifact
 */
export function createSignedExport(
  fieldSignature: Partial<ALIVEFieldSignature>,
  tier: string,
  options?: {
    includeProvenance?: boolean;
    ttlHours?: number;
  }
): SignedExport {
  const now = new Date();
  const ttlHours = options?.ttlHours || 24;
  const expiresAt = new Date(now.getTime() + ttlHours * 60 * 60 * 1000);

  // Extract metric versions
  const metricVersions: Record<string, string> = {};

  for (const metric of fieldSignature.influence || []) {
    metricVersions[metric.metricId] = metric.metricVersion;
  }
  for (const metric of fieldSignature.vitality || []) {
    metricVersions[metric.metricId] = metric.metricVersion;
  }
  for (const metric of fieldSignature.lifeLogistics || []) {
    metricVersions[metric.metricId] = metric.metricVersion;
  }

  // Extract decay context from provenance
  const decayContext = {
    provenanceWeights: (fieldSignature.corpusProvenance || []).map((p) => ({
      sourceId: p.sourceId,
      sourceType: p.sourceType,
      weight: p.weight,
    })),
  };

  // Build export payload
  const payload: Omit<SignedExport, "signature" | "signatureAlgorithm"> = {
    fieldSignature,
    meta: {
      schemaVersion: fieldSignature.schemaVersion || ALIVE_SCHEMA_VERSION,
      metricVersions,
      exportedAt: now.toISOString(),
      expiresAt: expiresAt.toISOString(),
      tier,
    },
    decayContext,
  };

  // Generate signature
  const signatureData = generateSignature(payload);

  return {
    ...payload,
    ...signatureData,
  };
}

/**
 * Generate HMAC signature for export.
 *
 * Uses SHA-256 HMAC for integrity verification.
 */
function generateSignature(payload: any): {
  signature: string;
  signatureAlgorithm: string;
} {
  // TODO: Use proper secret from environment
  const secret = process.env.ALIVE_EXPORT_SECRET || "alive-dev-secret";

  // Canonicalize payload for signing
  const canonical = JSON.stringify(payload, Object.keys(payload).sort());

  // Generate HMAC
  const hmac = crypto.createHmac("sha256", secret);
  hmac.update(canonical);
  const signature = hmac.digest("hex");

  return {
    signature,
    signatureAlgorithm: "HMAC-SHA256",
  };
}

/**
 * Verify export signature.
 *
 * @param signedExport - Signed export to verify
 * @returns True if signature is valid
 */
export function verifySignature(signedExport: SignedExport): boolean {
  const { signature: providedSignature, signatureAlgorithm, ...payload } = signedExport;

  if (signatureAlgorithm !== "HMAC-SHA256") {
    return false;
  }

  const { signature: computedSignature } = generateSignature(payload);

  return crypto.timingSafeEqual(
    Buffer.from(providedSignature, "hex"),
    Buffer.from(computedSignature, "hex")
  );
}

/**
 * Check if export has expired.
 */
export function isExpired(signedExport: SignedExport): boolean {
  const expiresAt = new Date(signedExport.meta.expiresAt);
  return expiresAt < new Date();
}

/**
 * Export as JSON string (pretty-printed).
 */
export function exportAsJSON(signedExport: SignedExport, pretty = true): string {
  return JSON.stringify(signedExport, null, pretty ? 2 : 0);
}

/**
 * Export as compact JSON (single line, no whitespace).
 */
export function exportAsCompactJSON(signedExport: SignedExport): string {
  return JSON.stringify(signedExport);
}
