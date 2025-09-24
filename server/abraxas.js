// Core Abraxas trading logic
export function scoreWatchlists(watchlists, ritual) {
  const { equities = [], fx = [] } = watchlists;
  const { seed, runes } = ritual;
  
  const results = {
    equities: { conservative: [], risky: [] },
    fx: { conservative: [], risky: [] }
  };

  // Score equities
  equities.forEach((ticker, idx) => {
    const score = generateScore(ticker, seed, idx);
    const edge = (score.raw - 0.5) * 0.3; // -0.15 to +0.15
    const confidence = 0.4 + Math.abs(score.raw - 0.5) * 1.2; // 0.4 to 1.0
    
    const prediction = {
      ticker,
      edge: Number(edge.toFixed(3)),
      confidence: Number(confidence.toFixed(2)),
      sector: getSector(ticker),
      rationale: generateRationale(ticker, runes, score.factors)
    };
    
    if (Math.abs(edge) > 0.08) {
      results.equities.risky.push(prediction);
    } else if (confidence > 0.6) {
      results.equities.conservative.push(prediction);
    }
  });

  // Score FX pairs
  fx.forEach((pair, idx) => {
    const score = generateScore(pair, seed, idx + 100);
    const edge = (score.raw - 0.5) * 0.08; // -0.04 to +0.04
    const confidence = 0.5 + Math.abs(score.raw - 0.5) * 0.8; // 0.5 to 0.9
    
    const prediction = {
      pair,
      edge: Number(edge.toFixed(3)),
      confidence: Number(confidence.toFixed(2)),
      rationale: generateFXRationale(pair, runes, score.factors)
    };
    
    if (Math.abs(edge) > 0.025) {
      results.fx.risky.push(prediction);
    } else if (confidence > 0.65) {
      results.fx.conservative.push(prediction);
    }
  });

  return results;
}

function generateScore(symbol, seed, offset) {
  const combined = hashString(symbol + seed + offset);
  const factors = [];
  
  // Generate mystical factors
  const factor1 = (combined % 7) / 10;
  const factor2 = ((combined >> 8) % 5) / 20;
  const factor3 = ((combined >> 16) % 3) / 30;
  
  factors.push(`Factor α: ${factor1.toFixed(2)}`);
  factors.push(`Factor β: ${factor2.toFixed(2)}`);
  factors.push(`Factor γ: ${factor3.toFixed(2)}`);
  
  const raw = (factor1 + factor2 + factor3 + 0.3) % 1.0;
  
  return { raw, factors };
}

function getSector(ticker) {
  const sectors = {
    'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology', 'NVDA': 'Technology',
    'TSLA': 'Automotive', 'AMZN': 'Consumer', 'META': 'Technology', 'NFLX': 'Media'
  };
  return sectors[ticker] || 'Unknown';
}

function generateRationale(ticker, runes, factors) {
  const rationales = [
    "Contract scope ↑", "Night-lights ↑", "IPR pressure easing", "Planetary align",
    "Supply chain flux", "Regulatory winds", "Market sentiment", "Technical patterns"
  ];
  
  const count = 1 + (hashString(ticker) % 3);
  const selected = [];
  
  for (let i = 0; i < count; i++) {
    const idx = (hashString(ticker + i) + runes.length) % rationales.length;
    if (!selected.includes(rationales[idx])) {
      selected.push(rationales[idx]);
    }
  }
  
  return selected;
}

function generateFXRationale(pair, runes, factors) {
  const rationales = [
    "Funding stress ↓", "Trade flow ↑", "Central bank signals", "Risk sentiment",
    "Carry trade unwind", "Liquidity conditions", "Economic data", "Geopolitical events"
  ];
  
  const count = 1 + (hashString(pair) % 2);
  const selected = [];
  
  for (let i = 0; i < count; i++) {
    const idx = (hashString(pair + i) + runes.length) % rationales.length;
    if (!selected.includes(rationales[idx])) {
      selected.push(rationales[idx]);
    }
  }
  
  return selected;
}

function hashString(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash);
}