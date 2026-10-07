# Abraxas Doctrine

The durable principles that decide what a claim may be called. This document exists because the
repository already enforces most of them in code and in scattered documents, but had no single
place stating the doctrine itself — so the reasoning had to be re-derived in every review.

## Status and provenance

**OBSERVED** — harvested from the second attempt (`Abraxas-v2.0`) and adapted to this repository.
That checkout shares zero commits with this one; nothing here is a merge.

**What was deliberately NOT ported.** `Abraxas-v2.0` carries `ADR-0017` (Bounded Activation
Policy), `ADR-0018` (Artifact Classification) and `ADR-0019` (Agent Doctrine and Skill Routing).
They were read in full and **not** copied, because every one of them cites surfaces that do not
exist here:

| Cited in the v2.0 ADRs | Present here? |
| --- | --- |
| `core/governance/activation_policy.py` | no |
| activation lanes `LOCAL_DEV` / `SANDBOX` / `INTERNAL_CANARY` / `EXTERNAL_PRODUCTION` | no |
| `core/canonical/artifact_classification.py` | no |
| `SKILLS.md`, `abraxas-master-loop-workflow`, `abraxas-jamon-agentic-workflow` | no |
| `scripts/governance/validate_agent_doctrine.py`, `tests/test_agent_doctrine_validation.py` | no |

Porting them verbatim would have put six non-existent surfaces into this repository's
documentation, which is worse than having no document: a doc that cites a missing module reads as
authority while being unverifiable. What was harvested instead is the **doctrine**, restated
against the mechanisms that actually exist here — with gaps marked as gaps.

## The three settlements

Every capability worth building is seeking three separate settlements. They are independent, and
conflating them is the most common way a project convinces itself of something untrue.

| Settlement | The question it answers | What evidences it |
| --- | --- | --- |
| **Empirical** | Is the claim supported by evidence? | declared forecast, falsification criteria, resolved observation, calibration |
| **Technical** | Does the implementation reliably meet specification? | determinism, schema validity, tests, replayability, provenance, canonical artifacts |
| **Economic** | Does it produce consequences someone adopts or pays for? | adoption, payment, operational use |

Two non-implication rules carry the weight:

1. **Technical settlement never implies empirical settlement.** A green suite, a schema-valid
   artifact and a replayable run say the thing works as specified. They say nothing about whether
   what it claims is true. This is the failure mode most available to a repository like this one,
   because technical settlement is the one that can be automated.
2. **Economic settlement is not causal or scientific validity.** Commercial success is not
   evidence of correctness. A thing can be adopted because it is cheap, or novel, or marketed.

## Evidence environments: LAB, RESEARCH, FIELD

Evidence is qualified by the environment it came from. These are not quality grades — they are
different kinds of claim.

| Environment | What it is | What it may claim |
| --- | --- | --- |
| **LAB** | synthetic fixtures, controlled simulation | that a method behaves as designed under controlled conditions |
| **RESEARCH** | methodologically qualified evidence | that a method holds under qualified study design |
| **FIELD** | commercial / operational observation | that something was observed to happen, in the world, unprompted |

**FIELD evidence generates hypotheses; it does not automatically become scientific validation.**
Observation in the field is where questions come from, not where answers are settled.

The intended flywheel:

```
FIELD → hypothesis → LAB → RESEARCH → validated method → FIELD
```

**The guard that makes the flywheel honest:** ABX-mediated provenance prevents the loop from
counting itself as independent confirmation. A system that generates a hypothesis from its own
field observation, tests it in its own lab, and then cites its own test as confirmation of its
own hypothesis has confirmed nothing. The provenance must show the loop is a loop.

## How this maps onto this repository

Each environment's mechanism here, or **GAP** where there is none. Mapping is asserted only where
a mechanism exists and was read.

| Doctrine | Mechanism in this repository | Status |
| --- | --- | --- |
| LAB | `data_grade="simulated"`, gated behind `--allow-simulated` — `abraxas/metric_extractors/base.py:20`, `abraxas/cli/main.py:90` | OBSERVED |
| FIELD | `data_grade="real"` (the default) | OBSERVED |
| RESEARCH | nearest surfaces are `docs/acceptance/ABRAXAS_ACCEPTANCE_SPEC_v1.md` and `docs/VALIDATION_AND_ATTESTATION.md`, but **neither declares methodological qualification of evidence** | **GAP** |

Two adjacent concepts that are *not* this doctrine — recorded so they are not mistaken for
coverage:

- `evidence_tier` (`canonical` / `staging` / `experimental`) — `abraxas/runes/models.py:23`. This
  is **artifact maturity**, a different axis from the environment evidence came from.
- `SHADOW` mode — `docs/EMERGENT_METRICS.md:10`. This is **lifecycle authority** (observe-only,
  no state influence), also a different axis.

## Prohibited moves

These are the moves the doctrine exists to prevent. Each is grounded in a mechanism or invariant
already present, so none of them is aspirational:

1. **Simulator or LAB output presented as FIELD / physical evidence.** The separation is real in
   code (`data_grade`, `--allow-simulated`); the prohibition is that a LAB result may never be
   *reported* as a physical one. Measured on device or not at all.
2. **A `planned` surface presented as available.** Enforced fail-closed in
   `abraxas/yggdrasil/registry.py` (`is_engine_available`; arbitration returns `REJECT`) and
   reinforced by `docs/ENGINE_TOPOLOGY.md`'s live/planned column. The invariant verbatim, from
   `abraxas/engines/manifest.py:21` and identically at `abraxas/yggdrasil/registry.py:32` — the
   doubled backticks are literal in the source:

   ```
   A ``planned`` engine must never be presented as available.
   ```

   *Addressable is not available.*
3. **Technical settlement claimed as empirical settlement.** See the non-implication rules above.
4. **A provenance loop counted as independent confirmation of itself.** The guard on the flywheel.
5. **Adoption or market outcome claimed as causal or scientific validity.**

## Relationship to doctrine already in this repository

This document does not replace the existing statements; it names the family they belong to and
points at them.

- `docs/EMERGENT_METRICS.md:9-12` already states three laws in the same spirit — *"Emergence ≠
  Promotion"*, *"Shadow-Only Until Proven"*, *"Evidence Beats Symbolism"*. Those are the
  **metric-lifecycle face** of the three settlements: a metric may be proposed by the system, but
  only evidenced promotion makes it real.
- `docs/ABRAXAS_KERNEL_CONTRACT.md` §5 carries the gate list for emergent metrics (SHADOW →
  promotion requires evidence bundle + reproducible evaluation).
- `docs/ENGINE_TOPOLOGY.md` carries the live/planned invariant that prohibition 3 enforces.
- `docs/VALIDATION_AND_ATTESTATION.md` covers attestation mechanics.

Where this document and those disagree, they are wrong and this one is not obviously right --
reconcile them explicitly rather than assuming precedence.

## Open gaps

- **RESEARCH has no representation.** There is no mechanism that distinguishes methodologically
  qualified evidence from ordinary real data. Until there is, every claim sourced from
  `data_grade="real"` carries FIELD-grade qualification and nothing stronger, and no one should
  read more into it.
- The three settlements are not tracked per artifact. `data_grade` records where data came from;
  nothing records which settlements a given capability has reached. That is the natural next
  step if this doctrine is to be enforced rather than merely stated.
