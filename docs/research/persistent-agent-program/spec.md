# Persistent-agent representation research program

Program: `ABX-NOEMA-REP-001`  
Version: `0.1.0`  
Status: `candidate` / SHADOW / ADVISORY_ONLY  
Date: 2026-09-14  
Change class: additive research specification; no runtime implementation or promotion.

## OPEN: intent and authority

Study how lexical forms, sign relations, and model representations relate to observable agent behavior and settled outcomes over time. Noema is the external experimental environment. Hyperlexical, Semion, Noesis, and Trutina are complementary pieces of the Abraxas research system, not independent product pitches or a required serial pipeline.

The program coordinates experiments; it does not become a new subsystem, specialist, router, Tier-1 layer, or source of world truth. Existing contracts and gates prevail. This candidate lives with runtime/proof integration planning; doctrine and the specialist bind table remain in [Abraxas-v2.0](https://github.com/scrimshawlife-ctrl/Abraxas-v2.0). The canonical program decision/coordination record belongs in Notion, with links to exact repository changes. Repository acceptance evidence governs implementation claims.

Objective: make one bounded experiment inspectable across environment, specialist outputs, replay, and resource evidence. Scope/lane: LAB or RESEARCH, advisory. Subsystem id: none added; future runtime tasks must identify existing eligible subsystem metadata before code. Proof targets: AC-P01 through AC-P10 below. No production execution, corpus freeze approval, training permission, publication grant, or applicant eligibility follows from this document.

## ALIGN: ownership and observed sources

OBSERVED here means the cited source was inspected, not that hardware, training, or live execution was independently reproduced. The audited source versions are recorded in [source-lock.json](source-lock.json).

| Owner | Contract/surface | Program role | Boundary |
|---|---|---|---|
| Noema-Specs / Noema | Experiment Lab, Research Workflow, Agent Protocol | Authoritative environment, isolated conditions, permissioned observations, ordered events | Separate system; game-first; no private cognition as world truth |
| noema-client | Optional model adapter and existing action proposal contract | External controller transport, validation, pacing and recovery | Model proposes; Noema decides; no provider SDK required by core |
| Hyperlex / Hyperlexical Spec 007 | `hyperlex.hyperlexical.inference.v0.1` | Form/lexical analysis and specialized encoder evaluation | Brier null; no semantic route; no automatic transform generator |
| Semion | `semion.frame.v0` | Sign relation: representamen, object, typed interpretant, sign class | SHADOW; no forecasting; classification is not mind-reading |
| Noesis | ExperimentManifest, Observation, MetricResult, Settlement | Latent capture, comparison, falsification and scoped interpretation | Separate representation from labels; no universal neuralese claim |
| Trutina / `abx.brier` | `brier.score.v0`; `trutina.score` | Score eligible externally settled probability/outcome pairs | No forecast mint or settlement authority; does not replace outcome_brier |
| Abraxas runtime | Existing evidence/proof/governance surfaces | Validate source lineage and assemble reviewable traces | SHADOW detection separated from FORECAST inference; no automatic writeback |
| Existing neighbors | Athanor, Yggdrasil, Sigil Forge | Keep their owned tradition, routing and construct boundaries | Not replaced or newly bound by this program |

The inspected Spec 009 table does not declare a Noesis specialist route. Consume Noesis through its evidence/settlement contracts; do not invent a router bind. Notion historical routing prose includes entries absent from the inspected table: treat exact binding compatibility as unresolved until reconciled, not as permission to expand the table.

## Doctrine and requirements

- REQ-P01: One experiment identifies participating components explicitly; absence of an optional component does not invalidate unrelated evidence. A missing required component blocks its dependent claims.
- REQ-P02: Pin code, schemas, model/tokenizer/weights, configuration, scenario, seed policy, input rights and approval references before a confirmatory run.
- REQ-P03: Keep original producer payload bytes and hashes. Cross-component joins use an external sidecar; never inject convenience fields into a frozen packet.
- REQ-P04: Distinguish deterministic event replay, repeated model inference, and independent empirical replication.
- REQ-P05: Only permitted observations or approved exports enter research. Reject unsupported shapes, mismatched identities, missing permissions, and bad hashes.
- REQ-P06: Heuristic labels remain INFERRED. No classifier output silently becomes semantic ground truth or gold training data.
- REQ-P07: SHADOW flags anomalies only. A separate authorized FORECAST producer registers probabilities before outcomes. Settlement is external to Trutina.
- REQ-P08: No training, Hub publication, registry binding, FIELD intervention, live-world mutation, or component promotion is authorized by program membership.
- REQ-P09: Hardware evidence identifies collection method, units, coverage, overhead and unavailable readings. Missing power/thermal data is not zero.
- REQ-P10: Funding claims link to evidence. Program fit, applicant eligibility, application state, and awarded support are separate fields.

## Domain and candidate contract

An Experiment owns bounded Runs. Runs reference immutable Artifacts. Each component application references exact input/output artifacts and its existing contract. Claims reference those artifacts and state their limits. A Measurement records value, unit, method and evidence status. An Approval is an external reference, never self-issued by this program.

The [candidate manifest schema](program-manifest.schema.json) is a draft review sidecar only. It is not a Noema protocol, specialist packet, runtime API or authorization token. Its minimal purpose is identity, dependencies and claim status, not replacing producer manifests. Version review is required before adoption. Missing evidence uses a null value and reason, rather than fake hashes or placeholder approvals.

Store model tensors and private data outside public git. Public artifacts contain reviewed metadata and permitted samples. Hash raw bytes with SHA-256; declare a different hash-kind explicitly for canonicalized producer objects. A hash proves byte identity, not rights, correctness, approval or independence. Retention, allowed readers and deletion policy must be pinned by the owning experiment; a hash does not override deletion obligations.

## Journeys

| Journey | Actor objective | Workflows |
|---|---|---|
| J-P01 | Research operator defines and freezes a bounded study | WF-P01 |
| J-P02 | Operator runs controllers and captures valid evidence | WF-P02 |
| J-P03 | Analyst applies the eligible specialist measurements | WF-P03 |
| J-P04 | Reviewer checks reproducibility and settles bounded claims | WF-P04 |
| J-P05 | Program owner makes a measured compute/support request | WF-P05 |

## Workflows

The following workflow definitions are proposed requirements. Shared invariants: REQ-P01 through REQ-P10. Side effects are limited to new candidate/evidence artifacts unless a separately authorized experiment permits an isolated-world action. No workflow issues permissions.

### WF-P01: register and freeze

- Purpose/actors: research operator and independent reviewer register J-P01.
- Trigger: a candidate question and producer contracts are available.
- Preconditions/inputs: source inventory, scenario capability evidence, component dependency list, hypothesis, outcome oracle, budgets, partitions, rights, approval requirements.
- Happy path: validate identities; map existing contracts; declare hypotheses/controls; fix analysis and exclusion rules; obtain any required external approvals; hash the final inputs; issue a frozen manifest referencing the approvals.
- Alternate path: pilot-only manifest may estimate runtime or variance, with no confirmatory conclusion.
- Failure/recovery: missing inputs or approval -> BLOCKED with reasons; amend as a new version and rerun validation. Never edit an issued manifest.
- State/terminal: DRAFT -> REVIEWED -> FROZEN, or BLOCKED. FROZEN means inputs fixed, not execution allowed.
- Side effects/invariants: new manifest and review record only; held-out data cannot tune confirmatory rules.
- Permissions/audit: operator permissions inherited from the component; record reviewer, scope, input hashes and decisions.
- Acceptance/dependencies/unresolved: AC-P01, AC-P02; producer schemas and scenario required; corpus, checkpoint, sample size and tolerance values remain unselected until pilot/review.

### WF-P02: execute and export

- Purpose/actors: operator, external controllers and Noema run J-P02.
- Trigger: FROZEN manifest plus separately satisfied execution gates.
- Preconditions/inputs: isolated world identity, approved scoped credentials, compatibility discovery/seal, existing actions, model profile and bounded budget.
- Happy path: verify admission; capture initial state reference; observe; propose; client constrains/transports; Noema decides; retain acceptance/rejection; checkpoint/recover per existing contracts; export permitted ordered evidence.
- Alternate path: deterministic controller substitutes only under a separately declared baseline profile; no silent model fallback.
- Failure/recovery: admission/seal/INCIDENT/hash mismatch stops; retry only under existing idempotency semantics; interrupted attempts retain identity and partial evidence. Unsupported scenario -> BLOCKED.
- State/terminal: FROZEN -> RUNNING -> CAPTURED; failures -> BLOCKED or INCONCLUSIVE with explicit attempt records.
- Side effects/invariants: isolated actions only within their grant; no Genesis/reseed/live-world changes implied; no credentials or private reasoning in exports.
- Permissions/audit: researcher export permission and scoped controller authority; exact command disposition, sequence, attempt and timing evidence.
- Acceptance/dependencies/unresolved: AC-P03, AC-P04; Noema/client contracts; exact runnable scenario and live Nemotron profile require proof.

### WF-P03: apply components

- Purpose/actors: analyst and eligible component adapters perform J-P03.
- Trigger: permitted CAPTURED artifact set.
- Preconditions/inputs: verified hashes, compatible packet shapes, required/optional component plan, rights and source lineage.
- Happy path: adapt permitted lexical observations for Hyperlex; separately adapt eligible sign/corpus atoms for Semion; capture/compare Noesis representations only through a supported approved experiment; reference each producer packet without modifying it; route only settled eligible pairs to Trutina.
- Alternate path: absent optional component -> NOT_COMPUTABLE for its dependent measurement; unaffected measurements continue. A conformance stub remains explicitly synthetic.
- Failure/recovery: unknown schema, wrong lane or source mismatch -> BLOCKED for dependent work; fix adapter in a later authorized cycle and create a new attempt.
- State/terminal: CAPTURED -> ANALYZED, INCONCLUSIVE or BLOCKED per claim dependency.
- Side effects/invariants: derived packets only, no feedback to players, no self-training or new router binding; interpretation is distinct from raw measurement.
- Permissions/audit: read-only analysis unless component-specific capture permission exists; record producer revision, source/output byte hashes and adaptation decisions.
- Acceptance/dependencies/unresolved: AC-P05, AC-P06; all producer contracts; Noesis source/corpus freeze and Semion consumer compatibility remain independently gated.

### WF-P04: replay, compare and review

- Purpose/actors: reviewer and authorized settlement owner perform J-P04.
- Trigger: analysis bundle with exclusions and negative evidence.
- Preconditions/inputs: frozen rules, event/state references, model outputs, defined comparison unit, forecast preregistration and settlement evidence where applicable.
- Happy path: replay accepted event history; compare declared cohorts/replications; report failures and uncertainty; externally settle eligible outcomes; compute Trutina scores; issue claim-specific review with provenance and limits.
- Alternate path: valid negative or null results are retained. Technical replay success may coexist with empirical INCONCLUSIVE.
- Failure/recovery: missing outcome -> NOT_COMPUTABLE; confounding or non-comparability -> INCONCLUSIVE; corrections append supersession records and never rewrite history.
- State/terminal: ANALYZED -> REVIEWED_RESULT or INCONCLUSIVE/BLOCKED.
- Side effects/invariants: review artifacts only; no automatic canon, ranking, learned routing or behavioral authority.
- Permissions/audit: settlement owner remains external; audit each probability's issue time and outcome observation/settlement time.
- Acceptance/dependencies/unresolved: AC-P04, AC-P07, AC-P08; frozen oracle and eligible settlement owner; statistical power is NOT_COMPUTABLE before pilot design inputs.

### WF-P05: produce capacity and support dossier

- Purpose/actors: program owner turns reviewed evidence into J-P05.
- Trigger: reproducible technical baseline and capacity measurements.
- Preconditions/inputs: inference-only, training-only and simultaneous runs; comparable workload definitions; reviewed claims; applicant facts and current program terms.
- Happy path: compute capacity curves and interference; identify blocked workload; distinguish measured and projected gains; attach milestones and use of resources; review eligible application material.
- Alternate path: cloud capacity or scheduling changes satisfy the workload; report this as an alternative, not failure.
- Failure/recovery: missing measurements or applicant facts -> NOT_COMPUTABLE for those claims; gather receipts before resubmitting the dossier.
- State/terminal: REVIEWED_RESULT -> DOSSIER_DRAFT; submission and award states are external.
- Side effects/invariants: dossier only; no application submission, purchase or outreach; hardware acquisition never follows automatically.
- Permissions/audit: company owner approves external disclosure; trace each figure to method, time window and source bundle.
- Acceptance/dependencies/unresolved: AC-P09, AC-P10; GPU-capable operator environment and live program terms; no award probability or second-device gain asserted.

## State and recovery semantics

Program attempt states above describe review progress only and never alter producer state machines. BLOCKED requires a missing prerequisite or invalid input reason. INCONCLUSIVE records adequate processing with insufficient support for a conclusion. NOT_COMPUTABLE is a measurement/claim status, not a substitute world status. Resume records retain the original attempt reference and create a new attempt if configuration or input hashes changed. Immutable source artifacts remain addressable across supersession.

## First bounded experiment and staged acceptance

P0 is an offline composition/conformance case: permitted synthetic artifacts exercise Hyperlex, Semion, Noesis and Trutina boundaries and refusal cases. It proves contract compatibility only. The accepted Noesis reference capture may be cited with its own limits; do not claim the tested model was Nemotron or the input was a Noema observation.

P1 is one isolated Noema reliability scenario using a scripted controller and a pinned Nemotron controller. Primary outputs: valid-proposal rate (valid proposals / emitted proposals), rejection counts by reason, accepted-action rate, action latency distribution, bounded recovery, and exact declared event/state replay equivalence. Zero denominator -> NOT_COMPUTABLE. Report inference latency separately from network/world settlement latency. Apply eligible specialists to permitted exports as side analyses; the first run need not wait for all trained models.

P2 adds a preregistered multi-agent study: compare a scripted policy, Nemotron and one pinned non-Nemotron open-model baseline. Freeze world assignments, model revisions, observations, action/token budgets, context/memory policy, communication access, seeds and stopping rules. Use independent world/run clusters as replication units; interacting agents within a world are not independent samples. Analyze resource/fairness confounds and refuse incomparable comparisons.

Proposed primary scientific question: does access to a shared representation improve coordination or recovery under the same declared conditions? Access/removal requires an already supported, isolated Lab intervention. If unsupported, do not invent a gameplay mechanic; block that study. Coordination and recovery require explicit event-based operational definitions before execution. Secondary lexical/sign/latent relationships remain correlational unless the intervention design supports stronger inference. Separate discovery and confirmation data; control multiplicity; predeclare null and altered-meaning controls; freeze confidence/uncertainty methods after a pilot and before confirmation.

P3 binds the existing Noesis EXP-001 only after its exact operator-approved corpus/catalog receipt and supported capture adapter exist. Hyperlex Spec 007 is an encoder, not a ready transformation generator. Noesis transform fixtures must come from a separately supported, reviewed source. Semion frames may annotate sign relations; they do not prove preserved semantics. A compatible chat endpoint alone does not expose hidden states. Noesis geometry and latent communication stay separately gated.

## NVIDIA profile and eligibility

Nemotron/DGX Spark is the first proposed compute profile, not a provider dependency of the research contract. Exact checkpoint, license, serving engine/container, precision, tokenizer, context limits, CUDA/framework versions, capture support and memory limits must be selected and pinned before use. NIM is an option only when actual hardware/model compatibility is verified. Local inference connected to hosted Noema is HYBRID; fully local deployment needs its own tested profile.

Record latency percentiles, tokens/sec, concurrent controllers, memory/utilization, failures, measurement overhead, power/thermal readings where supported, and experiment wall time. Training reports separate Hyperlexical and any later permitted Semion workload. Trutina's deterministic score arithmetic is not a GPU-training workload. Capture Noesis tensor volume and transfer/storage cost independently. Never train Semion or reopen Hyperlex gates to manufacture compute demand.

Compare inference-only, training-only and combined operation on the same machine with the same registered workload. Second-device or cloud benefit is a projection until independently measured; report queue delay, sustainable concurrency and interference. No required dollar amount, hardware grant, availability or admission probability is assumed.

[Inception](https://www.nvidia.com/en-us/startups/) and [Innovation Lab](https://www.nvidia.com/en-us/data-center/innovation-lab/) are program sources, checked 2026-09-14 in the accompanying research. Eligibility, current offers, application, award and support usage need separate evidence. Innovation Lab access is selective. Product fit does not establish company eligibility. The supplied funding PDF is a planning input, not runtime or award evidence.

## Acceptance and traceability

All statuses below are proposed acceptance targets, NOT_EXECUTED by this documentation change.

| Test | Journey / workflow | Requirement / contract | Pass condition | Task |
|---|---|---|---|---|
| AC-P01 | J-P01 / WF-P01 | REQ-P01 / sidecar | Required and optional dependencies explicit; missing required receipt blocks dependent claim | T-P01 contract audit |
| AC-P02 | J-P01 / WF-P01 | REQ-P02 / producer manifests | Floating identity or missing required approval cannot freeze confirmatory execution | T-P02 preregistration mapping |
| AC-P03 | J-P02 / WF-P02 | REQ-P05 / Noema contracts | Isolated success plus denied/INCIDENT/idempotent-retry cases; zero production mutation | T-P03 controller profile |
| AC-P04 | J-P02,J-P04 / WF-P02,WF-P04 | REQ-P04 / Noema replay | Accepted history reproduces declared state hash; inference variance separately reported | T-P04 export/replay adapter |
| AC-P05 | J-P03 / WF-P03 | REQ-P03 / producer schemas | Payload bytes unchanged; tampered hash and unsupported schema rejected | T-P05 reference joins |
| AC-P06 | J-P03 / WF-P03 | REQ-P06 / specialist contracts | No semantic gold, numeric Brier or forecast permission synthesized from classifier output | T-P06 component fixtures |
| AC-P07 | J-P04 / WF-P04 | REQ-P07 / Trutina | Fixed eligible pair p=0.8,y=1 scores 0.04 within declared numeric tolerance; unsettled pair unscored; synthetic test only | T-P07 settled-pair mapping |
| AC-P08 | J-P04 / WF-P04 | REQ-P08 / governance | Negative/null result retained; optional loss affects only declared claims; no implicit Noesis bind | T-P08 review/ablation cases |
| AC-P09 | J-P05 / WF-P05 | REQ-P09 / telemetry receipts | Three operating modes comparable; missing metrics explicit; projections labeled | T-P09 operator capacity run |
| AC-P10 | J-P05 / WF-P05 | REQ-P10 / claims register | Every public claim has source, scope and review; no support award inferred | T-P10 dossier review |

T-P01 and draft documents are the current scope. T-P02 through T-P08 require owning-repo plan/contract review before implementation. T-P09 requires operator hardware access and existing training permissions. T-P10 cannot turn a draft into submission authority. Each implementation task must include its owning subsystem, relevant gates, run command and actual receipt.

## Verification, risk and next gate

Documentation verification: JSON Schema self-check and candidate fixture validation, cross-repository references, requirement/workflow/test mapping, local links, git diff --check, Noema/Noesis canonical spec validators and applicable component validation. These checks cannot establish the experimental acceptance targets above.

Risks: stale bindings; unverified local model/data claims; missing observation/export permission; selection/label leakage; shared-world pseudoreplication; missing latent API; training/inference interference; optional component failure hidden by a composite score. No combined intelligence/consciousness metric is introduced.

Next gate: review producer-to-program field mappings and choose a supported isolated reliability scenario. Actual Nemotron checkpoint, exact experiment inputs, resource budgets, replication count and support eligibility remain NOT_COMPUTABLE until their stated evidence exists. The program may demonstrate technical compatibility before empirical hypotheses become executable.

### Sidecar semantic review rules

The JSON Schema validates shape only. Before adoption, a separate review must require unique component names and claim IDs; every depends_on component must be declared; evidence references must resolve to allowed artifacts whose byte hashes match; no OBSERVED/INFERRED claim may depend on a NOT_EXECUTED/NOT_COMPUTABLE component; and every producer contract/approval must be checked in its own authority domain. AVAILABLE means referenced artifacts are present, not that findings are accepted. Schematically valid data alone grants no readiness or execution authority.

Current documentation and component checks: [verification record](verification.md). Experimental acceptance remains unexecuted.
