/**
 * ABX-Core v1.2 - ERS (Event-driven Ritual Scheduler)
 * SEED Framework Compliant
 *
 * @module abraxas/integrations/ers-scheduler
 * @entropy_class low
 * @deterministic false (timing-dependent)
 * @capabilities { read: ["tasks"], write: ["executions"], network: false }
 *
 * Manages scheduled execution of symbolic tasks:
 * - Cron-based scheduling
 * - Interval-based execution
 * - Ritual-driven triggers
 * - Execution history tracking
 * - SEED compliance enforcement
 */

import crypto from "crypto";
import type {
  SymbolicTask,
  TaskExecution,
  TaskSchedule,
  TaskContext,
  TaskResult,
  TaskStatus,
  TaskTrigger,
} from "../models/task";

/**
 * ERS Scheduler singleton
 */
export class ERSScheduler {
  private tasks: Map<string, SymbolicTask> = new Map();
  private schedules: Map<string, TaskSchedule> = new Map();
  private executions: Map<string, TaskExecution> = new Map();
  private timers: Map<string, NodeJS.Timeout> = new Map();
  private running: boolean = false;

  /**
   * Register a symbolic task with the scheduler
   */
  registerTask(task: SymbolicTask): void {
    if (this.tasks.has(task.id)) {
      console.warn(`[ERS] Task ${task.id} already registered, replacing`);
    }

    this.tasks.set(task.id, task);

    // Create schedule
    const schedule: TaskSchedule = {
      taskId: task.id,
      trigger: task.trigger,
      enabled: task.enabled,
      executionCount: 0,
    };

    this.schedules.set(task.id, schedule);

    // Schedule if enabled and running
    if (task.enabled && this.running) {
      this.scheduleTask(task.id);
    }

    console.log(
      `[ERS] Registered task: ${task.id} (${task.name}) - ${task.trigger.type}`
    );
  }

  /**
   * Unregister a task
   */
  unregisterTask(taskId: string): void {
    const timer = this.timers.get(taskId);
    if (timer) {
      clearTimeout(timer);
      this.timers.delete(taskId);
    }

    this.tasks.delete(taskId);
    this.schedules.delete(taskId);

    console.log(`[ERS] Unregistered task: ${taskId}`);
  }

  /**
   * Start the scheduler
   */
  start(): void {
    if (this.running) {
      console.warn("[ERS] Scheduler already running");
      return;
    }

    this.running = true;

    // Schedule all enabled tasks
    for (const [taskId, task] of Array.from(this.tasks.entries())) {
      if (task.enabled) {
        this.scheduleTask(taskId);
      }
    }

    console.log(
      `[ERS] Scheduler started with ${this.tasks.size} registered tasks`
    );
  }

  /**
   * Stop the scheduler
   */
  stop(): void {
    if (!this.running) {
      return;
    }

    this.running = false;

    // Clear all timers
    for (const timer of Array.from(this.timers.values())) {
      clearTimeout(timer);
    }
    this.timers.clear();

    console.log("[ERS] Scheduler stopped");
  }

  /**
   * Schedule a specific task
   */
  private scheduleTask(taskId: string): void {
    const task = this.tasks.get(taskId);
    if (!task) {
      console.error(`[ERS] Task not found: ${taskId}`);
      return;
    }

    const schedule = this.schedules.get(taskId);
    if (!schedule || !schedule.enabled) {
      return;
    }

    // Clear existing timer
    const existingTimer = this.timers.get(taskId);
    if (existingTimer) {
      clearTimeout(existingTimer);
    }

    // Calculate next execution delay
    const delay = this.calculateDelay(task.trigger, schedule);

    if (delay === null) {
      console.log(`[ERS] Task ${taskId} will not be scheduled (manual trigger)`);
      return;
    }

    schedule.nextExecution = Date.now() + delay;

    // Schedule execution
    const timer = setTimeout(() => {
      this.executeTask(taskId);
    }, delay);

    this.timers.set(taskId, timer);

    console.log(
      `[ERS] Scheduled task ${taskId} to run in ${Math.round(delay / 1000)}s`
    );
  }

  /**
   * Calculate delay until next execution
   */
  private calculateDelay(
    trigger: TaskTrigger,
    schedule: TaskSchedule
  ): number | null {
    switch (trigger.type) {
      case "interval":
        return trigger.milliseconds;

      case "cron":
        // Simple cron implementation - only supports basic patterns
        return this.parseCronDelay(trigger.expression);

      case "ritual":
        // Ritual-based triggers
        return this.parseRitualDelay(trigger.event);

      case "manual":
        return null; // No automatic scheduling

      default:
        console.error(`[ERS] Unknown trigger type: ${(trigger as any).type}`);
        return null;
    }
  }

  /**
   * Parse cron expression to delay (simplified)
   */
  private parseCronDelay(expression: string): number {
    // Simplified cron parser - supports basic patterns only
    // Format: "minute hour day month weekday"
    // Examples: "0 0 * * *" (daily at midnight), "*/15 * * * *" (every 15 min)

    const parts = expression.split(" ");
    if (parts.length !== 5) {
      console.error(`[ERS] Invalid cron expression: ${expression}`);
      return 60000; // Default to 1 minute
    }

    const [minute, hour, day, month, weekday] = parts;

    const now = new Date();
    const next = new Date(now);

    // Handle simple patterns
    if (minute === "0" && hour === "0") {
      // Daily at midnight
      next.setDate(next.getDate() + 1);
      next.setHours(0, 0, 0, 0);
    } else if (minute.startsWith("*/")) {
      // Interval pattern (e.g., */15 for every 15 minutes)
      const interval = parseInt(minute.substring(2));
      const currentMinute = now.getMinutes();
      const nextMinute = Math.ceil((currentMinute + 1) / interval) * interval;
      next.setMinutes(nextMinute, 0, 0);
      if (nextMinute >= 60) {
        next.setHours(next.getHours() + 1);
        next.setMinutes(nextMinute % 60, 0, 0);
      }
    } else if (hour === "*" && minute !== "*") {
      // Specific minute every hour
      const targetMinute = parseInt(minute);
      next.setMinutes(targetMinute, 0, 0);
      if (now.getMinutes() >= targetMinute) {
        next.setHours(next.getHours() + 1);
      }
    } else {
      // Default: 1 hour
      next.setHours(next.getHours() + 1);
    }

    return next.getTime() - now.getTime();
  }

  /**
   * Parse ritual-based delay
   */
  private parseRitualDelay(event: "daily" | "weekly" | "monthly"): number {
    const now = new Date();
    const next = new Date(now);

    switch (event) {
      case "daily":
        // Next day at midnight
        next.setDate(next.getDate() + 1);
        next.setHours(0, 0, 0, 0);
        break;

      case "weekly":
        // Next Monday at midnight
        const daysUntilMonday = (8 - now.getDay()) % 7 || 7;
        next.setDate(next.getDate() + daysUntilMonday);
        next.setHours(0, 0, 0, 0);
        break;

      case "monthly":
        // First day of next month at midnight
        next.setMonth(next.getMonth() + 1);
        next.setDate(1);
        next.setHours(0, 0, 0, 0);
        break;
    }

    return next.getTime() - now.getTime();
  }

  /**
   * Execute a task
   */
  private async executeTask(taskId: string): Promise<void> {
    const task = this.tasks.get(taskId);
    if (!task) {
      console.error(`[ERS] Task not found for execution: ${taskId}`);
      return;
    }

    const schedule = this.schedules.get(taskId);
    if (!schedule) {
      console.error(`[ERS] Schedule not found: ${taskId}`);
      return;
    }

    // Create execution record
    const executionId = crypto.randomUUID();
    const execution: TaskExecution = {
      id: executionId,
      taskId: task.id,
      status: "running",
      scheduledAt: schedule.nextExecution || Date.now(),
      startedAt: Date.now(),
    };

    this.executions.set(executionId, execution);

    console.log(`[ERS] Executing task: ${task.id} (${task.name})`);

    try {
      // Create task context with ritual
      const context: TaskContext = {
        taskId: task.id,
        executionId,
        scheduledAt: execution.scheduledAt,
        startedAt: execution.startedAt,
        ritual: this.generateRitual(),
        trigger: task.trigger,
      };

      // Execute task
      const result = await task.executor(context);

      // Update execution record
      execution.status = result.success ? "completed" : "failed";
      execution.completedAt = Date.now();
      execution.duration = execution.completedAt - (execution.startedAt || 0);
      execution.result = result;

      if (!result.success) {
        execution.error = result.error;
        console.error(
          `[ERS] Task ${task.id} failed: ${result.error}`
        );
      } else {
        console.log(
          `[ERS] Task ${task.id} completed in ${execution.duration}ms`
        );
      }

      // Update schedule
      schedule.lastExecution = Date.now();
      schedule.executionCount++;
    } catch (error) {
      execution.status = "failed";
      execution.completedAt = Date.now();
      execution.duration = execution.completedAt - (execution.startedAt || Date.now());
      execution.error = error instanceof Error ? error.message : String(error);

      console.error(`[ERS] Task ${task.id} threw error:`, error);
    }

    // Reschedule if still enabled
    if (task.enabled && this.running) {
      this.scheduleTask(taskId);
    }
  }

  /**
   * Manually trigger a task execution
   */
  async triggerTask(taskId: string): Promise<TaskExecution> {
    const task = this.tasks.get(taskId);
    if (!task) {
      throw new Error(`Task not found: ${taskId}`);
    }

    // Create execution record
    const executionId = crypto.randomUUID();
    const execution: TaskExecution = {
      id: executionId,
      taskId: task.id,
      status: "running",
      scheduledAt: Date.now(),
      startedAt: Date.now(),
    };

    this.executions.set(executionId, execution);

    console.log(`[ERS] Manually triggering task: ${task.id}`);

    try {
      const context: TaskContext = {
        taskId: task.id,
        executionId,
        scheduledAt: execution.scheduledAt,
        startedAt: execution.startedAt,
        ritual: this.generateRitual(),
        trigger: { type: "manual" },
      };

      const result = await task.executor(context);

      execution.status = result.success ? "completed" : "failed";
      execution.completedAt = Date.now();
      execution.duration = execution.completedAt - (execution.startedAt || Date.now());
      execution.result = result;

      if (!result.success) {
        execution.error = result.error;
      }
    } catch (error) {
      execution.status = "failed";
      execution.completedAt = Date.now();
      execution.duration = execution.completedAt - (execution.startedAt || Date.now());
      execution.error = error instanceof Error ? error.message : String(error);
    }

    return execution;
  }

  /**
   * Generate ritual for task execution
   */
  private generateRitual(): any {
    // Import dynamically to avoid circular dependencies
    const { runRitual } = require("../../runes");
    return runRitual();
  }

  /**
   * Get task by ID
   */
  getTask(taskId: string): SymbolicTask | undefined {
    return this.tasks.get(taskId);
  }

  /**
   * Get all registered tasks
   */
  getTasks(): SymbolicTask[] {
    return Array.from(this.tasks.values());
  }

  /**
   * Get schedule for a task
   */
  getSchedule(taskId: string): TaskSchedule | undefined {
    return this.schedules.get(taskId);
  }

  /**
   * Get all schedules
   */
  getSchedules(): TaskSchedule[] {
    return Array.from(this.schedules.values());
  }

  /**
   * Get execution by ID
   */
  getExecution(executionId: string): TaskExecution | undefined {
    return this.executions.get(executionId);
  }

  /**
   * Get executions for a task
   */
  getTaskExecutions(taskId: string, limit: number = 10): TaskExecution[] {
    return Array.from(this.executions.values())
      .filter((e) => e.taskId === taskId)
      .sort((a, b) => (b.startedAt || 0) - (a.startedAt || 0))
      .slice(0, limit);
  }

  /**
   * Get recent executions
   */
  getRecentExecutions(limit: number = 20): TaskExecution[] {
    return Array.from(this.executions.values())
      .sort((a, b) => (b.startedAt || 0) - (a.startedAt || 0))
      .slice(0, limit);
  }

  /**
   * Enable a task
   */
  enableTask(taskId: string): void {
    const task = this.tasks.get(taskId);
    const schedule = this.schedules.get(taskId);

    if (!task || !schedule) {
      throw new Error(`Task not found: ${taskId}`);
    }

    task.enabled = true;
    schedule.enabled = true;

    if (this.running) {
      this.scheduleTask(taskId);
    }

    console.log(`[ERS] Enabled task: ${taskId}`);
  }

  /**
   * Disable a task
   */
  disableTask(taskId: string): void {
    const task = this.tasks.get(taskId);
    const schedule = this.schedules.get(taskId);

    if (!task || !schedule) {
      throw new Error(`Task not found: ${taskId}`);
    }

    task.enabled = false;
    schedule.enabled = false;

    // Clear timer
    const timer = this.timers.get(taskId);
    if (timer) {
      clearTimeout(timer);
      this.timers.delete(taskId);
    }

    console.log(`[ERS] Disabled task: ${taskId}`);
  }

  /**
   * Get scheduler status
   */
  getStatus(): {
    running: boolean;
    tasks: number;
    enabled: number;
    executions: number;
  } {
    const enabled = Array.from(this.tasks.values()).filter(
      (t) => t.enabled
    ).length;

    return {
      running: this.running,
      tasks: this.tasks.size,
      enabled,
      executions: this.executions.size,
    };
  }
}

// Singleton instance
export const scheduler = new ERSScheduler();
