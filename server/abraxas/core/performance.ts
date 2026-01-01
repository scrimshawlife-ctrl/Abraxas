/**
 * ABX-Core v1.2 - Performance Optimization Layer
 * SEED Framework Compliant
 *
 * @module abraxas/core/performance
 * @entropy_class low
 * @deterministic true
 * @capabilities { read: ["cache"], write: ["cache"], network: false }
 *
 * Provides caching and optimization utilities for the symbolic kernel
 */

// ═══════════════════════════════════════════════════════════════════════════
// LRU Cache Implementation
// ═══════════════════════════════════════════════════════════════════════════

export class LRUCache<K, V> {
  private cache: Map<string, { value: V; timestamp: number }>;
  private readonly maxSize: number;
  private readonly ttl: number; // Time to live in milliseconds

  constructor(maxSize: number = 1000, ttl: number = 3600000) {
    this.cache = new Map();
    this.maxSize = maxSize;
    this.ttl = ttl;
  }

  get(key: K): V | undefined {
    const keyStr = this.serialize(key);
    const entry = this.cache.get(keyStr);

    if (!entry) return undefined;

    // Check TTL
    if (Date.now() - entry.timestamp > this.ttl) {
      this.cache.delete(keyStr);
      return undefined;
    }

    // Move to end (most recently used)
    this.cache.delete(keyStr);
    this.cache.set(keyStr, entry);

    return entry.value;
  }

  set(key: K, value: V): void {
    const keyStr = this.serialize(key);

    // Remove if exists
    this.cache.delete(keyStr);

    // Evict oldest if at capacity
    if (this.cache.size >= this.maxSize) {
      const firstKey = Array.from(this.cache.keys())[0];
      this.cache.delete(firstKey);
    }

    this.cache.set(keyStr, { value, timestamp: Date.now() });
  }

  clear(): void {
    this.cache.clear();
  }

  size(): number {
    return this.cache.size;
  }

  private serialize(key: K): string {
    if (typeof key === "string") return key;
    if (typeof key === "number") return String(key);
    return JSON.stringify(key);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Hash Cache
// ═══════════════════════════════════════════════════════════════════════════

export const hashCache = new LRUCache<string, number>(5000, 7200000); // 2 hour TTL

export function getCachedHash(input: string, hashFn: (input: string) => number): number {
  const cached = hashCache.get(input);
  if (cached !== undefined) return cached;

  const result = hashFn(input);
  hashCache.set(input, result);
  return result;
}

// ═══════════════════════════════════════════════════════════════════════════
// Metric Cache
// ═══════════════════════════════════════════════════════════════════════════

export interface MetricCacheKey {
  vectorId: string;
  seed: string;
  date: string;
}

export const metricCache = new LRUCache<MetricCacheKey, any>(1000, 1800000); // 30 min TTL

// ═══════════════════════════════════════════════════════════════════════════
// Pre-computed Context
// ═══════════════════════════════════════════════════════════════════════════

export interface OptimizedContext {
  seed: string;
  date: string;
  timestamp: number;

  // Pre-computed hashes
  runeHashes: Map<string, number>;
  archetypeHashes: Map<string, number>;

  // Original data
  runes: string[];
  archetypes?: string[];
  priorVector?: any;
}

export function createOptimizedContext(
  seed: string,
  date: string,
  runes: string[],
  archetypes?: string[],
  priorVector?: any,
  hashFn?: (input: string) => number
): OptimizedContext {
  const defaultHash = hashFn || ((s: string) => 0);

  const runeHashes = new Map<string, number>();
  runes.forEach(rune => {
    runeHashes.set(rune, getCachedHash(rune + seed, defaultHash));
  });

  const archetypeHashes = new Map<string, number>();
  if (archetypes) {
    archetypes.forEach(archetype => {
      archetypeHashes.set(archetype, getCachedHash(archetype + seed, defaultHash));
    });
  }

  return {
    seed,
    date,
    timestamp: Date.now(),
    runeHashes,
    archetypeHashes,
    runes,
    archetypes,
    priorVector,
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Feature Vector Optimization
// ═══════════════════════════════════════════════════════════════════════════

export interface OptimizedFeatures {
  keys: string[];
  values: number[];
  entries: [string, number][];
  size: number;
}

export function extractFeatures(features: Record<string, number>): OptimizedFeatures {
  const entries = Object.entries(features);
  const keys = Object.keys(features);
  const values = Object.values(features);

  return {
    keys,
    values,
    entries,
    size: keys.length,
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// Performance Monitoring
// ═══════════════════════════════════════════════════════════════════════════

export interface PerformanceMetrics {
  operation: string;
  duration: number;
  timestamp: number;
  cacheHit?: boolean;
}

export class PerformanceMonitor {
  private metrics: PerformanceMetrics[] = [];
  private readonly maxEntries: number = 10000;

  startTimer(): { end: (operation: string, cacheHit?: boolean) => void } {
    const start = performance.now();

    return {
      end: (operation: string, cacheHit?: boolean) => {
        const duration = performance.now() - start;
        this.record(operation, duration, cacheHit);
      },
    };
  }

  record(operation: string, duration: number, cacheHit?: boolean): void {
    this.metrics.push({
      operation,
      duration,
      timestamp: Date.now(),
      cacheHit,
    });

    // Trim if exceeding max entries
    if (this.metrics.length > this.maxEntries) {
      this.metrics = this.metrics.slice(-this.maxEntries);
    }
  }

  getStats(operation?: string): {
    count: number;
    avgDuration: number;
    minDuration: number;
    maxDuration: number;
    cacheHitRate: number;
  } {
    const filtered = operation
      ? this.metrics.filter(m => m.operation === operation)
      : this.metrics;

    if (filtered.length === 0) {
      return { count: 0, avgDuration: 0, minDuration: 0, maxDuration: 0, cacheHitRate: 0 };
    }

    const durations = filtered.map(m => m.duration);
    const cacheHits = filtered.filter(m => m.cacheHit === true).length;

    return {
      count: filtered.length,
      avgDuration: durations.reduce((sum, d) => sum + d, 0) / durations.length,
      minDuration: Math.min(...durations),
      maxDuration: Math.max(...durations),
      cacheHitRate: cacheHits / filtered.length,
    };
  }

  getOperations(): string[] {
    return Array.from(new Set(this.metrics.map(m => m.operation)));
  }

  clear(): void {
    this.metrics = [];
  }

  getRecentMetrics(limit: number = 100): PerformanceMetrics[] {
    return this.metrics.slice(-limit);
  }
}

// Global performance monitor
export const performanceMonitor = new PerformanceMonitor();

// ═══════════════════════════════════════════════════════════════════════════
// Memoization Decorator
// ═══════════════════════════════════════════════════════════════════════════

export function memoize<T extends (...args: any[]) => any>(
  fn: T,
  cacheSize: number = 100
): T {
  const cache = new LRUCache<any[], ReturnType<T>>(cacheSize, 3600000);

  return ((...args: Parameters<T>) => {
    const cached = cache.get(args);
    if (cached !== undefined) {
      return cached;
    }

    const result = fn(...args);
    cache.set(args, result);
    return result;
  }) as T;
}

// ═══════════════════════════════════════════════════════════════════════════
// Cache Statistics
// ═══════════════════════════════════════════════════════════════════════════

export interface CacheStats {
  hashCacheSize: number;
  metricCacheSize: number;
  performanceMetrics: {
    operations: string[];
    stats: Record<string, {
      count: number;
      avgDuration: number;
      cacheHitRate: number;
    }>;
  };
}

export function getCacheStats(): CacheStats {
  const operations = performanceMonitor.getOperations();
  const stats: Record<string, any> = {};

  operations.forEach(op => {
    stats[op] = performanceMonitor.getStats(op);
  });

  return {
    hashCacheSize: hashCache.size(),
    metricCacheSize: metricCache.size(),
    performanceMetrics: {
      operations,
      stats,
    },
  };
}

export function clearAllCaches(): void {
  hashCache.clear();
  metricCache.clear();
  performanceMonitor.clear();
}
