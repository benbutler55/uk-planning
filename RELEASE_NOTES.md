# Release Notes

## v6.0 — Phase 6 Trust, Monitoring, and Decision Readiness (2026-03-20)

### Summary

Phase 6 strengthens trust and operational readiness with dataset health monitoring, drift guardrails, accessibility checks, and versioned export manifests/snapshots.

### Deliverables

**Data trust and monitoring:**
- Added data health page (`site/data-health.html`) with freshness status, age, and monitored source paths for core operational datasets
- Added benchmark/report data-health status cards linking to the full health report

**Drift and QA guardrails:**
- Added metric drift checker (`scripts/check_metric_drift.py`) with fail/warn thresholds for quarter-on-quarter changes
- Added accessibility checker (`scripts/check_accessibility.py`) for generated HTML semantics and control labeling
- CI and Pages workflows now run drift and accessibility checks after build/link checks

**Decision packs and provenance:**
- Added monthly snapshot bundle generation under `site/reports/` (`monthly-snapshot.csv` and `monthly-snapshot.json`)
- Added export manifest generation (`site/exports/manifest.json`) with build version, generation time, row counts, fields, and content SHA-256 hashes

**UX and accessibility polish:**
- Added screen-reader label support (`sr-only`) for search input labeling
- Maintained keyboard-visible focus styling and mobile table overflow support

## v5.0 — Phase 5 Analytics, Automation, and UX Polish (2026-03-20)

### Summary

Phase 5 adds deeper comparative analytics, richer filtering and saved comparison presets, and stronger provenance/version signalling for exported reporting assets.

### Deliverables

**Advanced analytics:**
- Extended benchmark dashboard with cohort and regional drilldowns
- Added 4-quarter decision-speed delta and outlier flags to benchmark ranking
- Added cohort filtering to benchmark and reports tables

**Data pipeline automation and provenance:**
- Enhanced stats ingest automation to emit both text and machine-readable JSON reports (`stats-ingest-report.txt` and `stats-ingest-report.json`)
- Updated ingest workflow artifact upload to include both report formats
- Added report-bundle version and generation-date stamps in per-LPA CSV/JSON report outputs

**UX and accessibility polish:**
- Added compare-page saved preset pairs (browser local storage) for recurring side-by-side authority checks
- Added focus-visible outlines for links, inputs, selects, and buttons
- Improved table usability on smaller screens with horizontal overflow handling

## v4.0 — Phase 4 Benchmarking and Reporting (2026-03-18)

### Summary

Phase 4 adds benchmarking and reporting capabilities so the site can be used for comparative performance review across authorities, not just static policy analysis.

### Deliverables

**Benchmarking:**
- Added quarterly trend dataset (`data/evidence/lpa-quarterly-trends.csv`) covering all 16 LPAs across four quarters
- Added LPA issue incidence dataset (`data/issues/lpa-issue-incidence.csv`) with high-severity counts and primary risk stage
- Added benchmark dashboard page (`site/benchmark.html`) with:
  - ranking by latest major decision speed,
  - percentile banding (top/middle/bottom third),
  - trend sparklines,
  - appeal overturn and issue-incidence context

**Downloadable reports:**
- Added report bundles page (`site/reports.html`)
- Generated per-LPA downloadable bundles under `site/reports/` in both CSV and JSON

**Validation and CI controls:**
- Extended schema coverage for new trend and issue-incidence datasets
- CI/Pages continue enforcing generated artifact sync (`git diff --exit-code -- site`)

### Notes

- Freshness checks remain warning-only for authority sites that block automated requests (for example, some council 403 responses).

## v3.0 — Phase 3 Decision-Support Upgrade (2026-03-18)

### Summary

Phase 3 upgrades the site from a static policy publication to an operational decision-support tool with authority comparison, evidence-quality signaling, and stricter CI integrity controls.

### Deliverables

**Analysis/product upgrades:**
- Added LPA data quality tiers (`A/B/C`) and coverage scoring for all 16 authorities (`data/plans/lpa-data-quality.csv`)
- Added side-by-side LPA comparison page (`site/compare.html`) covering type, region, growth context, constraints, decision speed, tracked plan-document count, and quality tier
- Integrated data quality metadata into plan profile pages and map popups

**Build/quality controls:**
- CI and Pages workflows now fail if generated `site/` artifacts are out of sync after `build_site.py`
- Added `CODEOWNERS` to require explicit review for workflow and core build/schema files

**Planning/documentation:**
- Added Phase 3 implementation plan (`content/methodology/phase-3-plan.md`)
- Updated README to reflect current Phase 3 capabilities and structure

### Notes

- Freshness checker may still produce occasional warning-only access-block messages for certain council sites that reject automated requests; this does not block deployment.

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
