import { getTodayRunes, runRitual } from "../../runes.js";

const RUNES_REGISTRY = [
  {
    runeId: "ABX_RUNES_GET_TODAY",
    capability: "runes:get_today",
    name: "Get Today Runes",
    version: "1.0.0",
    deterministic: true,
    inputs: [],
    outputs: ["runes"],
    handler: (_input, _ctx) => getTodayRunes(),
  },
  {
    runeId: "ABX_RUNES_RUN_RITUAL",
    capability: "runes:run_ritual",
    name: "Run Ritual",
    version: "1.0.0",
    deterministic: false,
    inputs: [],
    outputs: ["ritual"],
    handler: (_input, ctx) => runRitual(ctx?.run_id),
  },
];

export function getRuneRegistry() {
  return [...RUNES_REGISTRY];
}

export function listCapabilities() {
  return [...new Set(RUNES_REGISTRY.map((r) => r.capability))].sort();
}

export function listRunesByCapability(capability) {
  return RUNES_REGISTRY.filter((r) => r.capability === capability);
}

export function describeRune(runeId) {
  const match = RUNES_REGISTRY.find((r) => r.runeId === runeId);
  if (!match) {
    throw new Error(`Unknown rune id: ${runeId}`);
  }
  return match;
}

export function wiringSanityCheck(requiredCapabilities = []) {
  const seen = new Set();
  const duplicates = [];
  for (const rune of RUNES_REGISTRY) {
    if (seen.has(rune.runeId)) {
      duplicates.push(rune.runeId);
    }
    seen.add(rune.runeId);
  }

  const available = new Set(RUNES_REGISTRY.map((r) => r.capability));
  const missing = requiredCapabilities.filter((cap) => !available.has(cap));

  return { duplicateRuneIds: duplicates, missingCapabilities: missing };
}
