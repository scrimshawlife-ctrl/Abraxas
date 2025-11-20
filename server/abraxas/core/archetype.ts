/**
 * ABX-Core v1.2 - Archetype System
 * SEED Framework Compliant
 *
 * @module abraxas/core/archetype
 * @entropy_class low
 * @deterministic true
 * @capabilities { read: ["archetypes", "runes"], write: ["resonance"], network: false }
 *
 * Defines archetypal patterns and their resonance with market dynamics
 */

import crypto from "crypto";

// ═══════════════════════════════════════════════════════════════════════════
// Archetype Definitions
// ═══════════════════════════════════════════════════════════════════════════

export interface Archetype {
  id: string;
  name: string;
  domain: string;
  traits: string[];
  polarities: {
    growth: number;      // [-1, 1] expansion vs contraction
    stability: number;   // [-1, 1] chaos vs order
    momentum: number;    // [-1, 1] inertia vs dynamism
  };
  associations: {
    runes: string[];
    sectors: string[];
    features: string[];
  };
}

export const ARCHETYPES: Record<string, Archetype> = {
  warrior: {
    id: "warrior",
    name: "The Warrior",
    domain: "Action, aggression, conquest",
    traits: ["decisive", "aggressive", "competitive", "bold"],
    polarities: {
      growth: 0.7,
      stability: -0.4,
      momentum: 0.8,
    },
    associations: {
      runes: ["aether", "flux"],
      sectors: ["Technology", "Aerospace & Defense"],
      features: ["sam_mod_scope_delta", "jobs_clearance_burst", "momentum"],
    },
  },

  sage: {
    id: "sage",
    name: "The Sage",
    domain: "Wisdom, knowledge, analysis",
    traits: ["analytical", "patient", "strategic", "measured"],
    polarities: {
      growth: 0.3,
      stability: 0.7,
      momentum: -0.2,
    },
    associations: {
      runes: ["glyph", "nexus"],
      sectors: ["Healthcare", "Financials"],
      features: ["gematria_alignment", "astro_rul_align"],
    },
  },

  fool: {
    id: "fool",
    name: "The Fool",
    domain: "Chaos, innovation, disruption",
    traits: ["unpredictable", "creative", "disruptive", "volatile"],
    polarities: {
      growth: 0.5,
      stability: -0.8,
      momentum: 0.6,
    },
    associations: {
      runes: ["flux", "tide"],
      sectors: ["Tech", "Consumer"],
      features: ["ptab_ipr_burst", "fr_waiver_absence"],
    },
  },

  monarch: {
    id: "monarch",
    name: "The Monarch",
    domain: "Order, structure, dominance",
    traits: ["authoritative", "stable", "hierarchical", "conservative"],
    polarities: {
      growth: 0.2,
      stability: 0.9,
      momentum: -0.3,
    },
    associations: {
      runes: ["ward", "nexus"],
      sectors: ["Energy", "Utilities", "Financials"],
      features: ["nightlights_z", "port_dwell_delta"],
    },
  },

  trickster: {
    id: "trickster",
    name: "The Trickster",
    domain: "Deception, volatility, opportunity",
    traits: ["cunning", "adaptable", "opportunistic", "elusive"],
    polarities: {
      growth: 0.4,
      stability: -0.6,
      momentum: 0.7,
    },
    associations: {
      runes: ["flux", "glyph"],
      sectors: ["Fintech", "Crypto"],
      features: ["fx_basis_z", "hs_code_volume_z"],
    },
  },
};

// ═══════════════════════════════════════════════════════════════════════════
// Archetype Mapping & Resonance
// ═══════════════════════════════════════════════════════════════════════════

function deterministicHash(input: string): number {
  return parseInt(
    crypto.createHash("sha256").update(input).digest("hex").slice(0, 8),
    16
  );
}

/**
 * Map a subject (ticker, pair, sector) to dominant archetype
 */
export function mapToArchetype(
  subject: string,
  features: Record<string, number>,
  seed: string
): Archetype {
  const archetypeList = Object.values(ARCHETYPES);

  // Score each archetype based on feature alignment
  const scores = archetypeList.map((archetype) => {
    let score = 0;

    // Feature association score
    archetype.associations.features.forEach((feature) => {
      if (features[feature] !== undefined) {
        score += Math.abs(features[feature]) * 2;
      }
    });

    // Deterministic subject-archetype affinity
    const affinity = (deterministicHash(subject + archetype.id + seed) % 100) / 100;
    score += affinity;

    return { archetype, score };
  });

  // Return archetype with highest score
  scores.sort((a, b) => b.score - a.score);
  return scores[0].archetype;
}

/**
 * Compute resonance between features and archetype polarities
 */
export function computeArchetypeResonance(
  features: Record<string, number>,
  archetype: Archetype
): number {
  // Compute feature-implied polarities
  const featurePolarities = {
    growth: 0,
    stability: 0,
    momentum: 0,
  };

  let featureCount = 0;

  archetype.associations.features.forEach((feature) => {
    if (features[feature] !== undefined) {
      const magnitude = features[feature];
      featurePolarities.growth += magnitude * 0.5;
      featurePolarities.stability += magnitude * 0.3;
      featurePolarities.momentum += magnitude * 0.7;
      featureCount++;
    }
  });

  if (featureCount > 0) {
    featurePolarities.growth /= featureCount;
    featurePolarities.stability /= featureCount;
    featurePolarities.momentum /= featureCount;
  }

  // Compute dot product with archetype polarities
  const resonance =
    featurePolarities.growth * archetype.polarities.growth +
    featurePolarities.stability * archetype.polarities.stability +
    featurePolarities.momentum * archetype.polarities.momentum;

  // Normalize to [-1, 1]
  return Math.max(-1, Math.min(1, resonance / 3));
}

/**
 * Select archetypes compatible with given runes
 */
export function selectArchetypesForRunes(runes: string[]): Archetype[] {
  return Object.values(ARCHETYPES).filter((archetype) => {
    // Check if any of the runes match archetype associations
    return runes.some((rune) => archetype.associations.runes.includes(rune));
  });
}

/**
 * Generate archetypal narrative based on resonance
 */
export function generateArchetypeNarrative(
  archetype: Archetype,
  resonance: number
): string {
  if (resonance > 0.5) {
    return `Strong ${archetype.name} resonance: ${archetype.domain} dominates`;
  } else if (resonance > 0) {
    return `Moderate ${archetype.name} alignment: ${archetype.traits[0]} tendencies`;
  } else if (resonance > -0.5) {
    return `Weak ${archetype.name} dissonance: conflicting patterns`;
  } else {
    return `Strong opposition to ${archetype.name}: inverse ${archetype.domain}`;
  }
}
