import crypto from "crypto";
import type { AliveStrainSignal } from "@shared/alive/schema";
import type { AliveMetricProposal } from "@shared/alive/metric-proposals";

function initials(name: string): string {
  const letters = name
    .split(/\s+/)
    .map((part) => part.replace(/[^a-zA-Z]/g, ""))
    .filter(Boolean)
    .map((part) => part[0]);
  return letters.join("").toUpperCase() || "NEW";
}

function proposalId(): string {
  return crypto.randomUUID();
}

function proposedMetricId(workingName: string): string {
  return `CX.${initials(workingName)}`;
}

export function compileStrainProposals(
  signals: AliveStrainSignal[]
): AliveMetricProposal[] {
  const now = new Date().toISOString();

  return signals
    .filter((signal) => signal.suggested_new_dimension)
    .map((signal) => {
      const suggestion = signal.suggested_new_dimension!;
      const workingName = suggestion.working_name;
      const proposedId = proposedMetricId(workingName);

      return {
        proposal_id: proposalId(),
        created_at: now,
        working_name: workingName,
        proposed_metric_id: proposedId,
        candidate_axis: suggestion.candidate_axis,
        measures: suggestion.measures,
        motivation: signal.description,
        required_inputs: ["text"],
        estimation_method: "cue",
        validation_plan: {
          golden_cases: [
            { label: "high", notes: "Representative high-signal examples." },
            { label: "low", notes: "Representative low-signal examples." },
            { label: "ambiguous", notes: "Edge cases that should not trigger." },
          ],
          failure_modes: [],
          promotion_criteria: [
            "Stable distribution over 30d window",
            "Low false-positive rate on golden cases",
            "Documented decision utility",
          ],
        },
        tier_copy: {
          psychonaut: {
            summary: `${workingName}: track when signals show up repeatedly.`,
            prompts: ["Does this pattern show up again and again?"],
          },
          academic: {
            summary: `${workingName}: proposed metric from strain signals.`,
            operational_definition: suggestion.measures,
            failure_modes: [],
          },
          enterprise: {
            summary: `${workingName}: emerging metric candidate from strain detection.`,
            decision_uses: ["Pilot in shadow mode", "Review weekly distributions"],
            business_risk_notes: ["Unvalidated until shadow window completes"],
          },
        },
      } satisfies AliveMetricProposal;
    });
}
