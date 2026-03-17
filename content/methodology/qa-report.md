# QA Report and Scenario Testing

**Version:** MVP 1.0
**Date:** 2026-03-17
**Status:** Draft — awaiting user verification

---

## 1. Citation Integrity Review

### Method

Each recommendation was cross-checked against its evidence links in `data/evidence/recommendation_evidence_links.csv`. For each link, the following were verified:

- Source URL resolves (checked via `scripts/check_freshness.py`)
- Metric name corresponds to the referenced GOV.UK table or PINS dataset
- Baseline value falls within a plausible range given the source data
- Baseline window matches the official publication period

### Findings

| Rec | Evidence Links | URL Status | Metric Match | Confidence |
|-----|---------------|------------|--------------|------------|
| REC-001 | EVD-001 | Pass | PS2 invalid/withdrawn proxy — plausible, not exact | High |
| REC-002 | EVD-002 | Pass | P152 overturn rate — directly cited | High |
| REC-003 | EVD-003 | Pass | Plan age proxy from NPPF revision log — estimated | Medium |
| REC-004 | EVD-004, EVD-005 | Pass | P151 and PINS stats — both confirmed | Medium |
| REC-005 | EVD-006 | Pass | Officer estimation — no official dataset, flagged | Medium |
| REC-006 | EVD-007 | Pass | P153 used as proxy; no direct condition discharge dataset | High |
| REC-007 | EVD-008 | Pass | s106 delay estimated from delivery evidence — no single official table | High |
| REC-008 | EVD-009 | Pass | PINS ministerial measures — partial proxy | Medium |
| REC-009 | EVD-010 | Pass | PPG monitoring and practitioner evidence — estimated | Medium |
| REC-010 | EVD-011 | Pass | PINS NSIP statistics — confirmed | Medium |
| REC-011 | EVD-012 | Pass | EIA screening records — estimated proportion | Low |

**Gaps identified:**
- No official dataset directly measuring condition discharge timelines (REC-006). Recommend MHCLG add condition discharge duration to PS2 reporting.
- No official dataset for s106 completion timelines (REC-007). MHCLG housing delivery statistics provide partial evidence only.
- REC-011 evidence confidence rated low due to absence of comprehensive EIA over-screening data. Recommend MHCLG commission screening review.

---

## 2. Legal and Policy Consistency Check

### Method

Each contradiction record and recommendation was checked against the listed linked instruments for:

- Instrument status (in force vs superseded vs partially commenced)
- Correct legal basis for the proposed implementation vehicle
- No circular or self-referential instrument linkage

### Findings

| Issue | Linked Instruments | Status Check | Notes |
|-------|-------------------|--------------|-------|
| ISSUE-008 | LEG-ENG-2023-LURA | Partial commencement | LURA 2023 transitional provisions still rolling out; recommendations correctly note transitional risk |
| ISSUE-004/011 | LEG-ENG-2017-HABITATS | In force (amended post-Brexit) | Post-REULA 2023 amendments noted; basis for REC-004 CEER proposal confirmed valid |
| ISSUE-018 | LEG-ENG-2008-PA | In force | PA 2008 pre-application requirements at ss.42-47 confirmed as basis for REC-010 |
| REC-002 | LEG-ENG-2004-PCPA s38(6) | In force | SI amendment vehicle confirmed appropriate for precedence clarification |
| REC-006 | LEG-ENG-2015-DMPO | In force (amended) | DMPO amendment vehicle confirmed for statutory condition discharge period |

**No material legal inconsistencies identified.** All proposed implementation vehicles are within the competence of the specified delivery owners.

---

## 3. Scenario Testing

Three representative development pathways were tested against the contradiction register and recommendations to verify that identified issues and proposed reforms are internally consistent and operationally relevant.

---

### Scenario A: Major Housing Development on Allocated Site (200 dwellings, district LPA, green belt adjacent)

**LPA:** Oxford City Council (LPA-02, pilot)
**Pathway stage-by-stage:**

| Stage | Issues Triggered | Bottlenecks | Applicable Reforms |
|-------|-----------------|-------------|--------------------|
| Pre-application | ISSUE-005 (transitional policy uncertainty), ISSUE-007 (housing needs methodology), ISSUE-014 (grey belt definition) | BN-001 (4 weeks delay) | REC-003 (policy sync), REC-002 (precedence rules) |
| Validation | ISSUE-002 (inconsistent checklist), ISSUE-006 (no national list) | BN-003 (3 weeks delay) | REC-001 (national validation checklist) |
| Consultation | ISSUE-010 (consultee overlap), ISSUE-017 (late responses) | BN-005 (4 weeks delay) | REC-008 (binding deadline) |
| Committee | ISSUE-001 (housing need vs local policy), ISSUE-022 (tilted balance) | BN-007 (2 weeks delay) | REC-002 (precedence), REC-005 (design checklist) |
| Legal Agreements | ISSUE-009 (s106 delay), ISSUE-016 (viability re-assessment), ISSUE-019 (tenure mix) | BN-009 (26 weeks), BN-010 (12 weeks) | REC-007 (standard clauses), REC-009 (viability lock) |
| Condition Discharge | ISSUE-012 (no statutory period), ISSUE-020 (excessive conditions) | BN-011 (16 weeks) | REC-006 (8-week statutory period) |

**Total indicative delay from issues:** approximately 67 weeks above minimum statutory determination period.
**Expected reform impact:** approximately 40-50 weeks delay reduction if REC-001, REC-006, REC-007, REC-008, REC-009 implemented.

---

### Scenario B: Commercial Logistics Development (10,000 sqm, edge-of-town, transport assessment required)

**LPA:** South Cambridgeshire District Council (LPA-03, pilot)
**Pathway stage-by-stage:**

| Stage | Issues Triggered | Bottlenecks | Applicable Reforms |
|-------|-----------------|-------------|--------------------|
| Pre-application | ISSUE-003 (overlapping design tests), ISSUE-013 (transport assessment scope) | BN-001 (3 weeks) | REC-005 (baseline design/transport code) |
| Validation | ISSUE-002 (validation inconsistency), ISSUE-015 (EIA over-screening for 1.2 ha site) | BN-003 (3 weeks), BN-004 (5 weeks if screened in) | REC-001, REC-011 (updated thresholds) |
| Consultation | ISSUE-013 (highway authority scope), ISSUE-017 (late responses) | BN-005 (4 weeks), BN-008 (2 weeks) | REC-008 (consultee deadline) |
| Committee | ISSUE-013 (transport conditions required post-committee) | BN-008 (2 weeks) | REC-005 (transport baseline) |
| Legal Agreements | Not applicable for this scheme type | — | — |
| Condition Discharge | ISSUE-012 (transport and ecology conditions) | BN-011 (12 weeks) | REC-006 (statutory period) |

**Total indicative delay:** approximately 31 weeks above minimum statutory period.
**Expected reform impact:** approximately 15-20 weeks delay reduction if REC-001, REC-005, REC-006, REC-008 implemented.

---

### Scenario C: Nationally Significant Infrastructure — Onshore Wind Farm (120MW, NSIP threshold)

**Authority:** Planning Inspectorate (NSIP track)
**Pathway stage-by-stage:**

| Stage | Issues Triggered | Bottlenecks | Applicable Reforms |
|-------|-----------------|-------------|--------------------|
| Pre-application | ISSUE-018 (NSIP vs non-NSIP boundary), ISSUE-021 (disproportionate pre-app requirements) | BN-002 (12 weeks on track allocation; 52+ weeks for full pre-app) | REC-010 (tiered NSIP pre-app) |
| Validation (acceptance) | ISSUE-004 (EIA/HRA duplication at scoping) | BN-004 (5 weeks), BN-006 (8 weeks for combined ecological evidence) | REC-004 (evidence gateway) |
| Consultation (examination) | ISSUE-011 (HRA/EIA overlap), ISSUE-004 (duplicate evidence requests) | BN-006 (8 weeks) | REC-004 (CEER single gateway) |
| Examination/Committee | ISSUE-018 (NPS policy weight disputes for below-threshold schemes) | BN-007 (variable) | REC-010 (tier clarity) |
| Legal Agreements (DCO) | ISSUE-009 (DCO requirement conditions delay discharge) | BN-012 (20 weeks) | — |
| Condition Discharge (requirements) | ISSUE-012, ISSUE-004 | BN-012 (20 weeks) | REC-006 (where DMPO applies to any associated consent) |

**Total indicative delay:** pre-application stage alone adds 78-130 weeks over minimum required consultation.
**Expected reform impact:** REC-010 could reduce NSIP Tier 1 pre-app from 78 weeks to approximately 26 weeks. REC-004 reduces examination preparation time by approximately 8-16 weeks.

---

## 4. Internal Consistency Check

### Recommendation-to-issue coverage

All 22 issues in the contradiction register are linked to at least one recommendation. No orphaned issues identified.

### Issue-to-process-stage coverage

All six process stages have at least one issue and one bottleneck record:

| Stage | Issues | Bottlenecks |
|-------|--------|-------------|
| Pre-application | 7 | 2 |
| Validation | 4 | 2 |
| Consultation | 4 | 3 |
| Committee | 4 | 2 |
| Legal Agreements | 3 | 2 |
| Condition Discharge | 2 | 2 |

### Recommendation delivery owner coverage

| Owner | Recommendations |
|-------|----------------|
| MHCLG | REC-001, REC-002, REC-003, REC-008, REC-009, REC-011 |
| MHCLG and LPAs | REC-005, REC-007 |
| MHCLG and DESNZ | REC-004 |
| PINS and MHCLG | REC-010 |
| LPAs | REC-005 (co-delivery) |

---

## 5. Outstanding Limitations

1. **Baseline metrics are proxies** for some KPIs (condition discharge, s106 timelines, viability re-assessment). Direct measurement requires MHCLG to update planning statistics collection.
2. **Pilot LPA evidence** for REC-005 design compliance baseline is estimated from officer assessment rather than a systematic dataset.
3. **LURA 2023 commencement** is ongoing; recommendations touching plan-making (REC-003, REC-002) will need review once all provisions are commenced.
4. **Verification state** of all records is currently `draft`. Advancement to `verified` or `legal-reviewed` requires formal legal review and stakeholder consultation.
5. **Scotland, Wales, Northern Ireland** are out of scope for this MVP. Cross-border NSIP schemes may require separate treatment.
