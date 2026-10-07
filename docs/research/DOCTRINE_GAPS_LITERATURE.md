# Literature scan: the two doctrine gaps

A scan of arXiv for prior art on the two open gaps in [`docs/DOCTRINE.md`](../DOCTRINE.md):
**RESEARCH has no representation**, and **settlements are not tracked per artifact**.

This is a scan, not a survey. Its purpose is to find out whether the gaps are ours alone or
whether someone has already published the shape of the answer — and to say plainly where the
literature does not help.

## Method, and its limits

Ten targeted queries against the arXiv API, 36 results screened, 13 selected. Sources are
registered in a citation ledger and the `Sources` block below is generated from it, not typed.

Screening was not clean: the result sets contained genuine noise, excluded by reading rather than
by scoring. From the "levels of evidence" query, a survey of green computing in video games and a
paper on traceable humanities scholarship; from "external validity", a comparison of LLMs against
classical ML for COVID-19 mortality prediction; from "capability maturity", two cybersecurity
maturity-model papers and a nuclear-engineering Bayesian network. None bear on these gaps.

**Every summary below is drawn from the paper's own abstract**, fetched by identifier. Where I
extend a finding to our situation, that extension is mine and is marked as a recommendation rather
than reported as the paper's claim.

## Gap 1 — RESEARCH has no representation

The gap is that nothing distinguishes *methodologically qualified evidence* from ordinary real
data, so every claim sourced from `data_grade="real"` carries FIELD-grade qualification.

### The literature already has a schema for exactly this

The most directly usable finding: evaluation scores should be treated as epistemic claims carrying
three explicit properties — **formality** (human evaluation is stronger evidence than an automated
metric), **scope** (a benchmark result applies to the tested distribution, not universally), and
**validity windows** (results expire as contamination accumulates and distributions shift).[11]

That is a published schema for the missing representation. It also names a property we have no
concept of at all: **expiry**. Our grades are permanent; the literature says a claim's strength
decays, and that a field is needed to record when it does.[11]

**Trust inflation** is the second finding: when signals are aggregated by averaging, aggregate
confidence can substantially exceed the reliability of the weakest signal, and the authors show
top-five models ranked by mean and by weakest-link are completely disjoint on the HELM
leaderboard.[11]

**CORRECTION, added after reading the code rather than grepping it.** My first pass said no
weakest-link rule exists here, on the strength of `grep weakest` returning zero files. That was a
*name-based* check and it was wrong. The concept is present: `promotion_eligible` in
`abraxas/metrics/evidence.py` requires

    all(gates_passed.get(gate, False) for gate in PROMOTION_REQUIRED_GATES)

a conjunction over every required gate — a weakest-link rule under another name — and
`PROMOTION_REQUIRED_GATES` carries a gate for each dimension the composite weights
(`non_redundant`, `forecast_lift`, `ablation_proof`, `stability_verified`, `drift_robust`).

So the accurate statement is narrower and more useful than the one I first wrote. Nothing is
*named* weakest-link, and `data_grade` is a single-label assignment with no aggregation at all, so
claim *strength* is not represented — that part stands. But where strength **is** aggregated, the
weighted `_compute_composite_score` (0.35/0.20/0.25/0.20, threshold 0.70) cannot promote anything
the per-dimension gates have not already permitted, because promotion requires all of them.
The residual exposure is in **ranking**, not promotion: candidate order comes from the mean, and a
mean dilutes a weak dimension differently than a minimum does.

### A score measures less than it is usually read as measuring

Benchmark scores "at best measure performance relative to a specific dataset and learning
problem"; drawing scientific inferences from them requires additional assumptions, which the
authors make explicit as **validity conditions**.[5] Capability attributions are the practice under
critique: linking a theoretical capability to its empirical measurement requires a **nomological
network**, an account of how the constructs relate, not a single score.[3] Benchmarks are
frequently constructed arbitrarily and should themselves be evaluated for construct validity.[4]

Two of these validity types are operational rather than philosophical, which is what makes them
useful to us: **content validity** (whether a measure covers the facets of the capability it claims
to) and **convergent validity** (whether independent measures of the same capability produce stable
rankings).[13] Both are measurable against our own gates.

### The artifact shape is also published

An **evaluation card** — documentation accompanying any study that introduces an evaluation metric
— declaring target properties, **grounding levels**, metric assumptions, validation evidence,
gaming risks, and known failure cases.[9] "Grounding levels" is the closest published analogue to
our LAB/RESEARCH/FIELD split, and the card is per-metric rather than per-repository, which is the
granularity our gap is missing.

**Recommendation (mine, not the papers').** Represent RESEARCH as *claim metadata* rather than as a
missing environment: a formality tier, a scope declaration, a validity window, and a grounding
level, attached to the claim.[11][9] Add a weakest-link rule for any aggregated grade.[11] Adopt
the evaluation-card shape per capability — including `gaming risks` and `known failure cases`,
which we do not record — and define content and convergent validity tests we can actually run
against our own gates.[13][5]

## Gap 2 — settlements are not tracked per artifact

### Verification and validation are the technical/empirical distinction, and someone has formalised the assignment

The strongest match: a framework that quantifies **simulation adequacy** as an explicit,
transparent decision integrating evidence collected from validation activities.[1] Its motivation is
precisely our problem — in the pre-existing frameworks the decision process is "largely implicit
and obscure", and knowledge biases and unreliable judgments can be overlooked.[1]

The distinction it rests on is the one our doctrine makes: **verification** (does the
implementation do what it says) versus **validation** (is it adequate for the purpose). Technical
settlement and empirical settlement, under other names. The lesson we can take is not the Bayesian
network but the *stance*: settlement is an aggregation of cited evidence, not a label someone
types.

### Maturity ladders have precedent, and one caveat about their shape

**Technology Readiness Levels for ML** adapts spacecraft-engineering readiness levels to machine
learning, with explicit attention to where ML differs from traditional software engineering, and
positions the ladder as "a common language for people across the organization".[8] The relevant
property is that readiness is assessed **per technology**, not per release.

### The empirical caution — a measured prediction about our own document

Model cards are the canonical per-artifact structured report: performance in context, intended use
cases, evaluation procedures.[6] But a systematic analysis of **32,111** real model cards on Hugging
Face found that sections covering limitations and evaluation have the **lowest filled-out rates**,
while the training section is consistently filled.[7]

That is directly load-bearing for us. A settlement field written into a template is a section of
exactly the kind that measurement says gets skipped, because recording what you have not settled is
uncomfortable and nothing forces it. **The finding argues for enforcing the field with a test
rather than trusting the template** — which is the same conclusion this repository reached
independently when it mechanised `DOCTRINE.md`'s citations.

**Recommendation (mine).** Track settlements **per capability**, as an explicit aggregation with the
evidence cited for each settlement, in the style of reference [1] and on the ladder logic of [8].
Record it in the artifact's own documentation block [6] — and enforce its presence and its
non-vacuity with a test, because the empirical base says documentation fields decay.[7]

## Cross-cutting: LAB→FIELD, and the self-confirmation guard

### Sim-to-real is a solved-shaped problem, not only a prohibition

Our doctrine forbids reporting LAB output as FIELD evidence. The literature reframes it as a
transfer problem with two named strategy families: **shrink the gap** through model-centric
improvement of simulator fidelity, or **harden the policy** through in-simulation robustness
training and post-deployment adaptation.[10] The authors dissect the "curse of simulation" into
specific gap sources — dynamics, contact modelling, state estimation, numerical solvers.[10]

This is a constructive addition to a doctrine that currently only prohibits. Naming the two
families gives a path by which LAB work *may* reach FIELD standing, under conditions, which is
better than a rule that says only "not this".

### The sharpest available formulation of our self-confirmation guard

> "Attributing model behavior to synthetic training data requires knowing what produced each
> training item before estimating what that item caused."[12]

And the conclusion that matters most for us: **generation provenance is necessary but not
sufficient for behaviour attribution** — provenance defines the candidate causal graph and the
audit units, whereas contributive attribution still requires frozen runs and intervention or
influence evidence.[12] A second line worth adopting almost verbatim: *"Producer and selection
mechanism determine evidentiary meaning; storage location and variable name do not."*[12]

Our doctrine says a loop must not count itself as independent confirmation. This states the same
rule as a research contract, and adds the mechanism by which a loop *could* legitimately close:
frozen runs plus intervention evidence.[12]

### Validity has to survive the worst case

Assessing external validity over worst-case subpopulations guards "against brittle findings that
are invalidated by unanticipated population shifts", rather than validating on the average.[2]
FIELD→RESEARCH promotion by average performance is therefore a known-weak inference.

## Proposed edits to the doctrine document — status

These were written as proposals. Five have since landed, one was rejected, and the status of each is
given with commit SHAs so it is checkable with `git show` rather than taken on trust.

| # | Edit | Status |
| --- | --- | --- |
| 1 | RESEARCH as claim metadata (formality / scope / validity window / grounding) | **LANDED** — `150e257d`, `6961ade8`: `abraxas/evidence/claim_strength.py`. `research` now exists as a grounding level, and **no mechanism produces it yet**. |
| 2 | Weakest-link | **LANDED, retargeted twice** — `43ea1b66`, `7831447d`. See the correction history below. |
| 3 | Expiry on evidence qualification | **LANDED** — `150e257d`: `ClaimStrength.is_expired` with an injectable clock, and an undeclared declaration time treated as expired. |
| 4 | "Producer and selection mechanism determine evidentiary meaning" | **LANDED in its actionable form** — `671b24b5`: ten eager `or "real"` sites, so absence is no longer read as the strongest claim. |
| 5 | LAB→FIELD transferable under conditions | **LANDED as a clarification only** — the prohibition was NOT softened. The two strategies are recorded as ways to make the crossing succeed, not as grounds for reclassifying LAB evidence. See `docs/DOCTRINE.md`. |
| 6 | Settlement records per capability | **LANDED in its cheap form** — `2c19c6f9`, `f0393e7e`: on the EXISTING `EngineSpec`, not a new artefact type. **All ten engines read `unsettled`.** |
| — | A fourth `data_grade` value named `research` | **REJECTED** — see below. |

### Edit 2: the correction history, because the target moved twice

1. **First claim — wrong.** "No weakest-link rule exists here", inferred from `grep weakest` returning
   zero files. That was a *name-based* check, and a name-based check can only ever find the name.
2. **Disproved by reading the code.** `promotion_eligible` in `abraxas/metrics/evidence.py` is
   `all(gates_passed.get(gate, False) for gate in PROMOTION_REQUIRED_GATES)` — a conjunction over
   every required gate, which is weakest-link under another name. A weakest-link rule for
   **promotion** would therefore be redundant.
3. **Retargeted to ranking.** The weighted `_compute_composite_score` (0.35/0.20/0.25/0.20) still
   sets candidate order, and a mean and a minimum rank disjointly by construction.[11]
4. **Retargeted again — and this was the live instance.** `_select_data_grade` in
   `abraxas/tvm/frame.py` ranked grades (`{"real": 3, "derived": 2, "simulated": 1}`) and kept the
   **maximum**, so a frame built from twenty simulated points and one real point was labelled `real`.
   That is trust inflation in running code, and it was pinned by a passing test
   (`tests/test_multi_domain_seedpack.py`). It is now weakest-link — `43ea1b66`.

The pattern worth keeping: each correction came from reading the code, and the first was wrong
*because* it grepped for a name instead of looking for the mechanism.

### Why the fourth `data_grade` value is rejected

A fourth scalar is still a scalar. The gap was never the missing label `research`; it was that claim
*strength* had no representation at all — which is why edit 1 built the representation rather than
adding a value. `research` now exists as a grounding level in
`abraxas/evidence/claim_strength.py`, and nothing produces it yet. That remains an open gap, recorded
rather than papered over.

## What I did NOT find — limitations of this scan

- **No paper defines our three-way empirical / technical / economic settlement taxonomy.** The
  framing appears to be ours (inherited from the second attempt), not a literature standard. There
  is no external witness to cite for the taxonomy itself, only for its empirical and technical
  halves as verification and validation.[1]
- **The medical evidence-grading tradition is not surveyed here.** The `GRADE` query returned zero
  results and the "levels of evidence" query returned unrelated work; GRADE and the Oxford CEBM
  levels are not arXiv-hosted. They are the obvious next place to look for a claim-strength
  hierarchy, and their absence from this scan is a real gap, not a finding that they do not exist.
- **Nothing surfaced on economic settlement.** No query produced work on adoption or payment as an
  evidentiary claim, so the third settlement remains without prior art in this scan.
- **The query set was keyword-driven and my screening was by reading.** A different query set would
  surface a different 36 results; nothing here is a systematic review.

## Sources

[1] https://arxiv.org/abs/2010.03373 — "Predictive Capability Maturity Quantification using Bayesian Network"
[2] https://arxiv.org/abs/2007.02411 — "Assessing External Validity Over Worst-case Subpopulations"
[3] https://arxiv.org/abs/2603.15121 — "Establishing Construct Validity in LLM Capability Benchmarks Requires Nomological Networks"
[4] https://arxiv.org/abs/2503.10694 — "Medical Large Language Model Benchmarks Should Prioritize Construct Validity"
[5] https://arxiv.org/abs/2510.23191 — "The Benchmarking Epistemology: Validity Theory for Evaluating Machine Learning Models"
[6] https://arxiv.org/abs/1810.03993 — "Model Cards for Model Reporting"
[7] https://arxiv.org/abs/2402.05160 — "What's documented in AI? Systematic Analysis of 32K AI Model Cards"
[8] https://arxiv.org/abs/2006.12497 — "Technology Readiness Levels for AI & ML"
[9] https://arxiv.org/abs/2605.04410 — "Evaluation Cards for XAI Metrics"
[10] https://arxiv.org/abs/2511.06465 — "Sim-to-Real Transfer in Deep Reinforcement Learning for Bipedal Locomotion"
[11] https://arxiv.org/abs/2607.26191 — "Position: Evaluation Scores Are Perishable Knowledge Claims"
[12] https://arxiv.org/abs/2610.01378 — "Generation Provenance Before Behavior Attribution: Auditing Synthetic Speech Research Objects"
[13] https://arxiv.org/abs/2603.18019 — "BenchBrowser: Retrieving Evidence for Evaluating Benchmark Validity"
