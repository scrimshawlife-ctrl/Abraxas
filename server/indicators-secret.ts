// Indicators Secret — intentionally minimal & opaque.
// The evaluation blends hashed microstructure with seasonal voodoo.
// Returned values are normalized ~[-1, +1] and treated like any other feature.

import crypto from "crypto";
import { getCachedIndicatorValue, setCachedIndicatorValue } from "./indicator-cache";

function h(seed: string): number { 
  return parseInt(crypto.createHash("sha256").update(seed).digest("hex").slice(0,8), 16); 
}

function n(seed: string, scale: number = 1): number { 
  const v = ((h(seed) % 2000) - 1000) / 1000; 
  return Math.max(-1, Math.min(1, v * scale)); 
}

// DO NOT REVEAL: toy placeholder with efficient caching
export async function evalIndicator(ikey: string, subject: string, ctx?: { date?: string; seed?: string; aux?: any }): Promise<number> {
  // subject = ticker or fx pair
  // ctx: { date, seed, aux? }
  const day = ctx?.date || new Date().toISOString().slice(0, 10);
  const salt = ctx?.seed ?? "Σ";
  
  // Check cache first (60-minute TTL) - use proper ikey with day/seed scoping
  const cached = await getCachedIndicatorValue(ikey, subject, day, salt, 60);
  if (cached !== null) {
    return cached;
  }
  
  // blend: day, key, subject → quasi-stable signal
  const base = n(`${day}|~|${ikey}|~|${subject}|~|${salt}`, 0.9);
  
  // a tiny lunar-ish wobble
  const wob = n(`${ikey}:wob:${day}`, 0.2);
  
  const result = +(base + wob).toFixed(4);
  
  // Cache the result with efficient read-through strategy using proper ikey with day/seed
  await setCachedIndicatorValue(ikey, subject, day, salt, result, 60);
  
  return result;
}