/**
 * ABX-Core v1.2 - SQLite Database Adapter
 * SEED Framework Compliant
 *
 * @module abraxas/integrations/sqlite-adapter
 * @deterministic true
 * @capabilities { read: ["database"], write: ["database"], network: false }
 *
 * Legacy SQLite adapter for abraxas-server.ts
 * Note: This is a compatibility layer. Production should use PostgreSQL via storage.ts
 */

import Database from "better-sqlite3";
import { v4 as uuidv4 } from "uuid";

export class SQLiteAdapter {
  private db: Database.Database;

  constructor(dbPath: string = "./abraxas.db") {
    this.db = new Database(dbPath);
    this.initializeSchema();
  }

  private initializeSchema(): void {
    this.db.exec(`
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
  }

  /**
   * Health check query
   */
  public healthCheck(): boolean {
    try {
      this.db.prepare("SELECT 1").get();
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Store ritual execution
   */
  public storeRitualRun(params: {
    userId: string;
    date: string;
    seed: string;
    runes: any[];
    results: any;
  }): string {
    const runId = uuidv4();

    try {
      this.db
        .prepare(
          `INSERT INTO ritual_runs (id, user_id, date, seed, runes_json, results_json, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)`
        )
        .run(
          runId,
          params.userId,
          params.date,
          params.seed,
          JSON.stringify(params.runes),
          JSON.stringify(params.results),
          Date.now()
        );

      return runId;
    } catch (error) {
      console.error("Failed to store ritual run:", error);
      throw error;
    }
  }

  /**
   * Store sigil
   */
  public storeSigil(params: {
    ownerId: string;
    core: string;
    seed: string;
    method: string;
  }): string {
    const sigilId = uuidv4();

    try {
      this.db
        .prepare(
          `INSERT INTO sigils (id, owner_id, core, seed, method, created_at)
           VALUES (?, ?, ?, ?, ?, ?)`
        )
        .run(
          sigilId,
          params.ownerId,
          params.core,
          params.seed,
          params.method,
          Date.now()
        );

      return sigilId;
    } catch (error) {
      console.error("Failed to store sigil:", error);
      throw error;
    }
  }

  /**
   * Get ritual runs for user
   */
  public getRitualRuns(userId: string, limit: number = 10): any[] {
    try {
      return this.db
        .prepare(
          `SELECT * FROM ritual_runs
           WHERE user_id = ?
           ORDER BY created_at DESC
           LIMIT ?`
        )
        .all(userId, limit);
    } catch (error) {
      console.error("Failed to get ritual runs:", error);
      return [];
    }
  }

  /**
   * Close database connection
   */
  public close(): void {
    this.db.close();
  }
}

// Singleton instance for compatibility with existing code
export const sqliteDb = new SQLiteAdapter();
