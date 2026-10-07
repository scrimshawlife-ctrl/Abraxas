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

**This document is machine-checked.** Every citation below is verified by
`tests/test_doctrine_citations.py`, which resolves each `path:line`, requires any block introduced
as *verbatim* to appear in the source, and asserts that the surfaces in the table above stay
absent. Two conventions make that possible, and both are load-bearing:

- A fenced block counts as a **quotation** only when the paragraph introducing it contains the word
  "verbatim". Otherwise it is illustrative — the flywheel diagram — and is not matched against the
  source, because it does not claim to be from it.
- A row of the table above ending in `no` declares its paths **absent**. If one is ever added, the
  guard fails and this table has to be updated.

The point of checking it: prose has no resolver, so a sentence about the code can contradict the
code indefinitely. This document tries to be the kind that cannot.

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

## Data grades and claim strength

The mapping above says `data_grade` is where LAB and FIELD evidence are distinguished. Two properties
of how it behaves are doctrine rather than implementation detail, because both have been violated in
this repository's history.

**An undeclared grade supports no claim.** The grades are `real`, `derived`, `simulated` and
`undeclared` — the last defined at `abraxas/evidence/data_grade.py:34` and deliberately the weakest
member of every aggregate. A packet that declares nothing is `undeclared`, never `real`: absence is
not a licence to claim, and it is never upgraded by its neighbours. The model defaults are
`UNDECLARED` (for example `abraxas/metric_extractors/base.py:21`), and an unrecognised value
normalises to `undeclared` rather than being guessed at, so a typo cannot become the strongest grade.

**Aggregation is weakest-link.** An aggregate is only as strong as its weakest member
(`abraxas/evidence/data_grade.py:56`), applied where a frame's grade is decided
(`abraxas/tvm/frame.py:302`). The opposite rule held until recently and is worth remembering because
it was wrong in a quiet way: a frame's grade was the *highest* among its points, so one `real`
observation among twenty `simulated` ones labelled the whole frame `real`.

**Only `real` declares an observation.** `derived` is computed from other data and carries no
independent observation of its own; `simulated` is a LAB artefact; `undeclared` claims nothing at all.

### Claim strength

A grade says where data came from. It does not say how strongly the claim built on that data is
supported, how far it reaches, or whether it is still true. Those are three separate properties,
declared rather than inferred, on `abraxas/evidence/claim_strength.py:41`:

| Property | What it declares |
| --- | --- |
| `formality` | how the claim was assessed — `assessed`, `verified` or `automated` |
| `scope` | what the claim covers; may not be blank |
| `validity_days` | how long the claim lasts before it expires |

Expiry is evaluated against an **injected** clock, and an undeclared declaration time is treated as
**expired** — the same rule as above, one level up: not recording when a claim was made is not a
licence to assume it is fresh. A claim strength attaches to a source packet as an optional
declaration (`abraxas/sources/packets.py:26`) and is **excluded from packet identity**
(`abraxas/sources/packets.py:29`): declared strength is metadata *about* the claim, not part of the
observation — the same identity-versus-metadata rule this repository applied to the rune hash and the
lexicon content fingerprint.

### LAB output reaching FIELD standing

The prohibition above stands **unchanged**: simulator or LAB output may never be *reported* as FIELD
or physical evidence. What follows is not an exception to it.

Two engineering strategies make a LAB-trained result **survive** the field, rather than licensing it
to be **called** field evidence: improve the simulator's physical fidelity, or harden the policy with
in-simulation robustness training and verify on the real device. Both are ways to make the crossing
succeed. Neither changes which environment the evidence came from, and neither permits a LAB result
to be described as a physical one.

## The evidence contract has exactly one home

Every engine reports through one shape: the evidence envelope. That type *is* the architecture boundary —
Abraxas owns arbitration, engines own reasoning — and it must exist once.

A duplicate copy is not a style problem. If the type is defined twice, a consumer that checks "is this
an evidence envelope?" using one copy receives a real engine's output and is told **no**. That happened
here: the package-level copy and the contract copy were different objects diverging by a single field,
and a real engine returned the copy that the package-level check rejected. A duplicate is also how a
weaker variant survives: one copy of `Decision` was missing `REJECT`, the value the coordination layer
uses to fail closed, so a consumer importing the weaker copy could not express a rejection at all.

So the rule is: one home per contract type, the package re-exports rather than redefines, and a guard
asserts **object identity** between the two paths — not equality, not structural similarity.
`abraxas.evidence.EvidenceEnvelope` and `abraxas.evidence.contract.EvidenceEnvelope` must be the same
object, and a newly duplicated type must be catchable by adding one row to a table rather than writing
another bespoke test.

**Engine output must satisfy that one type.** An engine that returns a plain dictionary where the
interface declares an envelope is not conforming, and a guard checking only that a class inherits a base
class will not notice — that is how such a return passed every test in this repository. The check that
catches it inspects what `produce_evidence` actually returns.

### Metadata stays on the artifact and out of its identity

An envelope carries fields that describe the artifact rather than its content: the `timestamp` it was
created at, its `evidence_id`, and its `schema_version`. These are legitimate metadata and belong on the
record — a consumer needs to know when a record was made and what format it is in.

They are excluded from content and identity comparison, under a named constant, so that two runs over
identical input compare equal. This is the same identity-versus-metadata rule applied to the rune hash,
the lexicon content fingerprint, and the packet hash.

The failure mode to avoid is the opposite fix. Deleting a field so that a comparison passes destroys
information and can break behaviour elsewhere: `schema_version` was once removed to resolve exactly this
kind of divergence, and because the schema migrator read that field to decide whether migration was
needed — and wrote it so a second migration would be a no-op — its removal made migration silently
non-idempotent while the whole test suite stayed green. When a field is metadata, exclude it from the
comparison and say why; do not remove it. And when you conclude a field is unused, search for the exact
field name rather than for the class that owns it.

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
