import { sql } from "drizzle-orm";
import { pgTable, text, varchar, timestamp, json, real, integer, boolean } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// Users table
export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
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
  value: real("value").notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// Create insert schemas
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
});

// Export types
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
