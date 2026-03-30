# Next Round of Improvements — Design Spec

**Date:** 2026-03-30
**Status:** Approved

## Overview

Four sequential improvement phases to take the UK Planning Analysis site from a functional pilot to a maintainable, data-rich, analytically deeper, and more capable platform.

## Phase 1: Code Quality & Maintainability

### Problem

`scripts/build_site.py` is a 4,300-line monolith. Every change requires understanding the entire file. There are no tests. The build version string is stale (`v6.0` despite being at Phase 10).

### Design

Split `build_site.py` into focused modules:

```
scripts/
├── build_site.py              # Entry point only (~50 lines): load data, call generators, write outputs
├── builders/
│   ├── __init__.py
│   ├── data_loader.py         # CSV/JSON loading, schema validation, data structures
│   ├── html_utils.py          # Shared HTML rendering: shell, nav, footer, cards, badges, tables
│   ├── page_overview.py       # index, search
│   ├── page_analysis.py       # legislation, contradictions, bottlenecks, appeals, baselines
│   ├── page_authorities.py    # plans, LPA profiles, map, compare, benchmark, reports, coverage
│   ├── page_recommendations.py # recommendations, roadmap, consultation
│   ├── page_methods.py        # methodology, metric-methods, sources, exports, data-health
│   ├── page_audiences.py      # audience-* pages
│   ├── page_details.py        # contradiction-issue-*, recommendation-rec-* detail pages
│   └── export_utils.py        # Export manifest, report bundles, search index, UX KPI artifacts
├── tests/
│   ├── __init__.py
│   ├── test_data_loader.py    # Schema compliance, missing field detection, edge cases
│   ├── test_html_utils.py     # Component rendering correctness
│   ├── test_page_generation.py # Smoke tests: each page generator produces valid HTML
│   └── test_exports.py        # Manifest hashes, report bundle structure
```

Additional changes:
- Extract `BUILD_VERSION` to a `version.py` or top-level `VERSION` file, update to `v11.0`
- Extract `SECTION_CONFIG` to a separate config module
- Add `pytest` test suite with smoke tests for every generated page
- Add `ruff` linting compliance

### Constraints

- Every existing page must render identically after refactor (byte-for-byte HTML output comparison as regression test)
- No new dependencies beyond stdlib + pytest + ruff
- All existing CI checks must continue to pass

## Phase 2: Data Depth

### Problem

Stuck at 16 LPAs across 2 cohorts. Several benchmark metrics are analytical proxies rather than official series. No automated GOV.UK data pipeline.

### Design

**Cohort 3 onboarding (10 LPAs):**

Add the 10 authorities from `scale-out-backlog.md`:
- Leeds, Bristol, Guildford, Newcastle, Peak District NPA, Northumberland, Southampton, Leicester, Cambridge, Medway

For each:
1. Add row to `pilot-lpas.csv` with full metadata
2. Add plan documents to `pilot-plan-documents.csv`
3. Add policy hierarchy entries to `policy-hierarchy.csv`
4. Add geo coordinates to `lpa-geo.csv`
5. Add data quality tier to `lpa-data-quality.csv`
6. Add quarterly trend data to `lpa-quarterly-trends.csv`
7. Add issue incidence rows to `lpa-issue-incidence.csv`
8. Run onboarding pipeline and commit artifacts
9. Update schema if needed

**GOV.UK statistics integration:**

Enhance `scripts/ingest_govuk_stats.py` to:
- Download PS1/PS2 live tables (planning application statistics) programmatically
- Parse and map to internal schema fields
- Replace proxy metrics where official data is available (target: validation rework rate, delegated decision share)
- Write ingest audit trail to `stats-ingest-history.json`

**Metric upgrades:**
- Replace `validation_rework_proxy` with official PS1 validation data where available
- Replace `delegated_share_proxy` with official delegated decision percentages from PS2
- Update confidence badges from `medium`/`low` to `high` for upgraded metrics

### Constraints

- New LPAs enter as quality tier B or C (not A) until verified
- Proxy metrics remain as fallback where official data unavailable
- Schema must be updated before data changes

## Phase 3: Content & Analysis Quality

### Problem

All 22 contradiction records are `draft` verification state. Only 10 appeal decisions. Evidence cross-referencing is sparse.

### Design

**Verification upgrades:**
- Review all 22 contradiction records against source citations
- Upgrade records with strong evidence chains from `draft` to `verified` (target: 12+ records)
- Add confidence justification notes to upgraded records

**Appeal decisions expansion:**
- Add 5+ new appeal decision citations from PINS published decisions
- Link new appeals to existing contradiction records where applicable
- Add appeal outcome analysis (allowed/dismissed/split) to detail pages

**Cross-referencing:**
- Add `related_issues` field to contradiction register linking related ISSUE-* records
- Add `evidence_gaps` column to recommendations identifying where evidence is thin
- Generate an evidence coverage matrix page showing which recommendations have strong vs weak evidence backing

**Evidence gap analysis:**
- New data file: `data/evidence/evidence-gaps.csv` with fields: `record_id`, `record_type`, `gap_description`, `severity`, `remediation_path`
- Build script generates a summary section on `methodology.html` showing overall evidence health

### Constraints

- Only upgrade to `verified` where citation chain is complete and checkable
- New appeal records must reference real PINS decision letters
- Evidence gap records are `draft` by default

## Phase 4: User-Facing Features

### Problem

No temporal views, no PDF export, no way to track how an authority's performance changes over time.

### Design

**Trend analysis page (`trends.html`):**
- Time-series view of key metrics across quarters for all LPAs
- Filterable by region, type, cohort
- Sparkline expansion: click a sparkline on benchmark to jump to full trend view
- Show England aggregate trend line as reference

**LPA change-over-time view:**
- Add "Performance history" section to each `plans-lpa-XX.html` detail page
- Quarter-on-quarter change indicators with direction arrows
- Link to relevant trend page filtered for that authority

**Enhanced PDF/print export:**
- Add print stylesheet optimized for A4 output
- Add "Export as PDF" button on key pages (contradictions, recommendations, LPA profiles)
- Uses browser print-to-PDF (no server-side dependency)

**Comparison history:**
- Save comparison pairs to localStorage with timestamp
- Show "Recent comparisons" panel on `compare.html`
- Allow clearing history

### Constraints

- No server-side dependencies (static site)
- PDF export via print stylesheet only (CSS `@media print`)
- Trend data limited to available quarters in `lpa-quarterly-trends.csv`

## Success Criteria

1. **Phase 1:** All pages render identically after refactor. Test suite passes. `ruff check` clean. Build script under 100 lines.
2. **Phase 2:** 26 LPAs in dataset. At least 2 proxy metrics replaced with official data. Onboarding pipeline runs clean for all new LPAs.
3. **Phase 3:** 12+ contradiction records upgraded to `verified`. 15+ appeal decisions. Evidence gap analysis visible on methodology page.
4. **Phase 4:** Trend page live. LPA detail pages show performance history. Print export works on all key pages. Comparison history functional.
