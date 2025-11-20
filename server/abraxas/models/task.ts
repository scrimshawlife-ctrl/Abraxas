/**
 * ABX-Core v1.2 - SymbolicTask Model
 * SEED Framework Compliant
 *
 * @module abraxas/models/task
 * @entropy_class low
 * @deterministic true
 *
 * Defines schedulable symbolic tasks for ERS (Event-driven Ritual Scheduler)
 */

import type { RitualInput } from "./ritual";

/**
 * Task execution status
 */
export type TaskStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

/**
 * Task trigger types
 */
export type TaskTrigger =
  | { type: "cron"; expression: string }
  | { type: "interval"; milliseconds: number }
  | { type: "ritual"; event: "daily" | "weekly" | "monthly" }
  | { type: "manual" };

/**
 * Task execution context
 */
export interface TaskContext {
  taskId: string;
  executionId: string;
  scheduledAt: number;
  startedAt?: number;
  ritual: RitualInput;
  trigger: TaskTrigger;
}

/**
 * Task execution result
 */
export interface TaskResult<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  metrics: {
    duration: number;
    quality?: number;
    drift?: number;
    entropy?: number;
  };
  provenance: {
    taskId: string;
    executionId: string;
    seed: string;
    timestamp: number;
  };
}

/**
 * Symbolic task executor function
 */
export type TaskExecutor<T = any> = (
  context: TaskContext
) => Promise<TaskResult<T>>;

/**
 * Symbolic task definition
 */
export interface SymbolicTask<T = any> {
  id: string;
  name: string;
  description: string;
  pipeline: string; // Pipeline identifier (e.g., "daily-oracle", "vc-analyzer")
  executor: TaskExecutor<T>;
  trigger: TaskTrigger;
  enabled: boolean;
  config?: Record<string, any>;

  // SEED compliance
  deterministic: boolean;
  entropy_class: "low" | "medium" | "high";
  capabilities: {
    read: string[];
    write: string[];
    network: boolean;
  };
}

/**
 * Task execution record
 */
export interface TaskExecution {
  id: string;
  taskId: string;
  status: TaskStatus;
  scheduledAt: number;
  startedAt?: number;
  completedAt?: number;
  duration?: number;
  result?: TaskResult;
  error?: string;
}

/**
 * Task schedule configuration
 */
export interface TaskSchedule {
  taskId: string;
  trigger: TaskTrigger;
  enabled: boolean;
  lastExecution?: number;
  nextExecution?: number;
  executionCount: number;
}
