import Database from "better-sqlite3";

const db = new Database(process.env.DATABASE_URL || "abraxas.db");

// Initialize database schema
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

  CREATE TABLE IF NOT EXISTS social_trends (
    id TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    created_at INTEGER NOT NULL
  );

  CREATE TABLE IF NOT EXISTS vc_analyses (
    id TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    created_at INTEGER NOT NULL
  );
`);

// Prepared statements
export const q = {
  insertRun: db.prepare(`
    INSERT INTO ritual_runs (id, user_id, date, seed, runes_json, results_json, created_at) 
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `),
  insertSigil: db.prepare(`
    INSERT INTO sigils (id, owner_id, core, seed, method, created_at) 
    VALUES (?, ?, ?, ?, ?, ?)
  `),
  insertTrends: db.prepare(`
    INSERT INTO social_trends (id, payload_json, created_at) 
    VALUES (?, ?, ?)
  `),
  insertRecs: db.prepare(`
    INSERT INTO vc_analyses (id, user_id, payload_json, created_at) 
    VALUES (?, ?, ?, ?)
  `)
};

export default db;