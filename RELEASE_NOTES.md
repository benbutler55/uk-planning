# Release Notes

## v1.0 — Pilot Release (2026-03-17)

### Summary

First complete release of the England planning system analysis. Covers all phases of the implementation plan from research corpus through to published recommendations, scenario testing, and deployment-ready static site.

### Deliverables

**Research corpus:**
- 16 core legislation and regulation records (England)
- 31 national policy and PPG topic records including full NPS suite
- 6 pilot LPAs with 22 plan document records including neighbourhood plans
- Policy precedence hierarchy mapping for all 6 pilot authorities

**Analysis:**
- 22 issues in contradiction register across all 6 process stages (pre-application, validation, consultation, committee, legal agreements, condition discharge)
- 12 bottleneck records with severity heatmap by stage and pathway
- Weighted scoring model (explicit dimension weights: delay 35%, legal risk 30%, severity 20%, frequency 10%, fixability 5%)

**Recommendations:**
- 11 recommendations with official evidence traces
- 12 evidence links to GOV.UK planning statistics and PINS data
- 12 official baseline metrics (England aggregate + pilot LPA breakdowns)
- Full model drafting text for all 11 recommendations
- Implementation roadmap (6 milestones, quick wins and statutory reform split)

**Website:**
- 23 generated HTML pages
- Split audience views (policy makers, LPAs, developers, public)
- Filterable contradiction and recommendation tables
- Bottleneck heatmap page
- CSV/JSON exports for all datasets
- Bottleneck heatmap export

**Infrastructure:**
- Schema-based data validation with FK, enum, and unique-ID checks
- Internal link checker
- Monthly automated freshness check (warning-only)
- GitHub Pages CI/CD pipeline (pinned action SHAs)
- AGENTS.md operating rules for agent commit/push hygiene

### Known Limitations

- All records at `draft` verification state. Legal review required for advancement.
- Baseline metrics for condition discharge and s106 timelines are proxy-based; no direct official dataset.
- LURA 2023 commencement ongoing; plan-making recommendations subject to transitional review.
- Analysis covers England only; devolved nations out of scope.

### Next Release (v1.1 — Target: 4 weeks)

- Cohort 2 LPA expansion (10 additional authorities)
- Automated GOV.UK statistics ingest
- National map view
- Stakeholder consultation on draft recommendations
