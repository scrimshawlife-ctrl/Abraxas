// Indicator Cache Module - Extracted to avoid circular imports
// Handles efficient caching with TTL for indicator evaluations

import { storage } from "./storage";

// Get cached value for indicator with TTL (Time To Live) 
export async function getCachedIndicatorValue(ikey: string, subject: string, day: string, seed: string, ttlMinutes: number = 60): Promise<number | null> {
  // Use storage interface with TTL parameter and day/seed scoping
  return await storage.getCachedIndicatorValue(ikey, subject, day, seed, ttlMinutes);
}

// Cache indicator value (only if not already cached recently)
export async function setCachedIndicatorValue(ikey: string, subject: string, day: string, seed: string, value: number, ttlMinutes: number = 60): Promise<number> {
  // Check if we already have a recent cache entry through storage
  const existingValue = await storage.getCachedIndicatorValue(ikey, subject, day, seed, ttlMinutes);
  if (existingValue !== null) {
    return existingValue; // Return existing cached value
  }
  
  // Insert new cache entry through storage interface
  const cached = await storage.cacheIndicatorValue({
    ikey,
    subject,
    day,
    seed,
    value
  });
  
  return cached.value;
}