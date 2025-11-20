/**
 * ABX-Core v1.2 - ERS Scheduler Tests
 * Test suite for task scheduling and execution
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { ERSScheduler } from "../integrations/ers-scheduler";
import type { SymbolicTask } from "../models/task";

describe("ERS Scheduler", () => {
  let scheduler: ERSScheduler;

  beforeEach(() => {
    scheduler = new ERSScheduler();
  });

  afterEach(() => {
    scheduler.stop();
  });

  describe("Task Registration", () => {
    it("registers task successfully", () => {
      const task: SymbolicTask = {
        id: "test-task",
        name: "Test Task",
        description: "Test task description",
        pipeline: "test-pipeline",
        trigger: { type: "manual" },
        enabled: true,
        deterministic: true,
        entropy_class: "low",
        capabilities: { read: [], write: [], network: false },
        executor: async () => ({
          success: true,
          metrics: { duration: 0 },
          provenance: {
            taskId: "test-task",
            executionId: "test-exec",
            seed: "test-seed",
            timestamp: Date.now(),
          },
        }),
      };

      scheduler.registerTask(task);

      expect(scheduler.getTasks()).toHaveLength(1);
      expect(scheduler.getTask("test-task")).toBeDefined();
    });

    it("unregisters task successfully", () => {
      const task: SymbolicTask = {
        id: "test-task",
        name: "Test Task",
        description: "Test",
        pipeline: "test",
        trigger: { type: "manual" },
        enabled: false,
        deterministic: true,
        entropy_class: "low",
        capabilities: { read: [], write: [], network: false },
        executor: async () => ({
          success: true,
          metrics: { duration: 0 },
          provenance: {
            taskId: "test-task",
            executionId: "test-exec",
            seed: "test-seed",
            timestamp: Date.now(),
          },
        }),
      };

      scheduler.registerTask(task);
      scheduler.unregisterTask("test-task");

      expect(scheduler.getTasks()).toHaveLength(0);
    });
  });

  describe("Scheduler Control", () => {
    it("starts and stops scheduler", () => {
      scheduler.start();
      expect(scheduler.getStatus().running).toBe(true);

      scheduler.stop();
      expect(scheduler.getStatus().running).toBe(false);
    });

    it("status reflects task count", () => {
      const task: SymbolicTask = {
        id: "task1",
        name: "Task 1",
        description: "Test",
        pipeline: "test",
        trigger: { type: "manual" },
        enabled: true,
        deterministic: true,
        entropy_class: "low",
        capabilities: { read: [], write: [], network: false },
        executor: async () => ({
          success: true,
          metrics: { duration: 0 },
          provenance: {
            taskId: "task1",
            executionId: "exec1",
            seed: "seed1",
            timestamp: Date.now(),
          },
        }),
      };

      scheduler.registerTask(task);

      const status = scheduler.getStatus();
      expect(status.tasks).toBe(1);
      expect(status.enabled).toBe(1);
    });
  });

  describe("Task Execution", () => {
    it("executes manual task", async () => {
      let executed = false;

      const task: SymbolicTask = {
        id: "manual-task",
        name: "Manual Task",
        description: "Test",
        pipeline: "test",
        trigger: { type: "manual" },
        enabled: true,
        deterministic: true,
        entropy_class: "low",
        capabilities: { read: [], write: [], network: false },
        executor: async () => {
          executed = true;
          return {
            success: true,
            metrics: { duration: 100 },
            provenance: {
              taskId: "manual-task",
              executionId: "exec1",
              seed: "seed1",
              timestamp: Date.now(),
            },
          };
        },
      };

      scheduler.registerTask(task);
      const execution = await scheduler.triggerTask("manual-task");

      expect(executed).toBe(true);
      expect(execution.status).toBe("completed");
      expect(execution.result?.success).toBe(true);
    });

    it("tracks execution in history", async () => {
      const task: SymbolicTask = {
        id: "tracked-task",
        name: "Tracked Task",
        description: "Test",
        pipeline: "test",
        trigger: { type: "manual" },
        enabled: true,
        deterministic: true,
        entropy_class: "low",
        capabilities: { read: [], write: [], network: false },
        executor: async () => ({
          success: true,
          metrics: { duration: 100 },
          provenance: {
            taskId: "tracked-task",
            executionId: "exec1",
            seed: "seed1",
            timestamp: Date.now(),
          },
        }),
      };

      scheduler.registerTask(task);
      await scheduler.triggerTask("tracked-task");

      const executions = scheduler.getTaskExecutions("tracked-task");
      expect(executions).toHaveLength(1);
      expect(executions[0].taskId).toBe("tracked-task");
    });

    it("handles failed execution", async () => {
      const task: SymbolicTask = {
        id: "failing-task",
        name: "Failing Task",
        description: "Test",
        pipeline: "test",
        trigger: { type: "manual" },
        enabled: true,
        deterministic: true,
        entropy_class: "low",
        capabilities: { read: [], write: [], network: false },
        executor: async () => ({
          success: false,
          error: "Test error",
          metrics: { duration: 50 },
          provenance: {
            taskId: "failing-task",
            executionId: "exec1",
            seed: "seed1",
            timestamp: Date.now(),
          },
        }),
      };

      scheduler.registerTask(task);
      const execution = await scheduler.triggerTask("failing-task");

      expect(execution.status).toBe("failed");
      expect(execution.result?.success).toBe(false);
      expect(execution.error).toBe("Test error");
    });
  });

  describe("Task Enable/Disable", () => {
    it("enables disabled task", () => {
      const task: SymbolicTask = {
        id: "disabled-task",
        name: "Disabled Task",
        description: "Test",
        pipeline: "test",
        trigger: { type: "manual" },
        enabled: false,
        deterministic: true,
        entropy_class: "low",
        capabilities: { read: [], write: [], network: false },
        executor: async () => ({
          success: true,
          metrics: { duration: 0 },
          provenance: {
            taskId: "disabled-task",
            executionId: "exec1",
            seed: "seed1",
            timestamp: Date.now(),
          },
        }),
      };

      scheduler.registerTask(task);
      expect(scheduler.getStatus().enabled).toBe(0);

      scheduler.enableTask("disabled-task");
      expect(scheduler.getStatus().enabled).toBe(1);
    });

    it("disables enabled task", () => {
      const task: SymbolicTask = {
        id: "enabled-task",
        name: "Enabled Task",
        description: "Test",
        pipeline: "test",
        trigger: { type: "manual" },
        enabled: true,
        deterministic: true,
        entropy_class: "low",
        capabilities: { read: [], write: [], network: false },
        executor: async () => ({
          success: true,
          metrics: { duration: 0 },
          provenance: {
            taskId: "enabled-task",
            executionId: "exec1",
            seed: "seed1",
            timestamp: Date.now(),
          },
        }),
      };

      scheduler.registerTask(task);
      expect(scheduler.getStatus().enabled).toBe(1);

      scheduler.disableTask("enabled-task");
      expect(scheduler.getStatus().enabled).toBe(0);
    });
  });
});
