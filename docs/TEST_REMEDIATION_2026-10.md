# Test Debt Remediation — session record, 2026-10-06

**Result: 134 → 3 failures. 131 closed. Zero regressions. Zero policy/threshold values moved.**

| | before | after |
|---|---|---|
| failures | 134 | **3** |
| passing | 3,167 | **3,338** |
| diff | — | 122 files, +1,950 / −335 |
| commits | — | 44 |

Ratchet: `scripts/test_ratchet.sh` → `BASELINE_FAILURES=3` (verified: `OK: within baseline`).

Full per-failure detail, every diagnosis, every revert and every ruling lives in
`docs/TEST_DEBT.md`. This file is the session summary and the transferable conclusions.

---

## 1. The remaining 3 — decisions, not work

| Test | Decision |
|---|---|
| `test_non_censorship_invariant` | Scan patterns match VOCABULARY, not intent. 244 violations incl. the firewall module itself. Needs redesign; also exclude generated bundles. |
| `test_epp_builds_ranked_proposals` | `TIGHTEN` (risk >= 0.6) and `LOOSEN` (risk <= 0.3) cannot both fire under one global composite. Needs a second low-risk fixture. |
| `test_memetic_claim_runes` | **Recommended to stay red.** Jaccard 0.21 vs expected 0.42; passing means redesigning a similarity metric to hit a number. |

## 2. Defect taxonomy — what the 131 actually were

Not one was a logic bug in the ordinary sense.

| Class | Instances |
|---|---|
| **Cross-subsystem leak** | a webpanel agency-gate code (`agency_off`) reported as a *calibration drift* failure mode; a 244-item scan flagging the firewall itself |
| **One value, two consumers** | one term list serving base-word extraction AND phrase-only density; `provider_registry` defined in two modules |
| **Absolute where relative was needed** | `created_at = now()` at load (broke hash stability); `observed_at` pinned, rotted past a 14-day freshness window |
| **Enum/str collapse** | `sorted(kind.value)` on a `str` Enum put sources before their own parent nodes |
| **Inverted semantics** | `discount` declared inverted; the tau loop skipped the inversion MRI and IRI both apply |
| **Incomplete filter** | sanitizer filtered **2 of the 5** term sets the metrics measure |
| **Mis-scoped gate** | a per-unit loop gated by a GLOBAL composite risk |
| **Assertion false about its own literal** | golden fixture claimed >= 2 modals on text containing 1; canon test excluded a date while requiring that record's file present |
| **Test outliving its subject** | a stub-rune test whose rune got implemented; providers that no longer exist |

## 3. Transferable rules

1. **Measure before hypothesising.** Every apparent "impossible threshold" resolved into
   machinery once measured. The firewall cluster is the proof: `move_threshold` scored **0.000**
   when put to Jev, and the real causes were a refusal quoting 40 verbatim words of the draft it
   was refusing, a template containing a CLOSURE_TERM, an incomplete filter, and a
   METAPHOR_MARKER in boilerplate. **Moving the threshold would have encoded every one of those
   as intended behaviour.**
2. **Read the body before trusting the docstring or the summary.** Six corrections this session
   came from opening a file: the "fixture swap", the `tuning_layer` raise, the integration
   direction, the registry rename, the "impossible" ratios, and my own sanitizer's filter list.
3. **A passing test is a witness.** Jev abstained three times for "lack of an external witness",
   and each time the witness existed: `domain_map.json` for the econ label,
   `test_tdd_classifier.py` for the firewall severity ranking, `test_temporal_firewall.py` for
   DE_ESCALATE's contract.
4. **Land measured-joint parts jointly.** Registry-only rename: 19 -> 31; atomic: clean.
   `force_response_mode` override alone: 13 -> 13; with the template fix: 13 -> 12.
5. **Enumerate before fixing.** Five term sets existed; fixing against two cannot converge.
6. **Measure blast radius; do not estimate it.** "Low risk because it touches no canon identity"
   describes the SCOPE of a change, not the number of DEPENDENTS on it.
7. **Never move a threshold to make a test green.** `move_threshold` **0.000** and
   `lower_threshold` **0.000** on all five occasions. Not once was a threshold the problem.

## 4. Also delivered

- **Production engine wiring** — real providers (athanor, cypher, noesis, oracle, trutina)
  replace five inline mock types; mocks are opt-in. Health can report an unimplemented engine as
  unhealthy instead of HEALTHY.
- **Model-agnostic inference adapter** (`abraxas/evidence/adapters/model_agnostic.py`) — any
  OpenAI-compatible endpoint, deterministic offline fallback, honest provenance. Athanor is
  constructible without a bespoke model. UI carries a "custom inference coming soon" notice.
- **Yggdrasil / ABX-Runes integration** — `YggdrasilEngineRegistry` now loads all 117 rune
  bindings; it previously imported none and nothing imported it back.
- **Rune capability convention unified** to `RUNE.<PATH>` (67 files, 194 literals).
  Sigil-numeral `rune_id`s deliberately untouched: the sigils are canon identity,
  manifest-enforced.
- **Collection-order dependence fixed at root**, with the standing rule that baseline claims
  require BOTH collection orders.

## 5. Process honesty

Three of the last four turns ended in a **revert**: the registry-only rename (19 -> 31), the
non-censorship allowlist (3 files against a 244-violation tail), and the `tuning_layer`
recommendation (would have broken working code). Two of my own recommendations were retracted
after reading the source. All of it is recorded in `docs/TEST_DEBT.md` rather than quietly
dropped, because the reverts are the evidence for the rules above.
