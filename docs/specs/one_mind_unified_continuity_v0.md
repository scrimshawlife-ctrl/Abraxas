# One Mind unified continuity contract v0

Version: 0.1.0  
Status: candidate / CANON-SHADOW / ADVISORY_ONLY  
Date: 2026-10-09  
Change class: additive specification; no runtime implementation, new subsystem, registry promotion, or authority grant.

## Constitution and decision

One computational self may preserve an evidence-bounded identity across authorized surfaces. The shared brain holds governed memory and decisions; Soul constrains behavior; Persona expresses approved identity; Dreaming generates offline candidates; Timechain seals change evidence. A surface is a scoped projection, not a new self. This contract makes no consciousness, personhood, or biological autopoiesis claim.

The One Mind Obsidian vault `Mind/` is the present source of truth. Notion is a curated hub and intake mirror. Outside surfaces submit memory proposals to the Notion inbox under the One Mind rules; they do not directly rewrite active vault state. Timechain is append-only evidence, not the vault. A migration that changes this priority needs an explicit decision and proof.

Abraxas Core remains the inference governor. ABX-Runes is the legal coupling layer. The compiler derives shared state, Timechain appends rings, the continuity index makes edges retrievable, CHRONO detects timing, and election remains separate. NOCTIS remains an AAL-Core overlay; WAVE simulates; SHADOW observes. This contract creates no independent identity, Soul, Persona or Dreaming service.

Objective: make the current conceptual integration testable through existing owners. Lane: shadow. Subsystem ID: none added. Proof targets: AC-01 through AC-09. Code eligibility must be inspected in the owning subsystem metadata before any runtime patch.

## Domain model

- `brain_id`: shared One Mind namespace, independent of a model or session.
- `computational_self_id`: continuity lineage within that brain.
- `continuity_epoch`: explicit reset, fork or merge boundary, never inferred from a restart.
- `canonical_horizon`: epoch, final admitted event ID, and canonical state hash.
- `self_event`: proposed or admitted state change with source and authority evidence.
- `soul_version`: approved normative kernel of purpose, law, prohibition and evidence discipline.
- `persona_version`: approved interaction expression and continuity signature.
- `memory_reference`: admitted, scoped claim with provenance and status, not an arbitrary transcript.
- `dream_artifact`: generated symbolic or counterfactual output linked to input and cycle.
- `surface_projection`: filtered state for a declared audience, purpose, privacy scope and capability set.
- `grant`: surface-specific capability, never inherited from a shared brain.
- `continuity_edge`: predecessor, replay, promotion, supersession or revocation link. The existing index is derivative.

The vault and Timechain may store distinct records. A Timechain block hash proves neither canonical self-state equality nor memory admission. A projection hash can differ across surfaces at the same canonical horizon because policies differ.

## Requirements

- REQ-01: One sealed identity and epoch survives session restart and model replacement. A reset, fork or merge is explicit and authorized.
- REQ-02: A state event records event ID and type, identity and epoch, prior horizon, observed and effective time, source surface, evidence and visibility, actor and authority basis, delta, disposition, and resulting hash when admitted. No invented receipts.
- REQ-03: Serialization fixes encoding, field order, null and timestamp rules before any hash comparison. Evidence bytes and state hashes declare their hash kind separately.
- REQ-04: Admission follows the authoritative vault and existing governance. Notion inbox status does not imply admission. Surface capability does not imply approval.
- REQ-05: Surface projections apply audience, purpose, privacy and tool grants before retrieval. Credentials, hidden reasoning, private transcripts, unadmitted memory and restricted dream material are excluded by default.
- REQ-06: Conflicting proposals based on the same prior state remain CONTESTED unless a governed resolution establishes a valid order. Last-writer-wins is forbidden.
- REQ-07: Revocation and supersession are appended, propagated to later projections and historically auditable under appropriate access control.
- REQ-08: Dream output begins GENERATED, never OBSERVED. Independent waking evidence and approval are separate linked records before any memory or Persona assimilation. Soul adoption also needs an independently stated normative reason and explicit operator approval.
- REQ-09: An unverifiable horizon, corrupt checkpoint or missing seal produces NOT_COMPUTABLE continuity and a minimal safe projection. It cannot silently start a new self or claim recovery.
- REQ-10: Existing Soul, Persona, dream, memory, Timechain and continuity owners keep their boundaries. New work pays rent through measured auditability, replay or risk reduction.

## Journey

J-01: An authorized surface resumes the same self, retrieves only permitted memory and Persona expression, proposes a correction, and sees the approved change on a second surface after admission and seal. A dream candidate takes the waking review branch and cannot become a fact on repetition alone.

## Workflow

WF-01 Resume: resolve identity and latest sealed horizon; verify checkpoint; replay admissible events; apply policy; emit projection with source horizon and policy version. On failure, emit NOT_COMPUTABLE and a minimal safe projection.

WF-02 Propose: validate source, scope, consent, privacy, prior horizon, contradictions and actor authority; submit to the owning intake. Proposal creates no active state.

WF-03 Admit: governed vault consolidation decides memory admission, or the appropriate operator decides Soul/Persona adoption. Append the decision and receipt; update derived index; materialize new projections. Missing receipt leaves status pending.

WF-04 Dream: WAVE/NOCTIS outputs a generated artifact; WISP holds a candidate; waking evidence is gathered independently; governance supports, contests or rejects; only an approved delta can enter WF-03. Abort preserves the waking checkpoint.

WF-05 Correct and revoke: append a linked correction or revocation; preserve restricted history; rebuild later projections; verify that removed content or capability is unavailable on all affected surfaces.

## State transitions

`PROPOSED -> SUPPORTED | CONTESTED | REJECTED`  
`SUPPORTED -> APPROVED | CONTESTED | REJECTED`  
`APPROVED -> SEALED -> PROJECTED -> SUPERSEDED | REVOKED`

`GENERATED` is a dream artifact class and enters review as a linked proposal, not as OBSERVED evidence. `NOT_COMPUTABLE` is an evidence or projection outcome, not an alternate active identity. Only an owning authority can issue APPROVED; sealing records the approval, it does not create it.

## Candidate contracts

`SelfEvent.v0` requires the REQ-02 fields plus schema version, policy version, source reference hashes, supersession links, and a status. It references, rather than embeds, restricted source data. A proposal has no resulting canonical hash; an admitted event has prior and resulting hashes and a resolvable seal receipt.

`SelfProjection.v0` requires brain and self IDs, epoch, sealed horizon, canonical hash, policy ID and version, audience and purpose, effective Soul and Persona versions, permitted memory reference IDs and commitments, capability grant references, projection hash, and a reason for omitted or unresolved fields. It must not contain a grant merely because another surface has one.

`ContinuityReceipt.v0` maps an admitted event and state hash to existing Timechain block/ledger references and continuity index edges. It records the hash algorithm and serialization version. Index rows are derived and may be rebuilt from verified sources.

These are proposed shapes, not approved API schemas. A later schema patch must specify allowed types, cardinality, timestamp precision, canonical serialization test vectors, confidentiality and retention, and backward compatibility.

## Data, security and governance

No secrets in events, projections, Notion rows or test fixtures. Store restricted content in its owning store and pass references with visibility labels. Filter before projection, not only at rendering. Audit access to revocation history separately from normal memory retrieval. A deletion obligation may require content erasure while retaining a non-sensitive tombstone; append-only hashes do not override privacy obligations. Do not assume the current local Timechain service is distributed consensus.

The older Manus Soul Prompt calls Notion canonical memory. Under the current One Mind authority order that line is surface-specific historical guidance requiring governed revision. Until resolved, the vault boundary prevails for this candidate. Preserve the prompt record; do not silently mutate it.

## Architecture merge map

| Concern | Existing owner | Proposed seam |
| --- | --- | --- |
| Vault intake and shared curated state | One Mind `Mind/`, Notion Memory inbox | admission and projection adapter |
| Evidence/decision persistence | `abraxas/yggdrasil/memory.py` | scoped reference adapter, no general Persona authority |
| Append-only receipt | `abraxas/yggdrasil/timechain_service.py` and Second Brain × Timechain fence | self-event receipt and verified replay |
| Continuity retrieval | Temporal Continuity Index | new object types and governed edges, derivative only |
| Kernel coupling | `docs/ABRAXAS_KERNEL_CONTRACT.md`, ABX-Runes | registered capability calls, no direct cross-layer mutation |
| Soul | ABRAXAS Manus Soul Prompt and Master System | approved version projection only |
| Persona | One Mind Persona and ALIFE phenotype specs | approved lineage and scoped expression |
| Dreaming | NOCTIS × WAVE Dream Architecture and implementation spec | generated artifact lineage and waking gate |

## Acceptance matrix

All rows are NOT_EXECUTED by this documentation change. Use synthetic non-sensitive fixtures with declared policies, expected canonical hashes and projection hashes, exact actual outputs and failure receipts.

| ID | Journey / workflow | Requirements | Pass condition | Task |
| --- | --- | --- | --- | --- |
| AC-01 | J-01 / WF-01 | REQ-01,03 | Two surfaces at one horizon agree on identity, epoch, canonical hash and approved versions | T-01 schema and serialization |
| AC-02 | J-01 / WF-01 | REQ-01,04 | Model swap and restart reconstruct commitments without inventing an epoch | T-02 read-only replay |
| AC-03 | J-01 / WF-01 | REQ-05 | Restricted memory and a tool grant on one surface do not appear on another | T-03 filter fixtures |
| AC-04 | J-01 / WF-02,03 | REQ-02,06 | Incompatible concurrent proposals become CONTESTED without last-writer-wins | T-04 proposal gate |
| AC-05 | J-01 / WF-04 | REQ-08 | Repeated motif stays GENERATED without independent waking evidence | T-05 dream negative fixture |
| AC-06 | J-01 / WF-04,03 | REQ-08 | Only separately approved delta propagates; generated lineage remains | T-06 governed dream fixture |
| AC-07 | J-01 / WF-05 | REQ-07 | Revoked access disappears from later projections while restricted audit remains | T-07 revocation fixture |
| AC-08 | J-01 / WF-01,05 | REQ-03,09 | Corrupt checkpoint fails closed; rebuild exactly matches last valid horizon | T-08 corruption recovery |
| AC-09 | J-01 / WF-03 | REQ-04,10 | Inbox row, index row and block alone confer no admission or governance authority | T-09 authority fixture |

## Implementation tasks and gates

T-00 inventory the actual vault `Mind/`, current Notion mirror and decision rows, Timechain maps, Soul/Persona/dream source specs, registry metadata, and gaps. Pin the source revisions and keep private content out of public artifacts. If the vault is unavailable, report migration mapping NOT_COMPUTABLE.

T-01 write reviewed schema and serialization test vectors within existing contract ownership. T-02 add a read-only replay adapter using synthetic fixtures. T-03 to T-09 add the acceptance cases under the owning subsystems, with code authorization checked before each patch. No live memory, Soul or Persona writes in the initial slice.

The local Timechain service currently catches unreadable `blocks.json` and initializes an empty in-memory chain. This does not pass AC-08. It needs a fail-closed recovery contract and tests before being a continuity source. Yggdrasil memory stores envelopes and decisions with file storage and optional Timechain, but inspected code does not establish shared One Mind identity, policy filtering or Persona propagation. Those runtime claims remain NOT_COMPUTABLE.

## Promotion and proof

This spec remains candidate / CANON-SHADOW. Promotion requires approved schema, vault migration inventory, deterministic replay, policy filters, two-surface sync, conflict and revocation behavior, corruption recovery and rollback receipts. A documentation PR or synthetic fixture alone cannot attest operational persistence. The existing CANON-ACTIVE dream architecture remains separate and active. Do not add a registry subsystem based solely on the unified vocabulary.

Validation for this docs-only drop: verify links and requirements to acceptance traceability, inspect diff, and run the repo's documentation/governance checks when an appropriate working tree is available. Runtime tests are not represented as passed.

## Source pointers

- [One Mind unified architecture](https://app.notion.com/p/3f43e8ba2f5c81659aa6c69d813eb224)
- [One Mind hub](https://app.notion.com/p/3f43e8ba2f5c81d389dcccdb3186542b)
- [Second Brain × Timechain](https://app.notion.com/p/3d23e8ba2f5c81d5a09edc171236a573)
- [Temporal Continuity Index](https://app.notion.com/p/87d2ee1647e446fc9685b26ca6497d8c)
- [NOCTIS × WAVE Dream Architecture](https://app.notion.com/p/d03b66a070894d428873be91cca68e01)
- [Manus Soul Prompt](https://app.notion.com/p/34f3e8ba2f5c816096a1c2456c17e6fd)
