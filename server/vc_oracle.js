// VC Oracle (Athena) - Venture capital analysis system
export const VC_PERSONA = {
  name: "Athena",
  role: "Venture Capital Oracle",
  capabilities: ["market_analysis", "sector_prediction", "deal_flow_forecasting"],
  confidence_threshold: 0.6
};

export async function analyzeVC({ industry, region, horizonDays }) {
  // Mock VC analysis - in real system would integrate with CB Insights, PitchBook, etc.
  const sectors = {
    "Technology": ["Generative AI", "Cybersecurity", "Dev Tools"],
    "Healthcare": ["Digital Health", "Biotech", "MedTech"],
    "Fintech": ["Payments", "Lending", "Crypto Infrastructure"],
    "Climate": ["Clean Energy", "Carbon Tech", "Sustainable Materials"]
  };

  const riskFactors = [
    "Interest rate volatility",
    "Geopolitical tensions",
    "Market correction risks",
    "Regulatory uncertainty",
    "Valuation compression"
  ];

  const opportunities = [
    "AI infrastructure expansion",
    "Climate transition funding",
    "Healthcare digitization",
    "Enterprise automation",
    "Consumer fintech growth"
  ];

  // Generate prediction based on inputs
  const baseDealVolume = {
    "Technology": 1200,
    "Healthcare": 800,
    "Fintech": 600,
    "Climate": 400
  };

  const regionalMultiplier = {
    "US": 1.0,
    "EU": 0.6,
    "APAC": 0.8,
    "Global": 1.4
  };

  const prediction = Math.floor(
    baseDealVolume[industry] * regionalMultiplier[region] * (0.8 + Math.random() * 0.4)
  );

  const confidence = 0.6 + Math.random() * 0.3; // 60-90% confidence

  const hotSectors = sectors[industry] || ["General Tech"];
  const sectorAnalysis = hotSectors.map(sector => ({
    name: sector,
    score: Number((0.5 + Math.random() * 0.4).toFixed(2)),
    reasoning: generateSectorReasoning(sector)
  })).sort((a, b) => b.score - a.score);

  return {
    industry,
    region,
    horizon: horizonDays,
    forecast: {
      dealVolume: {
        prediction,
        confidence: Number(confidence.toFixed(2)),
        factors: [
          "Market sentiment analysis",
          "Historical trend correlation",
          "Economic indicator synthesis"
        ]
      },
      hotSectors: sectorAnalysis,
      riskFactors: riskFactors.slice(0, 3 + Math.floor(Math.random() * 2)),
      opportunities: opportunities.slice(0, 3 + Math.floor(Math.random() * 2))
    },
    timestamp: Date.now()
  };
}

function generateSectorReasoning(sector) {
  const reasonings = {
    "Generative AI": "Enterprise adoption accelerating",
    "Cybersecurity": "Threat landscape expanding",
    "Climate Tech": "Policy tailwinds strengthening",
    "Digital Health": "Post-pandemic digitization",
    "Biotech": "Pipeline maturation cycles",
    "Payments": "Embedded finance growth",
    "Dev Tools": "Developer productivity focus"
  };
  
  return reasonings[sector] || "Market dynamics favorable";
}