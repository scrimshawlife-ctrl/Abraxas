// Cryptographic utilities for Abraxas
import crypto from "crypto";

export function seal(data) {
  // Create a cryptographic seal for ritual results
  const serialized = JSON.stringify(data);
  const hash = crypto.createHash("sha256").update(serialized).digest("hex");
  const timestamp = Date.now();
  
  return {
    hash: hash.substring(0, 16),
    timestamp,
    signature: `⟟Σ${hash.substring(0, 8)}Σ⟟`
  };
}

export function fingerprint(source) {
  // Generate consistent fingerprint for sources
  return crypto.createHash("md5").update(source).digest("hex").substring(0, 12);
}