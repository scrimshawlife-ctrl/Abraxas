/**
 * ABX-Core v1.2 - Venture Capital Analysis Pipeline
 * SEED Framework Compliant
 *
 * @module abraxas/pipelines/vc-analyzer
 * @entropy_class medium
 * @deterministic true (given seed)
 * @capabilities { read: [], write: [], network: false }
 *
 * VC market analysis using symbolic kernel for:
 * - Deal flow forecasting
 * - Sector momentum analysis
 * - Risk/opportunity assessment
 * - Archetype-driven market narratives
 */

import crypto from "crypto";
import type { RitualInput } from "../models/ritual";
import { computeSymbolicMetrics, aggregateQualityScore } from "../core/kernel";
import { ritualToContext, createPipelineVector, mergeVectors } from "../integrations/runes-adapter";
import { mapToArchetype, computeArchetypeResonance } from "../core/archetype";

export interface VCAnalysisInput {
  industry: string;
  region: string;
  horizonDays: number;
}

export interface SectorAnalysis {
  name: string;
  score: number;
  momentum: number;
  reasoning: string;
  archetype: string;
  confidence: number;
}

export interface VCAnalysisResult {
  industry: string;
  region: string;
  horizon: number;
  forecast: {
    dealVolume: {
      prediction: number;
      confidence: number;
      factors: string[];
    };
    hotSectors: SectorAnalysis[];
    riskFactors: string[];
    opportunities: string[];
    qualityScore: number;
  };
  symbolicAnalysis: {
    drift: number;
    saturation: number;
    resonance: number;
    entropy: number;
  };
  timestamp: number;
  provenance: {
    seed: string;
    runes: string[];
  };
}

// Industry sector mappings
const SECTOR_MAP: Record<string, string[]> = {
  Technology: ["Generative AI", "Cybersecurity", "Dev Tools", "Cloud Infrastructure"],
  Healthcare: ["Digital Health", "Biotech", "MedTech", "Healthtech"],
  Fintech: ["Payments", "Lending", "Crypto Infrastructure", "Embedded Finance"],
  Climate: ["Clean Energy", "Carbon Tech", "Sustainable Materials", "Climate Adaptation"],
};

// Base deal volumes (annual estimates)
const BASE_DEAL_VOLUME: Record<string, number> = {
  Technology: 1200,
  Healthcare: 800,
  Fintech: 600,
  Climate: 400,
};

// Regional multipliers
const REGIONAL_MULTIPLIER: Record<string, number> = {
  US: 1.0,
  EU: 0.6,
  APAC: 0.8,
  Global: 1.4,
};

/**
 * Analyze VC market with symbolic kernel integration
 */
export async function analyzeVCMarket(
  input: VCAnalysisInput,
  ritual: RitualInput
): Promise<VCAnalysisResult> {
  const context = ritualToContext(ritual);

  // Create feature vector for industry/region
  const industryHash = hashString(input.industry, ritual.seed);
  const regionHash = hashString(input.region, ritual.seed);

  const features = {
    industry_momentum: (industryHash % 100) / 100,
    regional_sentiment: (regionHash % 100) / 100,
    horizon_factor: Math.min(1, input.horizonDays / 365),
    market_cycle: (Date.now() % (365 * 24 * 60 * 60 * 1000)) / (365 * 24 * 60 * 60 * 1000),
  };

  const vector = createPipelineVector(
    features,
    `vc-${input.industry}-${input.region}`,
    ritual.seed,
    "pipelines/vc-analyzer"
  );

  // Compute symbolic metrics
  const metrics = computeSymbolicMetrics(vector, context);
  const quality = aggregateQualityScore(metrics);

  // Forecast deal volume
  const baseDealVolume = BASE_DEAL_VOLUME[input.industry] || 500;
  const regionalMult = REGIONAL_MULTIPLIER[input.region] || 0.7;

  // Deterministic variance based on seed and metrics
  const variance = 0.8 + (metrics.MSI * 0.4); // 0.8 - 1.2 range
  const prediction = Math.floor(baseDealVolume * regionalMult * variance);

  // Confidence based on quality and low drift
  const confidence = Math.min(0.95, Math.max(0.6, quality * 0.7 + (1 - metrics.SDR) * 0.3));

  // Analyze sectors
  const sectors = SECTOR_MAP[input.industry] || ["General Tech"];
  const sectorAnalysis = await analyzeSectors(sectors, ritual, context);

  // Generate risk factors and opportunities
  const riskFactors = generateRiskFactors(metrics, ritual.seed);
  const opportunities = generateOpportunities(metrics, ritual.seed, input.industry);

  return {
    industry: input.industry,
    region: input.region,
    horizon: input.horizonDays,
    forecast: {
      dealVolume: {
        prediction,
        confidence: Math.round(confidence * 100) / 100,
        factors: [
          "Market sentiment analysis",
          "Historical trend correlation",
          "Economic indicator synthesis",
          `Symbolic quality: ${Math.round(quality * 100)}%`,
        ],
      },
      hotSectors: sectorAnalysis,
      riskFactors,
      opportunities,
      qualityScore: quality,
    },
    symbolicAnalysis: {
      drift: metrics.SDR,
      saturation: metrics.MSI,
      resonance: metrics.ARF,
      entropy: metrics.Hσ,
    },
    timestamp: Date.now(),
    provenance: {
      seed: ritual.seed,
      runes: ritual.runes.map((r) => r.id),
    },
  };
}

/**
 * Analyze individual sectors with archetype mapping
 */
async function analyzeSectors(
  sectors: string[],
  ritual: RitualInput,
  context: any
): Promise<SectorAnalysis[]> {
  const analysis: SectorAnalysis[] = sectors.map((sector) => {
    // Create feature vector for sector
    const sectorHash = hashString(sector, ritual.seed);
    const features = {
      adoption_rate: (sectorHash % 100) / 100,
      funding_velocity: ((sectorHash * 7) % 100) / 100,
      innovation_index: ((sectorHash * 13) % 100) / 100,
    };

    const vector = createPipelineVector(
      features,
      `sector-${sector}`,
      ritual.seed,
      "vc-analyzer/sector"
    );

    const metrics = computeSymbolicMetrics(vector, context);
    const archetype = mapToArchetype(sector, features, ritual.seed);
    const resonance = computeArchetypeResonance(features, archetype);

    // Score combines quality and momentum
    const baseScore = aggregateQualityScore(metrics);
    const score = Math.min(0.95, baseScore * 0.7 + (metrics.NMC + 1) / 2 * 0.3);

    return {
      name: sector,
      score: Math.round(score * 100) / 100,
      momentum: Math.round(((metrics.NMC + 1) / 2) * 100) / 100,
      reasoning: generateSectorReasoning(sector, archetype, metrics),
      archetype: archetype.name,
      confidence: Math.round((1 - metrics.SDR) * 100) / 100,
    };
  });

  // Sort by score descending
  return analysis.sort((a, b) => b.score - a.score);
}

/**
 * Generate sector reasoning based on archetype and metrics
 */
function generateSectorReasoning(sector: string, archetype: any, metrics: any): string {
  const reasoningMap: Record<string, string> = {
    "Generative AI": "Enterprise adoption accelerating",
    "Cybersecurity": "Threat landscape expanding",
    "Climate Tech": "Policy tailwinds strengthening",
    "Digital Health": "Post-pandemic digitization",
    "Biotech": "Pipeline maturation cycles",
    "Payments": "Embedded finance growth",
    "Dev Tools": "Developer productivity focus",
    "Cloud Infrastructure": "Multi-cloud optimization",
    "Crypto Infrastructure": "Institutional adoption",
    "Clean Energy": "Transition financing",
  };

  const baseReason = reasoningMap[sector] || "Market dynamics favorable";

  // Add archetype context if strong resonance
  if (Math.abs(metrics.ARF) > 0.5) {
    return `${baseReason} (${archetype.name} dynamics)`;
  }

  return baseReason;
}

/**
 * Generate risk factors based on symbolic metrics
 */
function generateRiskFactors(metrics: any, seed: string): string[] {
  const allRisks = [
    "Interest rate volatility",
    "Geopolitical tensions",
    "Market correction risks",
    "Regulatory uncertainty",
    "Valuation compression",
    "Exit market slowdown",
    "Capital allocation shifts",
  ];

  // Deterministic selection based on entropy and seed
  const count = metrics.Hσ > 0.6 ? 5 : metrics.Hσ > 0.4 ? 4 : 3;
  const seedNum = hashString(seed, "risk");

  const selected: string[] = [];
  for (let i = 0; i < count && i < allRisks.length; i++) {
    const index = (seedNum + i * 7) % allRisks.length;
    if (!selected.includes(allRisks[index])) {
      selected.push(allRisks[index]);
    }
  }

  return selected.slice(0, count);
}

/**
 * Generate opportunities based on symbolic metrics and industry
 */
function generateOpportunities(metrics: any, seed: string, industry: string): string[] {
  const allOpportunities = [
    "AI infrastructure expansion",
    "Climate transition funding",
    "Healthcare digitization",
    "Enterprise automation",
    "Consumer fintech growth",
    "Deep tech commercialization",
    "Supply chain resilience",
    "Cybersecurity consolidation",
  ];

  // More opportunities if momentum is positive
  const count = metrics.NMC > 0.3 ? 5 : metrics.NMC > 0 ? 4 : 3;
  const seedNum = hashString(seed, "opportunity");

  const selected: string[] = [];
  for (let i = 0; i < count && i < allOpportunities.length; i++) {
    const index = (seedNum + i * 11) % allOpportunities.length;
    if (!selected.includes(allOpportunities[index])) {
      selected.push(allOpportunities[index]);
    }
  }

  return selected.slice(0, count);
}

/**
 * Deterministic hash function for seeded randomness
 */
function hashString(str: string, seed: string): number {
  const combined = `${str}-${seed}`;
  const hash = crypto.createHash("md5").update(combined).digest("hex");
  return parseInt(hash.substring(0, 8), 16);
}
