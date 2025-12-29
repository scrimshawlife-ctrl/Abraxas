# Paper Triage Rules for SML Registry

**Version**: 1.0
**Last Updated**: 2025-12-26
**Scope**: Simulation Mapping Layer (SML) paper registry curation

---

## Purpose

This document defines inclusion/exclusion criteria for adding academic papers to the SML paper registry (`data/sim_sources/papers.json`). The registry should contain high-quality academic sources relevant to misinformation/information dynamics modeling.

---

## Inclusion Criteria

### ✅ INCLUDE

Papers that meet ANY of the following criteria:

1. **Epidemic/Diffusion Models for Misinformation**
   - SIR, SEIR, SIS variants applied to misinformation/rumor spread
   - Coupled information-epidemic dynamics
   - Media impact parameters (c2, advertising, external fields)
   - Examples: PMC12281847, PMC10250073, PMC12564303

2. **Opinion Dynamics Models**
   - Voter models, DeGroot models, bounded confidence
   - Social influence, homophily, polarization
   - Mass media influence on opinion formation
   - Examples: ARXIV_OPINION_OVERVIEW, PMC9689558, JASSS_ARGUMENT_BASED

3. **Agent-Based Misinformation Models**
   - Bot/automation agents
   - Platform moderation/intervention mechanisms
   - Sharing behavior, virality dynamics
   - Examples: DSAA2019_MISINFO, ICWSM2021_ABM_FAKENEWS

4. **Network Cascade Models**
   - Threshold models, cascade dynamics
   - Network structure effects on spread
   - Examples: Papers with activation thresholds, cascade branching

5. **Game-Theoretic Models**
   - Propagandist-citizen dynamics
   - Inspection games, sanction mechanisms
   - Strategic misinformation deployment
   - Examples: ARXIV_SPATIAL_GAMES, PNAS_SPATIAL_GAMES

6. **Survey/Meta-Analysis Papers** (Limited)
   - Comprehensive reviews of model families
   - Must provide parameter taxonomy across multiple models
   - Examples: ARXIV_OPINION_OVERVIEW, OPENREVIEW_ABM_SURVEY
   - **Limit**: Max 2-3 survey papers per model family

---

## Exclusion Criteria

### ❌ EXCLUDE

Papers that meet ANY of the following criteria:

1. **SEO/Wordlist/Non-Academic Sources**
   - "SEO list" pages
   - Wordlists, dictionaries, taxonomies without models
   - Blog posts, opinion pieces
   - **Rationale**: Not peer-reviewed academic work

2. **Unrelated Technical Papers**
   - Papers about unrelated technical topics (e.g., compiler optimization, database indexing)
   - PDFs that happen to mention "information" but are not about information dynamics
   - **Rationale**: No relevance to misinformation modeling

3. **Non-Quantitative Descriptive Papers**
   - Purely qualitative analysis without formal models
   - No mathematical parameters or equations
   - **Rationale**: Cannot extract parameters for SML mapping

4. **Biological/Medical Papers** (Unless Relevant)
   - Pure epidemiology papers about disease transmission (without misinformation angle)
   - Clinical trials, medical studies
   - **Exception**: Include if paper explicitly applies epidemic model to information/misinformation
   - **Rationale**: SML is for information dynamics, not biological epidemiology

5. **Duplicate Publications**
   - Same paper across multiple repositories (arXiv, PMC, PubMed, journal site)
   - **Action**: Keep ONE canonical version (prefer arXiv or PMC), mark others as duplicates in notes field
   - **Example**: ARXIV_SPATIAL_GAMES (canonical), PNAS_SPATIAL_GAMES/PMC10924450/PUBMED_38463039 (duplicates)

6. **Paywalled/Inaccessible Papers**
   - Papers behind paywalls with no accessible version
   - **Rationale**: Cannot verify parameters without access
   - **Exception**: If abstract/supplementary materials provide sufficient parameter info

7. **Pre-prints Without Follow-up** (Case-by-Case)
   - Extremely early pre-prints with no subsequent versions
   - **Rationale**: May contain errors or incomplete models
   - **Exception**: Include if model is well-specified and stable

---

## Duplicate Handling

When encountering the same paper across multiple sources:

1. **Identify Canonical Version**:
   - Prefer: arXiv > PMC > journal site > PubMed abstract
   - **Rationale**: arXiv/PMC typically have full text and stable URLs

2. **Registry Entry**:
   - Create ONE entry with canonical paper_id and URL
   - In `notes` field, list duplicate sources

3. **Example Stub Files**:
   - Create full parameter stub for canonical version
   - Create minimal stub for duplicates with reference to canonical

**Example**:
```json
{
  "paper_id": "ARXIV_SPATIAL_GAMES",
  "title": "Spatial Games of Fake News",
  "url": "https://arxiv.org/abs/2206.04118",
  "notes": "Canonical reference. Duplicated in PMC10924450, PNAS_SPATIAL_GAMES, PUBMED_38463039."
}
```

---

## Parameter Extraction Priority

Papers with these characteristics get **higher priority**:

1. **Well-Specified Parameters**: Clear notation (β, γ, etc.), defined ranges
2. **Experimental Calibration**: Parameters fitted to real data
3. **Sensitivity Analysis**: Papers that explore parameter sensitivity
4. **Reproducible Code**: GitHub repo or supplementary code
5. **Recent Publications**: Prefer 2020+ unless foundational work

---

## Quality Tiers

### Tier 1: Foundational / High-Impact
- Highly cited (>50 citations)
- Novel model formulation
- Experimental validation
- **Action**: Always include, prioritize parameter extraction

### Tier 2: Standard Academic
- Peer-reviewed journal or conference
- Clear parameter specification
- Relevant to misinformation dynamics
- **Action**: Include if capacity permits

### Tier 3: Marginal
- Pre-prints without validation
- Weak parameter specification
- Tangential relevance
- **Action**: Include only if filling gaps in model family coverage

---

## Registry Maintenance Rules

1. **Append-Only**: Never delete papers once added (unless proven invalid)
2. **Annotation-Only Updates**: Update `notes` field to add context, not to modify canonical data
3. **Deduplication**: Periodically audit for duplicates, consolidate using rules above
4. **Versioning**: Maintain `metadata.last_updated` field
5. **Provenance**: Always include URL and paper_id for traceability

---

## Example Decision Tree

```
Is the paper peer-reviewed or from arXiv?
  NO → EXCLUDE (unless exceptional case)
  YES ↓

Does it contain a formal mathematical model with parameters?
  NO → EXCLUDE
  YES ↓

Is it about information/misinformation dynamics (or applied epidemic model to info)?
  NO → EXCLUDE
  YES ↓

Is it a duplicate of an existing entry?
  YES → Mark as duplicate, reference canonical version
  NO ↓

Does it fit into one of the 5 model families?
  NO → Consider if it defines a new family (consult maintainer)
  YES ↓

→ INCLUDE in registry
```

---

## Curator Guidelines

When adding papers to the registry:

1. **Verify URL Accessibility**: Ensure URL is stable and publicly accessible
2. **Extract Year**: Add publication year if available (prefer earliest version)
3. **Write Descriptive Notes**: Briefly describe model type and key parameters
4. **Check for Duplicates**: Search registry before adding
5. **Create Example Stub**: Add `data/sim_sources/examples/{paper_id}.json` if parameters are well-specified
6. **Update Mapping Table**: Add row to `paper_mapping_table.csv`

---

## Special Cases

### Case 1: Survey Papers
- **Limit**: Max 2-3 per model family
- **Parameter Stub**: Leave `params: []` empty (no single parameter set)
- **Value**: Useful for understanding parameter taxonomy across models

### Case 2: Multi-Model Papers
- **Action**: Assign to primary model family
- **Notes**: Mention secondary families in notes field
- **Example**: Paper using both SIR and opinion dynamics → classify as DIFFUSION_SIR, note opinion component

### Case 3: Foundational Papers (Pre-2000)
- **Action**: Include if widely cited and foundational
- **Example**: Original DeGroot model, Bass diffusion model
- **Rationale**: Historical context and baseline comparisons

---

## Rejection Examples

| URL | Reason |
|-----|--------|
| example.com/seo-keywords.html | SEO list, not academic |
| pmc.nlm.nih.gov/articles/PMC1234567 (cancer genetics) | Unrelated domain |
| blog.medium.com/opinion-piece | Not peer-reviewed |
| example.edu/paywall-only.pdf | Inaccessible, no public version |

---

## References

- Paper Registry: `data/sim_sources/papers.json`
- Example Stubs: `data/sim_sources/examples/`
- Mapping Table: `data/sim_sources/paper_mapping_table.csv`
- SML Specification: `docs/specs/simulation_mapping_layer.md`
