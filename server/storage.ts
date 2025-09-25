import { 
  type User, 
  type InsertUser, 
  type TradingConfig, 
  type InsertTradingConfig,
  type RitualHistory,
  type InsertRitualHistory,
  type Prediction,
  type InsertPrediction,
  type MysticalMetrics,
  type InsertMysticalMetrics,
  type UserSession,
  type InsertUserSession
} from "@shared/schema";
import { db } from "./db";
import { users, tradingConfigs, ritualHistory, predictions, mysticalMetrics, userSessions } from "@shared/schema";
import { eq, desc, and } from "drizzle-orm";

export interface IStorage {
  // User operations
  getUser(id: string): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  
  // Trading config operations
  getTradingConfig(id: string): Promise<TradingConfig | undefined>;
  getTradingConfigs(userId?: string): Promise<TradingConfig[]>;
  createTradingConfig(config: InsertTradingConfig): Promise<TradingConfig>;
  updateTradingConfig(id: string, config: Partial<InsertTradingConfig>): Promise<TradingConfig | undefined>;
  deleteTradingConfig(id: string): Promise<boolean>;
  
  // Ritual history operations
  getRitualHistory(userId?: string, limit?: number): Promise<RitualHistory[]>;
  createRitualHistory(ritual: InsertRitualHistory): Promise<RitualHistory>;
  updateRitualStatus(id: string, status: string, results?: any): Promise<RitualHistory | undefined>;
  
  // Prediction operations
  getPredictions(userId?: string, isResolved?: boolean): Promise<Prediction[]>;
  createPrediction(prediction: InsertPrediction): Promise<Prediction>;
  resolvePrediction(id: string, actualValue: number, accuracy: number): Promise<Prediction | undefined>;
  
  // Metrics operations
  getMysticalMetrics(userId?: string, metricType?: string, period?: string): Promise<MysticalMetrics[]>;
  createMysticalMetrics(metrics: InsertMysticalMetrics): Promise<MysticalMetrics>;
  
  // Session operations
  getUserSessions(userId: string, limit?: number): Promise<UserSession[]>;
  createUserSession(session: InsertUserSession): Promise<UserSession>;
  endUserSession(id: string, outcome: string, actions?: any[]): Promise<UserSession | undefined>;
}

export class PostgresStorage implements IStorage {
  // User operations
  async getUser(id: string): Promise<User | undefined> {
    const result = await db.select().from(users).where(eq(users.id, id));
    return result[0];
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    const result = await db.select().from(users).where(eq(users.username, username));
    return result[0];
  }

  async createUser(user: InsertUser): Promise<User> {
    const result = await db.insert(users).values(user).returning();
    return result[0];
  }

  // Trading config operations
  async getTradingConfig(id: string): Promise<TradingConfig | undefined> {
    const result = await db.select().from(tradingConfigs).where(eq(tradingConfigs.id, id));
    return result[0];
  }

  async getTradingConfigs(userId?: string): Promise<TradingConfig[]> {
    if (userId) {
      return await db.select().from(tradingConfigs)
        .where(eq(tradingConfigs.userId, userId))
        .orderBy(desc(tradingConfigs.updatedAt));
    }
    return await db.select().from(tradingConfigs).orderBy(desc(tradingConfigs.updatedAt));
  }

  async createTradingConfig(config: InsertTradingConfig): Promise<TradingConfig> {
    const result = await db.insert(tradingConfigs).values(config).returning();
    return result[0];
  }

  async updateTradingConfig(id: string, config: Partial<InsertTradingConfig>): Promise<TradingConfig | undefined> {
    const result = await db.update(tradingConfigs)
      .set({ ...config, updatedAt: new Date() })
      .where(eq(tradingConfigs.id, id))
      .returning();
    return result[0];
  }

  async deleteTradingConfig(id: string): Promise<boolean> {
    const result = await db.delete(tradingConfigs).where(eq(tradingConfigs.id, id));
    return result.rowCount ? result.rowCount > 0 : false;
  }

  // Ritual history operations
  async getRitualHistory(userId?: string, limit = 50): Promise<RitualHistory[]> {
    if (userId) {
      return await db.select().from(ritualHistory)
        .where(eq(ritualHistory.userId, userId))
        .orderBy(desc(ritualHistory.createdAt))
        .limit(limit);
    }
    
    return await db.select().from(ritualHistory)
      .orderBy(desc(ritualHistory.createdAt))
      .limit(limit);
  }

  async createRitualHistory(ritual: InsertRitualHistory): Promise<RitualHistory> {
    const result = await db.insert(ritualHistory).values(ritual).returning();
    return result[0];
  }

  async updateRitualStatus(id: string, status: string, results?: any): Promise<RitualHistory | undefined> {
    const updateData: any = { status };
    if (results !== undefined) {
      updateData.results = results;
    }
    
    const result = await db.update(ritualHistory)
      .set(updateData)
      .where(eq(ritualHistory.id, id))
      .returning();
    return result[0];
  }

  // Prediction operations
  async getPredictions(userId?: string, isResolved?: boolean): Promise<Prediction[]> {
    const conditions = [];
    if (userId) conditions.push(eq(predictions.userId, userId));
    if (isResolved !== undefined) conditions.push(eq(predictions.isResolved, isResolved));
    
    if (conditions.length > 0) {
      return await db.select().from(predictions)
        .where(and(...conditions))
        .orderBy(desc(predictions.createdAt));
    }
    
    return await db.select().from(predictions)
      .orderBy(desc(predictions.createdAt));
  }

  async createPrediction(prediction: InsertPrediction): Promise<Prediction> {
    const result = await db.insert(predictions).values(prediction).returning();
    return result[0];
  }

  async resolvePrediction(id: string, actualValue: number, accuracy: number): Promise<Prediction | undefined> {
    const result = await db.update(predictions)
      .set({ 
        actualValue, 
        accuracy, 
        isResolved: true, 
        resolvedAt: new Date() 
      })
      .where(eq(predictions.id, id))
      .returning();
    return result[0];
  }

  // Metrics operations
  async getMysticalMetrics(userId?: string, metricType?: string, period?: string): Promise<MysticalMetrics[]> {
    const conditions = [];
    if (userId) conditions.push(eq(mysticalMetrics.userId, userId));
    if (metricType) conditions.push(eq(mysticalMetrics.metricType, metricType));
    if (period) conditions.push(eq(mysticalMetrics.period, period));
    
    if (conditions.length > 0) {
      return await db.select().from(mysticalMetrics)
        .where(and(...conditions))
        .orderBy(desc(mysticalMetrics.createdAt));
    }
    
    return await db.select().from(mysticalMetrics)
      .orderBy(desc(mysticalMetrics.createdAt));
  }

  async createMysticalMetrics(metrics: InsertMysticalMetrics): Promise<MysticalMetrics> {
    const result = await db.insert(mysticalMetrics).values(metrics).returning();
    return result[0];
  }

  // Session operations
  async getUserSessions(userId: string, limit = 20): Promise<UserSession[]> {
    return await db.select().from(userSessions)
      .where(eq(userSessions.userId, userId))
      .orderBy(desc(userSessions.startTime))
      .limit(limit);
  }

  async createUserSession(session: InsertUserSession): Promise<UserSession> {
    const result = await db.insert(userSessions).values(session).returning();
    return result[0];
  }

  async endUserSession(id: string, outcome: string, actions?: any[]): Promise<UserSession | undefined> {
    const updateData: any = { outcome, endTime: new Date() };
    if (actions !== undefined) {
      updateData.actions = actions;
    }
    
    const result = await db.update(userSessions)
      .set(updateData)
      .where(eq(userSessions.id, id))
      .returning();
    return result[0];
  }
}

// Legacy MemStorage for compatibility (if needed)
export class MemStorage implements IStorage {
  private users: Map<string, User> = new Map();
  private configs: Map<string, TradingConfig> = new Map();
  private rituals: RitualHistory[] = [];
  private preds: Prediction[] = [];
  private metrics: MysticalMetrics[] = [];
  private sessions: UserSession[] = [];

  async getUser(id: string): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(user => user.username === username);
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const user: User = { 
      ...insertUser, 
      id: crypto.randomUUID(),
      createdAt: new Date()
    };
    this.users.set(user.id, user);
    return user;
  }

  // Stub implementations for other methods (not used in memory mode)
  async getTradingConfig(id: string): Promise<TradingConfig | undefined> { return undefined; }
  async getTradingConfigs(userId?: string): Promise<TradingConfig[]> { return []; }
  async createTradingConfig(config: InsertTradingConfig): Promise<TradingConfig> { throw new Error("Not implemented in MemStorage"); }
  async updateTradingConfig(id: string, config: Partial<InsertTradingConfig>): Promise<TradingConfig | undefined> { return undefined; }
  async deleteTradingConfig(id: string): Promise<boolean> { return false; }
  async getRitualHistory(userId?: string, limit?: number): Promise<RitualHistory[]> { return []; }
  async createRitualHistory(ritual: InsertRitualHistory): Promise<RitualHistory> { throw new Error("Not implemented in MemStorage"); }
  async updateRitualStatus(id: string, status: string, results?: any): Promise<RitualHistory | undefined> { return undefined; }
  async getPredictions(userId?: string, isResolved?: boolean): Promise<Prediction[]> { return []; }
  async createPrediction(prediction: InsertPrediction): Promise<Prediction> { throw new Error("Not implemented in MemStorage"); }
  async resolvePrediction(id: string, actualValue: number, accuracy: number): Promise<Prediction | undefined> { return undefined; }
  async getMysticalMetrics(userId?: string, metricType?: string, period?: string): Promise<MysticalMetrics[]> { return []; }
  async createMysticalMetrics(metrics: InsertMysticalMetrics): Promise<MysticalMetrics> { throw new Error("Not implemented in MemStorage"); }
  async getUserSessions(userId: string, limit?: number): Promise<UserSession[]> { return []; }
  async createUserSession(session: InsertUserSession): Promise<UserSession> { throw new Error("Not implemented in MemStorage"); }
  async endUserSession(id: string, outcome: string, actions?: any[]): Promise<UserSession | undefined> { return undefined; }
}

// Use PostgreSQL storage by default, fallback to MemStorage if needed
export const storage = new PostgresStorage();
