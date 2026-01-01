/**
 * ABX-Core v1.2 - Runic Symbolic System
 * SEED Framework Compliant
 *
 * @module runes
 * @entropy_class low
 * @deterministic true
 * @capabilities { read: ["date", "seed"], write: ["ritual_state"], network: false }
 */

// Mystical rune system for Abraxas
const RUNES = [
  { id: "aether", name: "Aether", color: "#FFD166", meaning: "cosmic flow" },
  { id: "tide", name: "Tide", color: "#4CC9F0", meaning: "market cycles" },
  { id: "ward", name: "Ward", color: "#F87171", meaning: "protection" },
  { id: "glyph", name: "Glyph", color: "#C6F6D5", meaning: "hidden knowledge" },
  { id: "flux", name: "Flux", color: "#A78BFA", meaning: "transformation" },
  { id: "nexus", name: "Nexus", color: "#FDE68A", meaning: "connection" }
];

export function getTodayRunes() {
  const today = new Date().toISOString().slice(0, 10);
  const seed = hashString(today);
  const count = 2 + (seed % 3); // 2-4 runes per day
  
  const selected = [];
  let tempSeed = seed;
  
  for (let i = 0; i < count; i++) {
    const index = tempSeed % RUNES.length;
    if (!selected.find(r => r.id === RUNES[index].id)) {
      selected.push(RUNES[index]);
    }
    tempSeed = Math.floor(tempSeed / RUNES.length) + 1;
  }
  
  return selected;
}

export function runRitual(runId) {
  const date = new Date().toISOString().slice(0, 10);
  const seedMaterial = runId ? `${date}:${runId}` : date;
  const seed = hashString(seedMaterial);
  const runes = getTodayRunes();

  return { date, seed, runes };
}

function hashString(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash);
}
