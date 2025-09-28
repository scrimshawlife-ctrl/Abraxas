import { sql } from "drizzle-orm";
import { pgTable, text, varchar, timestamp, json, real, integer, boolean, index } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// Session storage table for Replit Auth
export const sessions = pgTable(
  "sessions",
  {
    sid: varchar("sid").primaryKey(),
    sess: json("sess").notNull(),
    expire: timestamp("expire").notNull(),
  },
  (table) => [index("IDX_session_expire").on(table.expire)],
);

// Users table - updated for Replit Auth compatibility
export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  // Legacy fields (keeping for compatibility)
  username: text("username").unique(), // Optional for legacy compatibility
  password: text("password"), // Optional for legacy compatibility
  // Replit Auth fields
  email: varchar("email").unique().notNull(), // Required for Replit Auth
  firstName: varchar("first_name"),
  lastName: varchar("last_name"),
  profileImageUrl: varchar("profile_image_url"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
});

// Trading configurations/weights
export const tradingConfigs = pgTable("trading_configs", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").references(() => users.id),
  name: text("name").notNull(), // preset name or "custom"
  weights: json("weights").notNull(), // JSON object with feature weights
  isActive: boolean("is_active").default(false).notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
});

// Ritual execution history
export const ritualHistory = pgTable("ritual_history", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").references(() => users.id),
  configId: varchar("config_id").references(() => tradingConfigs.id),
  ritualType: text("ritual_type").notNull(), // "market_divination", "prediction", etc
  inputData: json("input_data"), // The data fed into the ritual
  results: json("results"), // The mystical outputs
  confidence: real("confidence"), // 0-1 confidence score
  duration: integer("duration"), // milliseconds
  status: text("status").notNull().default("completed"), // "running", "completed", "failed"
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// Market predictions and outcomes
export const predictions = pgTable("predictions", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").references(() => users.id),
  symbol: text("symbol").notNull(), // Trading symbol predicted
  predictionType: text("prediction_type").notNull(), // "price", "trend", "volatility"
  predictedValue: real("predicted_value"), // The numerical prediction
  actualValue: real("actual_value"), // What actually happened
  confidence: real("confidence").notNull(), // 0-1 confidence
  timeHorizon: integer("time_horizon").notNull(), // prediction timeframe in hours
  isResolved: boolean("is_resolved").default(false).notNull(),
  accuracy: real("accuracy"), // calculated accuracy when resolved
  createdAt: timestamp("created_at").defaultNow().notNull(),
  resolvedAt: timestamp("resolved_at"),
});

// Mystical metrics and performance tracking
export const mysticalMetrics = pgTable("mystical_metrics", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").references(() => users.id),
  metricType: text("metric_type").notNull(), // "accuracy", "profit", "mystical_alignment"
  value: real("value").notNull(),
  period: text("period").notNull(), // "daily", "weekly", "monthly"
  metadata: json("metadata"), // Additional context
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// User sessions and mystical workings
export const userSessions = pgTable("user_sessions", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").references(() => users.id),
  sessionType: text("session_type").notNull(), // "trading", "configuration", "analysis"
  startTime: timestamp("start_time").defaultNow().notNull(),
  endTime: timestamp("end_time"),
  actions: json("actions"), // Array of actions taken during session
  outcome: text("outcome"), // "successful", "terminated", "error"
});

// Mystical indicators registry
export const indicators = pgTable("indicators", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  ikey: text("ikey").notNull().unique(), // weight key: 'ind:<slug>'
  name: text("name").notNull(), // display name
  svgPath: text("svg_path").notNull(), // rune path for visualization
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// Indicator value cache for performance
export const indicatorCache = pgTable("indicator_cache", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  ikey: text("ikey").notNull().references(() => indicators.ikey),
  subject: text("subject").notNull(), // ticker/pair/etc
  day: text("day").notNull(), // date string for day scoping
  seed: text("seed").notNull(), // seed for deterministic scoping
  value: real("value").notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// Dynamic watchlists for equity and FX analysis
export const watchlists = pgTable("watchlists", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").references(() => users.id),
  name: text("name").notNull(), // "Growth Opportunities", "Short Candidates", etc
  type: text("type").notNull(), // "growth", "short", "custom"
  description: text("description"),
  isActive: boolean("is_active").default(true).notNull(),
  lastAnalyzed: timestamp("last_analyzed"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow().notNull(),
});

// Items within watchlists with analysis data
export const watchlistItems = pgTable("watchlist_items", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  watchlistId: varchar("watchlist_id").notNull().references(() => watchlists.id),
  symbol: text("symbol").notNull(), // ticker or FX pair
  symbolType: text("symbol_type").notNull(), // "equity" or "fx"
  analysisScore: real("analysis_score").notNull(), // -1 to 1 (negative for short, positive for growth)
  confidence: real("confidence").notNull(), // 0-1 confidence in the analysis
  growthPotential: real("growth_potential"), // 0-1 score for growth opportunity
  shortPotential: real("short_potential"), // 0-1 score for short opportunity
  riskLevel: text("risk_level").notNull(), // "low", "medium", "high"
  sector: text("sector"), // market sector for equities
  rationale: text("rationale"), // explanation of why it's on the watchlist
  metadata: json("metadata"), // additional analysis data
  addedAt: timestamp("added_at").defaultNow().notNull(),
  lastUpdated: timestamp("last_updated").defaultNow().notNull(),
});

// Replit Auth user schema
export const insertReplitUserSchema = createInsertSchema(users).pick({
  id: true,
  email: true,
  firstName: true,
  lastName: true,
  profileImageUrl: true,
});

// Legacy user schema (keeping for compatibility)
export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export const insertTradingConfigSchema = createInsertSchema(tradingConfigs).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export const insertRitualHistorySchema = createInsertSchema(ritualHistory).omit({
  id: true,
  createdAt: true,
});

export const insertPredictionSchema = createInsertSchema(predictions).omit({
  id: true,
  createdAt: true,
  resolvedAt: true,
});

export const insertMysticalMetricsSchema = createInsertSchema(mysticalMetrics).omit({
  id: true,
  createdAt: true,
});

export const insertUserSessionSchema = createInsertSchema(userSessions).omit({
  id: true,
  startTime: true,
});

export const insertIndicatorSchema = createInsertSchema(indicators).omit({
  id: true,
  createdAt: true,
}).extend({
  ikey: z.string().regex(/^ind:[a-z0-9-]{1,64}$/, "Indicator key must be format 'ind:slug' where slug is alphanumeric with dashes, 1-64 characters"),
  name: z.string().min(1).max(128, "Name must be 1-128 characters"),
  svgPath: z.string().min(1).max(2000, "SVG path must be 1-2000 characters")
});

export const insertIndicatorCacheSchema = createInsertSchema(indicatorCache).omit({
  id: true,
  createdAt: true,
}).extend({
  day: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Day must be YYYY-MM-DD format"),
  seed: z.string().min(1).max(64, "Seed must be 1-64 characters")
});

export const insertWatchlistSchema = createInsertSchema(watchlists).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
}).extend({
  name: z.string().min(1).max(128, "Name must be 1-128 characters"),
  type: z.enum(["growth", "short", "custom"], { required_error: "Type must be growth, short, or custom" }),
  description: z.string().max(500).optional()
});

export const insertWatchlistItemSchema = createInsertSchema(watchlistItems).omit({
  id: true,
  addedAt: true,
  lastUpdated: true,
}).extend({
  symbol: z.string().min(1).max(20, "Symbol must be 1-20 characters"),
  symbolType: z.enum(["equity", "fx"], { required_error: "Symbol type must be equity or fx" }),
  analysisScore: z.number().min(-1).max(1, "Analysis score must be between -1 and 1"),
  confidence: z.number().min(0).max(1, "Confidence must be between 0 and 1"),
  growthPotential: z.number().min(0).max(1).optional(),
  shortPotential: z.number().min(0).max(1).optional(),
  riskLevel: z.enum(["low", "medium", "high"], { required_error: "Risk level must be low, medium, or high" }),
  sector: z.string().max(100).optional(),
  rationale: z.string().max(1000).optional()
});

// Export types
export type UpsertUser = z.infer<typeof insertReplitUserSchema>;
export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;
export type InsertTradingConfig = z.infer<typeof insertTradingConfigSchema>;
export type TradingConfig = typeof tradingConfigs.$inferSelect;
export type InsertRitualHistory = z.infer<typeof insertRitualHistorySchema>;
export type RitualHistory = typeof ritualHistory.$inferSelect;
export type InsertPrediction = z.infer<typeof insertPredictionSchema>;
export type Prediction = typeof predictions.$inferSelect;
export type InsertMysticalMetrics = z.infer<typeof insertMysticalMetricsSchema>;
export type MysticalMetrics = typeof mysticalMetrics.$inferSelect;
export type InsertUserSession = z.infer<typeof insertUserSessionSchema>;
export type UserSession = typeof userSessions.$inferSelect;
export type InsertIndicator = z.infer<typeof insertIndicatorSchema>;
export type Indicator = typeof indicators.$inferSelect;
export type InsertIndicatorCache = z.infer<typeof insertIndicatorCacheSchema>;
export type IndicatorCache = typeof indicatorCache.$inferSelect;
export type InsertWatchlist = z.infer<typeof insertWatchlistSchema>;
export type Watchlist = typeof watchlists.$inferSelect;
export type InsertWatchlistItem = z.infer<typeof insertWatchlistItemSchema>;
export type WatchlistItem = typeof watchlistItems.$inferSelect;
