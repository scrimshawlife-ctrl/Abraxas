// Market Analysis Engine for Dynamic Watchlists
// Identifies growth opportunities and short candidates based on mystical market indicators

import { evalDynamicIndicators } from "./indicators";
import { storage } from "./storage";
import { InsertWatchlistItem } from "@shared/schema";

// Hash function for deterministic random values (matching abraxas.ts pattern)
function hseed(input: string): number {
  let hash = 0;
  for (let i = 0; i < input.length; i++) {
    const char = input.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return Math.abs(hash);
}

// Generate features for equity analysis
function generateEquityFeatures(ticker: string, seed: string): Record<string, number> {
  const r = (x: string) => (((hseed(ticker + x + seed) % 200) - 100) / 50);
  
  return {
    // Technical indicators
    momentum_strength: r("momentum") / 2,
    volatility_score: Math.abs(r("volatility")) / 2,
    volume_surge: Math.max(0, r("volume")),
    price_momentum: r("price") / 3,
    
    // Growth indicators  
    earnings_growth: r("earnings") / 2,
    revenue_growth: r("revenue") / 2,
    market_cap_momentum: r("mcap") / 3,
    
    // Risk factors
    debt_ratio: Math.abs(r("debt")) / 4,
    beta_risk: Math.abs(r("beta")) / 3,
    liquidity_risk: Math.abs(r("liquidity")) / 4,
    
    // Sector momentum
    sector_strength: r("sector") / 2,
    relative_strength: r("relative") / 2
  };
}

// Generate features for FX pair analysis
function generateFxFeatures(pair: string, seed: string): Record<string, number> {
  const r = (x: string) => (((hseed(pair + x + seed) % 200) - 100) / 50);
  
  return {
    // Currency strength indicators
    base_strength: r("base") / 2,
    quote_strength: r("quote") / 2,
    carry_trade_appeal: r("carry") / 3,
    
    // Economic indicators
    interest_rate_diff: r("rates") / 2,
    economic_momentum: r("economic") / 2,
    inflation_pressure: r("inflation") / 3,
    
    // Technical factors
    volatility_profile: Math.abs(r("vol")) / 2,
    trend_strength: r("trend") / 2,
    support_resistance: r("support") / 3,
    
    // Geopolitical factors
    political_stability: r("politics") / 4,
    trade_balance: r("trade") / 3
  };
}

// Analyze symbol for growth potential
export async function analyzeGrowthPotential(symbol: string, symbolType: "equity" | "fx"): Promise<{
  score: number;
  confidence: number;
  rationale: string;
  riskLevel: "low" | "medium" | "high";
  sector?: string;
  metadata: any;
}> {
  const seed = new Date().toISOString().slice(0, 10); // Use current date as seed
  
  // Get dynamic indicators for this symbol
  const indicators = await evalDynamicIndicators(symbol, { date: seed });
  
  // Generate base features
  const features = symbolType === "equity" 
    ? generateEquityFeatures(symbol, seed)
    : generateFxFeatures(symbol, seed);
  
  // Combine with mystical indicators
  const combinedFeatures = { ...features, ...indicators };
  
  // Growth-focused weights
  const growthWeights = {
    momentum_strength: 0.25,
    earnings_growth: 0.3,
    revenue_growth: 0.25,
    volume_surge: 0.15,
    sector_strength: 0.2,
    base_strength: 0.2, // FX
    economic_momentum: 0.25, // FX
    trend_strength: 0.2, // FX
  };
  
  // Calculate growth score
  let growthScore = 0;
  let totalWeight = 0;
  
  for (const [feature, weight] of Object.entries(growthWeights)) {
    if (combinedFeatures[feature] !== undefined) {
      growthScore += combinedFeatures[feature] * weight;
      totalWeight += weight;
    }
  }
  
  if (totalWeight > 0) {
    growthScore = growthScore / totalWeight;
  }
  
  // Normalize to 0-1 range
  growthScore = Math.max(0, Math.min(1, (growthScore + 1) / 2));
  
  // Calculate confidence based on feature consistency
  const featureValues = Object.values(combinedFeatures).filter(v => v !== undefined);
  const variance = featureValues.reduce((sum, v) => sum + Math.pow(v - growthScore, 2), 0) / featureValues.length;
  const confidence = Math.max(0.1, Math.min(1, 1 - variance));
  
  // Determine risk level
  const volatility = combinedFeatures.volatility_score || combinedFeatures.volatility_profile || 0;
  const riskLevel: "low" | "medium" | "high" = 
    Math.abs(volatility) < 0.3 ? "low" : 
    Math.abs(volatility) < 0.7 ? "medium" : "high";
  
  // Generate rationale
  const topFeatures = Object.entries(combinedFeatures)
    .sort(([,a], [,b]) => Math.abs(b) - Math.abs(a))
    .slice(0, 3)
    .map(([name, value]) => `${name}: ${value.toFixed(3)}`);
  
  const rationale = `Growth potential based on ${topFeatures.join(", ")}. ${
    symbolType === "equity" ? "Strong fundamentals" : "Favorable currency dynamics"
  } with ${confidence > 0.7 ? "high" : confidence > 0.4 ? "moderate" : "low"} confidence.`;
  
  // Determine sector for equities
  const sector = symbolType === "equity" ? guessEquitySector(symbol) : undefined;
  
  return {
    score: Number(growthScore.toFixed(4)),
    confidence: Number(confidence.toFixed(4)),
    rationale,
    riskLevel,
    sector,
    metadata: {
      features: combinedFeatures,
      analysisDate: seed,
      symbolType
    }
  };
}

// Analyze symbol for short opportunity
export async function analyzeShortPotential(symbol: string, symbolType: "equity" | "fx"): Promise<{
  score: number;
  confidence: number;
  rationale: string;
  riskLevel: "low" | "medium" | "high";
  sector?: string;
  metadata: any;
}> {
  const seed = new Date().toISOString().slice(0, 10);
  
  // Get dynamic indicators
  const indicators = await evalDynamicIndicators(symbol, { date: seed });
  
  // Generate base features
  const features = symbolType === "equity" 
    ? generateEquityFeatures(symbol, seed)
    : generateFxFeatures(symbol, seed);
    
  const combinedFeatures = { ...features, ...indicators };
  
  // Short-focused weights (opposite of growth)
  const shortWeights = {
    momentum_strength: -0.3, // Negative momentum is good for shorts
    earnings_growth: -0.35,   // Declining earnings
    debt_ratio: 0.25,         // High debt is bad
    beta_risk: 0.2,           // High beta for volatility
    volatility_score: 0.15,   // Volatility creates opportunities
    base_strength: -0.25,     // FX: weakness in base currency
    economic_momentum: -0.3,  // FX: economic decline
    political_stability: -0.2 // FX: instability
  };
  
  // Calculate short score
  let shortScore = 0;
  let totalWeight = 0;
  
  for (const [feature, weight] of Object.entries(shortWeights)) {
    if (combinedFeatures[feature] !== undefined) {
      shortScore += combinedFeatures[feature] * weight;
      totalWeight += Math.abs(weight);
    }
  }
  
  if (totalWeight > 0) {
    shortScore = shortScore / totalWeight;
  }
  
  // Normalize to 0-1 range (higher is better for shorting)
  shortScore = Math.max(0, Math.min(1, (shortScore + 1) / 2));
  
  // Calculate confidence
  const featureValues = Object.values(combinedFeatures).filter(v => v !== undefined);
  const variance = featureValues.reduce((sum, v) => sum + Math.pow(v, 2), 0) / featureValues.length;
  const confidence = Math.max(0.1, Math.min(1, variance * 2)); // Higher variance = more confident short signal
  
  // Risk level for shorting (higher volatility = higher risk)
  const volatility = combinedFeatures.volatility_score || combinedFeatures.volatility_profile || 0;
  const riskLevel: "low" | "medium" | "high" = 
    Math.abs(volatility) < 0.4 ? "low" : 
    Math.abs(volatility) < 0.8 ? "medium" : "high";
  
  // Generate rationale
  const negativeFeatures = Object.entries(combinedFeatures)
    .filter(([,value]) => value < -0.2)
    .sort(([,a], [,b]) => a - b) // Sort by most negative
    .slice(0, 3)
    .map(([name, value]) => `${name}: ${value.toFixed(3)}`);
    
  const rationale = `Short opportunity identified from ${negativeFeatures.length > 0 ? negativeFeatures.join(", ") : "negative momentum indicators"}. ${
    symbolType === "equity" ? "Weak fundamentals" : "Unfavorable currency outlook"
  } suggest downward pressure.`;
  
  const sector = symbolType === "equity" ? guessEquitySector(symbol) : undefined;
  
  return {
    score: Number(shortScore.toFixed(4)),
    confidence: Number(confidence.toFixed(4)),
    rationale,
    riskLevel,
    sector,
    metadata: {
      features: combinedFeatures,
      analysisDate: seed,
      symbolType
    }
  };
}

// Guess sector for equity symbols (simplified version)
function guessEquitySector(ticker: string): string {
  if (/(AAPL|MSFT|GOOGL|AMZN|META|TSLA|NVDA|CRM|ADBE|NFLX)/.test(ticker)) return "Technology";
  if (/(JPM|BAC|WFC|GS|MS|C|USB|PNC|TFC|COF)/.test(ticker)) return "Financials";
  if (/(JNJ|PFE|UNH|ABBV|BMY|MRK|GILD|AMGN|CVS|TMO)/.test(ticker)) return "Healthcare";
  if (/(XOM|CVX|COP|EOG|SLB|HAL|OXY|DVN|MPC|VLO)/.test(ticker)) return "Energy";
  if (/(AMZN|WMT|HD|TGT|COST|LOW|TJX|SBUX|MCD|NKE)/.test(ticker)) return "Consumer";
  if (/(CAT|MMM|GE|HON|BA|UNP|RTX|LMT|DE|EMR)/.test(ticker)) return "Industrials";
  return "Mixed";
}

// Analyze a pool of symbols and return top candidates
export async function analyzeSymbolPool(symbols: { symbol: string; type: "equity" | "fx" }[], analysisType: "growth" | "short", limit: number = 10): Promise<{
  symbol: string;
  symbolType: "equity" | "fx";
  analysisScore: number;
  confidence: number;
  growthPotential?: number;
  shortPotential?: number;
  riskLevel: "low" | "medium" | "high";
  sector?: string;
  rationale: string;
  metadata: any;
}[]> {
  const results = [];
  
  for (const { symbol, type } of symbols) {
    try {
      const analysis = analysisType === "growth" 
        ? await analyzeGrowthPotential(symbol, type)
        : await analyzeShortPotential(symbol, type);
      
      results.push({
        symbol,
        symbolType: type,
        analysisScore: analysisType === "growth" ? analysis.score : -analysis.score, // Negative for short positions
        confidence: analysis.confidence,
        growthPotential: analysisType === "growth" ? analysis.score : undefined,
        shortPotential: analysisType === "short" ? analysis.score : undefined,
        riskLevel: analysis.riskLevel,
        sector: analysis.sector,
        rationale: analysis.rationale,
        metadata: analysis.metadata
      });
    } catch (error) {
      console.warn(`Failed to analyze ${symbol}:`, error);
    }
  }
  
  // Sort by score (descending) and return top candidates
  return results
    .sort((a, b) => Math.abs(b.analysisScore) - Math.abs(a.analysisScore))
    .slice(0, limit);
}

// Update watchlist with fresh analysis
export async function updateWatchlistAnalysis(watchlistId: string): Promise<void> {
  const items = await storage.getWatchlistItems(watchlistId);
  const watchlist = await storage.getWatchlistById(watchlistId);
  
  if (!watchlist) {
    throw new Error("Watchlist not found");
  }
  
  const analysisType = watchlist.type === "growth" ? "growth" : "short";
  
  for (const item of items) {
    try {
      const analysis = analysisType === "growth"
        ? await analyzeGrowthPotential(item.symbol, item.symbolType as "equity" | "fx")
        : await analyzeShortPotential(item.symbol, item.symbolType as "equity" | "fx");
      
      await storage.updateWatchlistItem(item.id, {
        analysisScore: analysisType === "growth" ? analysis.score : -analysis.score,
        confidence: analysis.confidence,
        growthPotential: analysisType === "growth" ? analysis.score : undefined,
        shortPotential: analysisType === "short" ? analysis.score : undefined,
        riskLevel: analysis.riskLevel,
        sector: analysis.sector,
        rationale: analysis.rationale,
        metadata: analysis.metadata
      });
    } catch (error) {
      console.warn(`Failed to update analysis for ${item.symbol}:`, error);
    }
  }
  
  // Update watchlist last analyzed timestamp
  await storage.updateWatchlist(watchlistId, {
    lastAnalyzed: new Date()
  });
}