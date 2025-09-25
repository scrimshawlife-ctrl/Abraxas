import { v4 as uuidv4 } from "uuid";
import { db } from "./db";
import { indicators, indicatorCache, tradingConfigs } from "@shared/schema";
import { evalIndicator } from "./indicators-secret";
import { eq, sql, desc } from "drizzle-orm";

// Rune factory — generate a simple occult-tinged SVG path for a new indicator
function runePathFromKey(ikey: string): string {
  // aesthetic: concentric diamond + curl; deterministic from key
  const seed = ikey.split(":").pop() || "x";
  const hash = Array.from(seed).reduce((a, c) => (a * 33 + c.charCodeAt(0)) >>> 0, 7);
  const t = (p: number) => (hash % p) / p;
  const r1 = 10 + (t(97) * 20);
  const r2 = 28 + (t(89) * 20);
  const cx = 50 + (t(83) * 6 - 3);
  const cy = 50 + (t(79) * 6 - 3);
  const d1 = `M ${cx} ${cy - r2} L ${cx + r2} ${cy} L ${cx} ${cy + r2} L ${cx - r2} ${cy} Z`;
  const d2 = `M ${cx} ${cy - r1} L ${cx + r1} ${cy} L ${cx} ${cy + r1} L ${cx - r1} ${cy} Z`;
  const curl = `M ${cx - 8} ${cy + 8} C ${cx - 18} ${cy - 8}, ${cx + 18} ${cy - 8}, ${cx + 8} ${cy + 8}`;
  return `${d1} ${d2} ${curl}`;
}

// Register a new indicator (adds weight key 'ind:<slug>')
export async function registerIndicator({ name, slug }: { name: string; slug: string }) {
  const ikey = `ind:${slug.toLowerCase().replace(/[^a-z0-9-]/g, "-")}`;
  
  // Check if already exists
  const existing = await db.select().from(indicators).where(eq(indicators.ikey, ikey)).limit(1);
  if (existing.length > 0) return existing[0];
  
  const rec = {
    ikey,
    name,
    svgPath: runePathFromKey(ikey),
  };
  
  const result = await db.insert(indicators).values(rec).returning();
  
  // Ensure config weight exists (default small positive tilt)
  try {
    // Get or create default config
    const configRows = await db.select().from(tradingConfigs).where(eq(tradingConfigs.name, "default")).limit(1);
    
    if (configRows.length > 0) {
      const config = configRows[0];
      const currentWeights = config.weights as Record<string, number>;
      
      if (typeof currentWeights[ikey] !== "number") {
        currentWeights[ikey] = 0.2;
        await db.update(tradingConfigs)
          .set({ 
            weights: currentWeights,
            updatedAt: new Date()
          })
          .where(eq(tradingConfigs.id, config.id));
      }
    }
  } catch (error) {
    console.warn("Could not update default config weights:", error);
  }
  
  return result[0];
}

// Discover routine: occasionally mint 0–2 fresh, esoteric indicators
export function discoverIndicators() {
  const day = new Date().toISOString().slice(0, 10);
  const salt = day.replace(/-/g, "");
  const may = (n: number) => ((parseInt(salt.slice(-2), 10) + n) % 3) === 0; // pseudo randomness
  const minted = [];
  
  if (may(1)) minted.push(registerIndicator({ name: "Chaldean Phase Drift", slug: `chaldean-phase-${salt.slice(-3)}` }));
  if (may(2)) minted.push(registerIndicator({ name: "Heron's Market Spiral", slug: `heron-spiral-${salt.slice(0, 3)}` }));
  
  return Promise.all(minted.filter(Boolean));
}

// Evaluate all dynamic indicator values for a subject (ticker/fx pair)
export async function evalDynamicIndicators(subject: string, ctx?: { date?: string; seed?: string; aux?: any }) {
  const out: Record<string, number> = {};
  const rows = await db.select().from(indicators).orderBy(desc(indicators.createdAt));
  
  for (const ind of rows) {
    try {
      const v = evalIndicator(ind.ikey, subject, ctx);
      out[ind.ikey] = v;
      
      // tiny cache (optional)
      try {
        await db.insert(indicatorCache).values({
          ikey: ind.ikey,
          subject,
          value: v,
        });
      } catch (cacheError) {
        // Cache insert failed, continue
        console.warn("Cache insert failed:", cacheError);
      }
    } catch (evalError) {
      console.warn("Indicator evaluation failed:", evalError);
    }
  }
  
  return out;
}

// Get all indicators
export async function getAllIndicators() {
  return await db.select().from(indicators).orderBy(desc(indicators.createdAt));
}

// Get indicator by key
export async function getIndicatorByKey(ikey: string) {
  const result = await db.select().from(indicators).where(eq(indicators.ikey, ikey)).limit(1);
  return result.length > 0 ? result[0] : null;
}

// Get cached value for indicator
export async function getCachedValue(ikey: string, subject: string) {
  const result = await db.select({ value: indicatorCache.value })
    .from(indicatorCache)
    .where(sql`${indicatorCache.ikey} = ${ikey} AND ${indicatorCache.subject} = ${subject}`)
    .orderBy(desc(indicatorCache.createdAt))
    .limit(1);
  
  return result.length > 0 ? result[0].value : null;
}