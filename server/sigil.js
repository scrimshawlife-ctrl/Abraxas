// Sigil generation system for Abraxas
import crypto from "crypto";

export function forgeSigil(phrase) {
  // Traditional sigil method: remove vowels and repeating letters
  const core = phrase
    .toUpperCase()
    .replace(/[AEIOU\s]/g, "")
    .split("")
    .filter((char, index, arr) => arr.indexOf(char) === index)
    .join("")
    .slice(0, 8) || "SIGIL";

  // Generate cryptographic seed
  const seed = crypto.randomBytes(8).toString("hex");
  
  return {
    core,
    seed,
    method: "traditional_strip+grid3x3+seeded_quadratic"
  };
}