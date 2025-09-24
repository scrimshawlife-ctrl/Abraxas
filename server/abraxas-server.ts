import express from "express";
import http from "http";
import passport from "passport";
import session from "express-session";
import { Strategy as GoogleStrategy } from "passport-google-oauth20";
import Database from "better-sqlite3";
import { WebSocketServer } from "ws";
import { v4 as uuidv4 } from "uuid";
import crypto from "crypto";

// Initialize database with proper path
const db = new Database("./abraxas.db");

// Database schema
db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    picture TEXT,
    created_at INTEGER NOT NULL
  );
  CREATE TABLE IF NOT EXISTS ritual_runs (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    date TEXT NOT NULL,
    seed TEXT NOT NULL,
    runes_json TEXT NOT NULL,
    results_json TEXT NOT NULL,
    created_at INTEGER NOT NULL
  );
  CREATE TABLE IF NOT EXISTS sigils (
    id TEXT PRIMARY KEY,
    owner_id TEXT REFERENCES users(id),
    core TEXT NOT NULL,
    seed TEXT NOT NULL,
    method TEXT NOT NULL,
    created_at INTEGER NOT NULL
  );
`);

// Mystical rune system
const RUNES = [
  { id: "aether", name: "Aether", color: "#FFD166", meaning: "cosmic flow" },
  { id: "tide", name: "Tide", color: "#4CC9F0", meaning: "market cycles" },
  { id: "ward", name: "Ward", color: "#F87171", meaning: "protection" },
  { id: "glyph", name: "Glyph", color: "#C6F6D5", meaning: "hidden knowledge" },
  { id: "flux", name: "Flux", color: "#A78BFA", meaning: "transformation" },
  { id: "nexus", name: "Nexus", color: "#FDE68A", meaning: "connection" }
];

function getTodayRunes() {
  const today = new Date().toISOString().slice(0, 10);
  const seed = hashString(today);
  const count = 2 + (seed % 3);
  
  const selected: typeof RUNES = [];
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

function runRitual() {
  const date = new Date().toISOString().slice(0, 10);
  const seed = Date.now() + Math.floor(Math.random() * 100000);
  const runes = getTodayRunes();
  
  return { date, seed, runes };
}

function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash);
}

// Trading logic
function scoreWatchlists(watchlists: any, ritual: any) {
  const { equities = [], fx = [] } = watchlists;
  
  const results = {
    equities: { conservative: [] as any[], risky: [] as any[] },
    fx: { conservative: [] as any[], risky: [] as any[] }
  };

  equities.forEach((ticker: string, idx: number) => {
    const score = generateScore(ticker, ritual.seed, idx);
    const edge = (score.raw - 0.5) * 0.3;
    const confidence = 0.4 + Math.abs(score.raw - 0.5) * 1.2;
    
    const prediction = {
      ticker,
      edge: Number(edge.toFixed(3)),
      confidence: Number(confidence.toFixed(2)),
      sector: getSector(ticker),
      rationale: generateRationale(ticker, ritual.runes)
    };
    
    if (Math.abs(edge) > 0.08) {
      results.equities.risky.push(prediction);
    } else if (confidence > 0.6) {
      results.equities.conservative.push(prediction);
    }
  });

  fx.forEach((pair: string, idx: number) => {
    const score = generateScore(pair, ritual.seed, idx + 100);
    const edge = (score.raw - 0.5) * 0.08;
    const confidence = 0.5 + Math.abs(score.raw - 0.5) * 0.8;
    
    const prediction = {
      pair,
      edge: Number(edge.toFixed(3)),
      confidence: Number(confidence.toFixed(2)),
      rationale: generateFXRationale(pair, ritual.runes)
    };
    
    if (Math.abs(edge) > 0.025) {
      results.fx.risky.push(prediction);
    } else if (confidence > 0.65) {
      results.fx.conservative.push(prediction);
    }
  });

  return results;
}

function generateScore(symbol: string, seed: number, offset: number) {
  const combined = hashString(symbol + seed + offset);
  const factor1 = (combined % 7) / 10;
  const factor2 = ((combined >> 8) % 5) / 20;
  const factor3 = ((combined >> 16) % 3) / 30;
  const raw = (factor1 + factor2 + factor3 + 0.3) % 1.0;
  
  return { raw, factors: [`α: ${factor1.toFixed(2)}`, `β: ${factor2.toFixed(2)}`, `γ: ${factor3.toFixed(2)}`] };
}

function getSector(ticker: string): string {
  const sectors: { [key: string]: string } = {
    'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology', 'NVDA': 'Technology',
    'TSLA': 'Automotive', 'AMZN': 'Consumer', 'META': 'Technology', 'NFLX': 'Media'
  };
  return sectors[ticker] || 'Unknown';
}

function generateRationale(ticker: string, runes: any[]): string[] {
  const rationales = [
    "Contract scope ↑", "Night-lights ↑", "IPR pressure easing", "Planetary align",
    "Supply chain flux", "Regulatory winds", "Market sentiment", "Technical patterns"
  ];
  
  const count = 1 + (hashString(ticker) % 3);
  const selected: string[] = [];
  
  for (let i = 0; i < count; i++) {
    const idx = (hashString(ticker + i) + runes.length) % rationales.length;
    if (!selected.includes(rationales[idx])) {
      selected.push(rationales[idx]);
    }
  }
  
  return selected;
}

function generateFXRationale(pair: string, runes: any[]): string[] {
  const rationales = [
    "Funding stress ↓", "Trade flow ↑", "Central bank signals", "Risk sentiment",
    "Carry trade unwind", "Liquidity conditions", "Economic data", "Geopolitical events"
  ];
  
  const count = 1 + (hashString(pair) % 2);
  const selected: string[] = [];
  
  for (let i = 0; i < count; i++) {
    const idx = (hashString(pair + i) + runes.length) % rationales.length;
    if (!selected.includes(rationales[idx])) {
      selected.push(rationales[idx]);
    }
  }
  
  return selected;
}

// Metrics system
class MetricsTracker {
  sources = new Set<string>();
  signals = new Set<string>();
  predictions: any[] = [];

  addSource(fingerprint: string) { this.sources.add(fingerprint); }
  addSignal(fingerprint: string) { this.signals.add(fingerprint); }
  addPrediction(pred: any) { this.predictions.push({ ...pred, timestamp: Date.now() }); }

  snapshot() {
    const now = Date.now();
    const day = 24 * 60 * 60 * 1000;
    
    return {
      day: {
        uniqueSources: Math.min(15, this.sources.size),
        uniqueSignals: Math.min(40, this.signals.size),
        fxShiftAbs: Math.random() * 5,
        accuracy: { acc: 0.65 + Math.random() * 0.15, n: Math.floor(Math.random() * 20) + 5 }
      },
      week: {
        uniqueSources: Math.min(70, this.sources.size * 2),
        uniqueSignals: Math.min(150, this.signals.size * 2),
        fxShiftAbs: Math.random() * 25,
        accuracy: { acc: 0.68 + Math.random() * 0.12, n: Math.floor(Math.random() * 90) + 20 }
      },
      month: {
        uniqueSources: Math.min(250, this.sources.size * 5),
        uniqueSignals: Math.min(600, this.signals.size * 5),
        fxShiftAbs: Math.random() * 80,
        accuracy: { acc: 0.71 + Math.random() * 0.10, n: Math.floor(Math.random() * 300) + 50 }
      },
      lifetime: {
        uniqueSources: Math.max(500, this.sources.size * 10),
        uniqueSignals: Math.max(1000, this.signals.size * 10),
        fxShiftAbs: Math.random() * 500,
        accuracy: { acc: 0.69 + Math.random() * 0.12, n: Math.floor(Math.random() * 2000) + 100 }
      }
    };
  }
}

const metrics = new MetricsTracker();

export function setupAbraxasRoutes(app: express.Application, server: http.Server) {
  // Broadcast functionality (disabled for now to avoid Vite WebSocket conflicts)
  const broadcast = (type: string, data: any) => {
    // console.log(`Broadcasting ${type}:`, data);
    // WebSocket functionality disabled to avoid conflicts with Vite
  };

  // Health endpoints
  app.get("/healthz", (req, res) => res.json({ ok: true, ts: Date.now() }));
  app.get("/readyz", (req, res) => {
    try {
      db.prepare("SELECT 1").get();
      res.json({ ready: true, ts: Date.now() });
    } catch (e) {
      res.status(503).json({ ready: false, error: String(e) });
    }
  });

  // Ritual endpoints
  app.get("/api/runes", (req, res) => res.json(getTodayRunes()));
  app.get("/api/stats", (req, res) => res.json(metrics.snapshot()));
  app.get("/api/daily-oracle", (req, res) => {
    const s = metrics.snapshot();
    const conf = s.lifetime.accuracy.acc || 0.5;
    const tone = conf > 0.6 ? "ascending" : conf > 0.52 ? "tempered" : "probing";
    const b = Buffer.from(JSON.stringify({ day: new Date().toISOString().slice(0, 10), tone })).toString("base64").replace(/=/g, "");
    const glyph = b.match(/.{1,8}/g)?.join("·") || b;
    res.json({ 
      ciphergram: `⟟Σ ${glyph} Σ⟟`, 
      note: `Litany (${tone}): "Vectors converge; witnesses veiled."` 
    });
  });

  app.post("/api/ritual", async (req, res) => {
    const { equities = [], fx = [] } = req.body || {};
    const ritual = runRitual();
    const results = scoreWatchlists({ equities, fx }, ritual);

    // Add mock metrics
    ["federal_register", "sam.gov", "uspto"].forEach((s, i) => 
      metrics.addSource(crypto.createHash("md5").update(s + i).digest("hex").substring(0, 12))
    );
    ["rule:dfars", "mod:sam", "ipr:ptab"].forEach((s, i) => 
      metrics.addSignal(crypto.createHash("md5").update(s + i).digest("hex").substring(0, 12))
    );

    broadcast("results", { results });

    // Store ritual run
    const runId = uuidv4();
    try {
      db.prepare(`
        INSERT INTO ritual_runs (id, user_id, date, seed, runes_json, results_json, created_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
      `).run(runId, "mock-user", ritual.date, String(ritual.seed), 
        JSON.stringify(ritual.runes), JSON.stringify(results), Date.now());
    } catch (e) {
      console.log("DB insert failed (expected if no auth):", e);
    }

    const sealed = {
      hash: crypto.createHash("sha256").update(JSON.stringify({ ritual, results })).digest("hex").substring(0, 16),
      timestamp: Date.now(),
      signature: `⟟Σ${crypto.randomBytes(4).toString("hex")}Σ⟟`
    };

    res.json({ 
      ritual, 
      results, 
      sealed, 
      disclaimer: "Abraxas persona is fictional; sources & methods sealed. Not financial advice." 
    });
  });

  // Social trends mock
  app.get("/api/social-trends", (req, res) => {
    const trends = [
      {
        platform: "Twitter/X",
        trends: [
          { keyword: "AI", momentum: 0.85, sentiment: 0.72, volume: 125000 },
          { keyword: "blockchain", momentum: 0.43, sentiment: 0.58, volume: 89000 }
        ],
        timestamp: Date.now()
      }
    ];
    res.json(trends);
  });

  app.post("/api/social-trends/scan", async (req, res) => {
    const trends = [
      {
        platform: "Twitter/X",
        trends: [
          { keyword: "AI", momentum: Math.random(), sentiment: Math.random(), volume: Math.floor(Math.random() * 200000) },
          { keyword: "DeFi", momentum: Math.random(), sentiment: Math.random(), volume: Math.floor(Math.random() * 100000) }
        ],
        timestamp: Date.now()
      }
    ];
    broadcast("social_trends", trends);
    res.json(trends);
  });

  // VC Oracle mock
  app.post("/api/vc/analyze", async (req, res) => {
    const { industry = "Technology", region = "US", horizonDays = 90 } = req.body || {};
    
    const analysis = {
      industry,
      region,
      horizon: horizonDays,
      forecast: {
        dealVolume: {
          prediction: 800 + Math.floor(Math.random() * 400),
          confidence: 0.6 + Math.random() * 0.3,
          factors: ["Market sentiment", "Historical trends", "Economic indicators"]
        },
        hotSectors: [
          { name: "Generative AI", score: 0.9 + Math.random() * 0.1, reasoning: "Enterprise adoption accelerating" },
          { name: "Climate Tech", score: 0.7 + Math.random() * 0.2, reasoning: "Policy tailwinds strengthening" }
        ],
        riskFactors: ["Interest rate volatility", "Geopolitical tensions"],
        opportunities: ["AI infrastructure", "Climate transition funding"]
      },
      timestamp: Date.now()
    };
    
    res.json(analysis);
  });

  console.log("🔮 Abraxas mystical endpoints initialized");
}