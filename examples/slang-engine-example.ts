/**
 * ABRAXAS SLANG ENGINE - Usage Examples
 * Demonstrates all operating modes and capabilities
 *
 * Run with: npx tsx examples/slang-engine-example.ts
 */

import {
  initializeEngine,
  executeEngine,
  type SlangSignal,
  type SlangClass,
  type EngineState,
} from "../server/abraxas/slang_engine";

// ═══════════════════════════════════════════════════════════════════════════
// Example 1: OPEN Mode - Detect and Validate New Signals
// ═══════════════════════════════════════════════════════════════════════════

function exampleOpenMode() {
  console.log("\n═══════════════════════════════════════════════════════════");
  console.log("EXAMPLE 1: OPEN MODE - Detecting New Slang Signals");
  console.log("═══════════════════════════════════════════════════════════\n");

  const engine = initializeEngine("OPEN");
  const seed = "abraxas-demo-2025";

  // Candidate signals to ingest
  const candidates: Partial<SlangSignal>[] = [
    {
      term: "touch-grass",
      class: "ritual_avoidance",
      definition:
        "Dismissive advice to spend time offline, implying the recipient is too absorbed in digital discourse. Used to deflect engagement rather than address substance.",
      origin_context: "twitter/reddit",
      frequency_index: 0.7,
      pressure_vector: {
        cognitive: 0.4,
        social: 0.8,
        economic: 0.1,
        temporal: 0.6,
        identity: 0.5,
      },
      symptoms: [
        "Used in response to disagreements",
        "Implies moral superiority of offline life",
        "Avoids direct debate",
      ],
      hygiene: [
        "Recognize when genuinely overwhelmed vs. being dismissed",
        "Consider if breaks are self-directed or externally prescribed",
      ],
    },
    {
      term: "cooked",
      class: "unspoken_load",
      definition:
        "State of being overwhelmed, defeated, or facing inevitable negative outcome. Compresses complex feelings of burnout, futility, or systemic exhaustion into casual slang.",
      origin_context: "gen-z/tiktok",
      frequency_index: 0.85,
      pressure_vector: {
        cognitive: 0.9,
        social: 0.6,
        economic: 0.8,
        temporal: 0.9,
        identity: 0.7,
      },
      symptoms: [
        "Self-deprecating humor masking genuine stress",
        "Normalization of burnout states",
        "Performative exhaustion",
      ],
      hygiene: [
        "Distinguish between venting and chronic overwhelm",
        "Track frequency of use as stress indicator",
      ],
    },
    {
      term: "lol",
      class: "meaning_inflation",
      definition: "Just laughing.",
      origin_context: "everywhere",
      frequency_index: 0.2,
      pressure_vector: {
        cognitive: 0.1,
        social: 0.1,
        economic: 0.0,
        temporal: 0.1,
        identity: 0.0,
      },
      symptoms: [],
    },
  ];

  const result = executeEngine({
    mode: "OPEN",
    state: engine,
    params: {
      candidate_signals: candidates,
      seed,
      noise_threshold: 0.15,
    },
  });

  console.log(`Processed ${candidates.length} candidate signals:`);
  console.log(`  ✓ Accepted: ${result.result.accepted.length}`);
  console.log(`  ✗ Rejected: ${result.result.rejected.length}`);
  console.log(`  Pass rate: ${(result.result.validation_stats.passRate * 100).toFixed(1)}%\n`);

  console.log("Accepted signals:");
  result.result.accepted.forEach((signal: SlangSignal) => {
    console.log(`  • ${signal.term} (${signal.class})`);
    console.log(`    Strength: ${signal.signal_strength.toFixed(3)}`);
    console.log(`    Confidence: ${signal.confidence.toFixed(3)}`);
    console.log(`    Novelty: ${signal.novelty?.toFixed(3)}`);
  });

  console.log("\nRejected signals:");
  result.result.rejected.forEach(
    (r: { signal: Partial<SlangSignal>; reason: string }) => {
      console.log(`  • ${r.signal.term}: ${r.reason}`);
    }
  );

  return result.state;
}

// ═══════════════════════════════════════════════════════════════════════════
// Example 2: ALIGN Mode - Validate Pressure & Compression
// ═══════════════════════════════════════════════════════════════════════════

function exampleAlignMode(state: EngineState) {
  console.log("\n═══════════════════════════════════════════════════════════");
  console.log("EXAMPLE 2: ALIGN MODE - Validation & Quality Checks");
  console.log("═══════════════════════════════════════════════════════════\n");

  const result = executeEngine({
    mode: "ALIGN",
    state,
    params: { seed: "abraxas-demo-2025" },
  });

  console.log(`Revalidated ${result.result.revalidated.length} signals`);
  console.log(`Compression issues: ${result.result.compression_issues.length}`);
  console.log(`Pressure anomalies: ${result.result.pressure_anomalies.length}\n`);

  if (result.result.compression_issues.length > 0) {
    console.log("Compression issues detected:");
    result.result.compression_issues.forEach(
      (issue: { term: string; issue: string }) => {
        console.log(`  • ${issue.term}: ${issue.issue}`);
      }
    );
  }

  if (result.result.pressure_anomalies.length > 0) {
    console.log("\nPressure anomalies detected:");
    result.result.pressure_anomalies.forEach(
      (anomaly: { term: string; anomaly: string }) => {
        console.log(`  • ${anomaly.term}: ${anomaly.anomaly}`);
      }
    );
  }

  return result.state;
}

// ═══════════════════════════════════════════════════════════════════════════
// Example 3: ASCEND Mode - Integrate with Forecasting
// ═══════════════════════════════════════════════════════════════════════════

function exampleAscendMode(state: EngineState) {
  console.log("\n═══════════════════════════════════════════════════════════");
  console.log("EXAMPLE 3: ASCEND MODE - Forecasting Integration");
  console.log("═══════════════════════════════════════════════════════════\n");

  const result = executeEngine({
    mode: "ASCEND",
    state,
    params: {
      forecast_horizon_days: 30,
    },
  });

  console.log("Oracle Modulation:");
  console.log(
    `  Confidence adjustment: ${(result.result.oracle_modulation.confidence_adjustment * 100).toFixed(1)}%`
  );
  console.log(
    `  Narrative debt influence: ${result.result.oracle_modulation.narrative_debt_influence.toFixed(3)}\n`
  );

  console.log("Narrative Debt Index:");
  console.log(
    `  Total unspoken load: ${result.result.narrative_debt.total_unspoken_load.toFixed(3)}`
  );
  console.log(
    `  System stress level: ${result.result.narrative_debt.system_stress_level.toFixed(3)}`
  );
  console.log(`  Trend: ${result.result.narrative_debt.trend}`);
  console.log(
    `  Critical signals: ${result.result.narrative_debt.critical_signals.length}\n`
  );

  console.log("Drift Alerts:");
  if (result.result.drift_alerts.length > 0) {
    result.result.drift_alerts.forEach(
      (alert: {
        class: SlangClass;
        frequency_spike: number;
        severity: string;
      }) => {
        console.log(
          `  • ${alert.class}: ${alert.frequency_spike.toFixed(1)}% spike (${alert.severity})`
        );
      }
    );
  } else {
    console.log("  No alerts (no prior snapshot for comparison)");
  }

  console.log("\nMemetic Pressure Trends:");
  result.result.memetic_pressure_trends.forEach(
    (trend: {
      class: SlangClass;
      pressure_trend: number[];
      forecast_horizon_days: number;
    }) => {
      const current = trend.pressure_trend[0];
      const final = trend.pressure_trend[trend.pressure_trend.length - 1];
      const change = ((final - current) / current) * 100;
      console.log(
        `  • ${trend.class}: ${current.toFixed(3)} → ${final.toFixed(3)} (${change.toFixed(1)}% over ${trend.forecast_horizon_days}d)`
      );
    }
  );

  return result.state;
}

// ═══════════════════════════════════════════════════════════════════════════
// Example 4: CLEAR Mode - Decay and Archive
// ═══════════════════════════════════════════════════════════════════════════

function exampleClearMode(state: EngineState) {
  console.log("\n═══════════════════════════════════════════════════════════");
  console.log("EXAMPLE 4: CLEAR MODE - Decay & Archival");
  console.log("═══════════════════════════════════════════════════════════\n");

  const result = executeEngine({
    mode: "CLEAR",
    state,
    params: {},
  });

  console.log("Decay Statistics:");
  console.log(
    `  Total processed: ${result.result.decay_stats.totalProcessed}`
  );
  console.log(
    `  Average decay: ${result.result.decay_stats.averageDecay.toFixed(4)}`
  );
  console.log(`  Archived count: ${result.result.decay_stats.archivalCount}\n`);

  console.log(`Active signals after decay: ${result.result.decayed.length}`);
  console.log(`Archived signals: ${result.result.archived.length}`);
  console.log(`Resurrected signals: ${result.result.resurrected.length}`);

  return result.state;
}

// ═══════════════════════════════════════════════════════════════════════════
// Example 5: SEAL Mode - Provenance & Ledger
// ═══════════════════════════════════════════════════════════════════════════

function exampleSealMode(state: EngineState) {
  console.log("\n═══════════════════════════════════════════════════════════");
  console.log("EXAMPLE 5: SEAL MODE - Finalization & Provenance");
  console.log("═══════════════════════════════════════════════════════════\n");

  const result = executeEngine({
    mode: "SEAL",
    state,
    params: {
      seed: "abraxas-demo-2025",
      sources: ["manual-curation", "observation-logs"],
      version: "1.0.0",
    },
  });

  console.log("Provenance:");
  console.log(`  Seed: ${result.result.provenance.seed}`);
  console.log(`  Timestamp: ${result.result.provenance.timestamp}`);
  console.log(`  Version: ${result.result.provenance.version}`);
  console.log(
    `  Hash: ${result.result.provenance.deterministic_hash.slice(0, 16)}...`
  );
  console.log(`  Sources: ${result.result.provenance.sources.join(", ")}\n`);

  console.log("Ledger Entry:");
  console.log(`  Timestamp: ${result.result.ledger_entry.timestamp}`);
  console.log(
    `  Active signals: ${result.result.ledger_entry.active_signal_count}`
  );
  console.log(
    `  Archived signals: ${result.result.ledger_entry.archived_signal_count}`
  );
  console.log(
    `  State hash: ${result.result.ledger_entry.hash.slice(0, 16)}...`
  );

  return result.state;
}

// ═══════════════════════════════════════════════════════════════════════════
// Main Execution
// ═══════════════════════════════════════════════════════════════════════════

function main() {
  console.log("\n╔═══════════════════════════════════════════════════════════╗");
  console.log("║   ABRAXAS SLANG ENGINE - Comprehensive Demonstration      ║");
  console.log("║   Passive Organ. Observes. Speaks When Queried.          ║");
  console.log("╚═══════════════════════════════════════════════════════════╝");

  let state = exampleOpenMode();
  state = exampleAlignMode(state);
  state = exampleAscendMode(state);
  state = exampleClearMode(state);
  state = exampleSealMode(state);

  console.log("\n═══════════════════════════════════════════════════════════");
  console.log("Final Engine State:");
  console.log("═══════════════════════════════════════════════════════════\n");
  console.log(`Mode: ${state.mode}`);
  console.log(`Active signals: ${state.active_signals.length}`);
  console.log(`Archived signals: ${state.archived_signals.length}`);
  console.log(`Last sealed: ${state.last_seal_timestamp}`);
  console.log(
    `Provenance hash: ${state.provenance_hash?.slice(0, 16)}...\n`
  );

  console.log("✓ All operating modes demonstrated successfully\n");
}

// Run if executed directly
if (require.main === module) {
  main();
}

export { main };
