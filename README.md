# UK Planning Analysis

Citation-backed analysis of England's planning system identifying contradictions, bottlenecks, and opportunities for reform. Published as a static website on GitHub Pages.

## Current State (v11.0 Phase 11)

- 16 core legislation and regulation records
- 31 national policy, PPG topic, and NPS records
- **16 LPAs across 2 cohorts** with 44 plan document records (including neighbourhood plans)
- Policy precedence hierarchy mapping for all 16 authorities
- 22 issues in contradiction register across all 6 process stages (weighted-scored)
- 12 bottleneck records with severity heatmap by stage and pathway
- 11 recommendations with model drafting text and official evidence traces
- 12 evidence links to GOV.UK planning statistics and PINS data
- 19 official baseline metrics (England aggregate and all LPA breakdowns)
- 10 appeal decision citations linked to contradiction records
- 11 recommendation consultation status records
- LPA data quality tiers (`A/B/C`) with coverage scores for all 16 authorities
- Full-text client-side search across all content
- National Leaflet.js map with decision speed overlay
- LPA side-by-side comparison page (`compare.html`)
- LPA benchmark dashboard with ranking, percentile banding, trend sparklines, and region/type filters
- Benchmark analytics include cohort and regional drilldowns, 4-quarter change, and outlier flags
- Downloadable per-LPA report bundles (`reports/*.csv` and `reports/*.json`)
- Report bundles now include version and generation-date stamps
- Benchmark preset compare links and compare-page URL deep-linking (`?a=LPA-XX&b=LPA-YY`)
- Compare page supports saved preset pairs in-browser for repeat use
- Shared authority filter state (`region`, `type`, `cohort`, `quality`) persists across plans, benchmark, compare, and reports views
- Metric provenance badges across benchmark and reports (official stats vs analytical estimates)
- Inline metric definition/provenance help markers on benchmark and reports tables
- Tooltip method links from benchmark/reports to a dedicated metric-methods appendix
- Context panels on generated pages to explain what each view shows and how to interpret it
- Per-record drill-down pages for contradictions (`contradiction-issue-xxx.html`) with connected recommendations, appeals, bottlenecks, and filter-context links
- Per-record drill-down pages for recommendations (`recommendation-rec-xxx.html`) with status timeline, linked contradictions, milestones, and evidence rows
- Detail pages now include subsection anchors and sticky mini-TOC blocks (Summary, Evidence, Connected items, Actions)
- Homepage "England at a glance" KPI strip with source-linked baseline indicators and trend movement card
- Peer-group benchmark mode for like-for-like authority comparisons, with anchor-authority toggle on benchmark view
- Expanded authority metrics on benchmark/reports: validation rework proxy, delegated share proxy, plan age, consultation lag proxy, backlog pressure index
- Analytical confidence badges (high/medium/low) on estimated authority metrics and report bundles
- Boundary-led choropleth map layer with marker overlay toggle on `map.html`
- Coverage tracker page (`coverage.html`) with complete/partial/estimated authority status
- Onboarding pipeline outputs under `site/reports/onboarding/*.json` with ingest->validate->profile->QA gate status
- Mobile table detail drawer on dense benchmark/reports/contradictions tables
- Guided vs Expert page mode toggle with optional plain-language guidance
- Faceted search filters (type/pathway/confidence/status) with exact-ID prioritization
- Quick filter presets and active-filter chips on major analytical tables
- Shareable state helper (`Copy this view`) and global trust legend
- UX KPI artifacts generated under `site/reports/ux-kpi-report.*`
- Quarterly automated GOV.UK statistics ingest check
- Ingest workflow now publishes both text and JSON freshness reports as build artifacts
- Statistics ingest can append quarterly run history (`stats-ingest-history.json`) and source-level freshness details
- Data health dashboard page (`data-health.html`) with freshness status for core datasets
- Export manifest (`site/exports/manifest.json`) includes dataset hashes, row counts, and build timestamp
- Monthly decision snapshot bundles generated under `site/reports/monthly-snapshot.*`
- CI/Pages now include metric-drift and accessibility checks
- CI now includes derived metric stability checks (`scripts/check_metric_stability.py`)
- IA refresh: 5-section top navigation (audiences moved to footer + homepage cards) with two-tier visual hierarchy
- Progressive drill-down from overview to analysis to authority-level detail pages
- Standard page guide blocks on generated pages (what, who, how, data freshness)
- “How to read this table” explainers for major analytical tables
- “Where to go next” step cards across pages for intuitive cross-navigation
- Detail pages use sidebar layout (sticky TOC + metadata on desktop, single column on mobile)
- Card variants for visual hierarchy: `.card-kpi`, `.card-guidance`, `.card-hero`, `.card-filter`
- Homepage organised with section headings (Key Indicators, Explore by Goal, Audience Views, Data & Health)
- Collapsible settings/trust bar (closed by default) to reclaim viewport space
- Table row striping, sortable headers with `aria-sort`, cell truncation for long text
- Mobile hamburger nav collapse below 768px, table tap hints, back-to-top button
- Site-wide footer with section links, version info, and methodology/data health links
- External shared JS (`assets/shell.js`) for view mode, plain language, copy, event logging
- Accessibility: `aria-live` filter counts, double-ring focus indicators, font-display swap fallback
- Methodology page now includes monthly/quarterly/annual governance cadence and owner responsibilities
- Metric methods appendix page (`metric-methods.html`) documents formulas, provenance, and confidence mapping for authority metrics
- UI blueprint document for reusable layout/copy components (`content/methodology/ui-blueprint.md`)
- Consultation layer with status tracker, disclaimer, and PDF print export
- CI and Pages guardrails fail if generated `site/` artifacts are out of sync
- 39+ generated site pages including benchmark and reports views

## Repository Structure

```
uk-planning/
├── AGENTS.md                        # Agent operating rules (commit, push, README hygiene)
├── IMPLEMENTATION_PLAN.md           # Phased delivery plan
├── RELEASE_NOTES.md                 # Version release notes
├── README.md                        # This file
├── data/
│   ├── evidence/
│   │   ├── appeal-decisions.csv     # PINS appeal decisions linked to issues
│   │   ├── lpa-quarterly-trends.csv # Quarterly trend data for benchmark sparklines
│   │   ├── official_baseline_metrics.csv
│   │   └── recommendation_evidence_links.csv
│   ├── issues/
│   │   ├── bottleneck-heatmap.csv
│   │   ├── contradiction-register.csv
│   │   ├── implementation-roadmap.csv
│   │   ├── lpa-issue-incidence.csv  # LPA-level issue and severity incidence
│   │   ├── recommendation-status.csv  # Consultation submission tracker
│   │   └── recommendations.csv
│   ├── legislation/
│   │   └── england-core-legislation.csv
│   ├── plans/
│   │   ├── lpa-geo.csv              # LPA coordinates for map
│   │   ├── lpa-data-quality.csv     # LPA evidence quality tiers and coverage scores
│   │   ├── pilot-lpas.csv           # 16 LPAs across 2 cohorts
│   │   ├── pilot-plan-documents.csv
│   │   └── policy-hierarchy.csv
│   ├── policy/
│   │   └── england-national-policy.csv
│   └── schemas/
│       ├── datasets.json
│       └── scoring.json
├── scripts/
│   ├── build_site.py                # Thin entry point — orchestrates builders/ modules
│   ├── check_accessibility.py      # Accessibility guardrails for generated HTML
│   ├── check_metric_drift.py       # Quarter-on-quarter drift threshold checks
│   ├── check_metric_stability.py   # Stability checks for derived authority metrics
│   ├── check_freshness.py           # Monthly URL/staleness checker (warn-only)
│   ├── check_links.py
│   ├── ingest_govuk_stats.py        # Quarterly GOV.UK statistics ingest check
│   ├── onboard_council.py           # Onboarding gate checks and report writer
│   ├── serve_local.sh
│   ├── validate_data.py
│   ├── builders/                    # Modular page-builder package
│   │   ├── __init__.py
│   │   ├── config.py                # Paths, constants, site-wide settings
│   │   ├── data_loader.py           # CSV ingestion and data-health helpers
│   │   ├── html_utils.py            # Shared HTML rendering primitives
│   │   ├── metrics.py               # Derived metric computations
│   │   ├── page_analysis.py         # Contradictions, bottlenecks, appeals pages
│   │   ├── page_audiences.py        # Audience-specific views (policymakers, LPAs, etc.)
│   │   ├── page_authorities.py      # LPA profiles, benchmark, compare, reports pages
│   │   ├── page_core.py             # Homepage, legislation, policy, baselines pages
│   │   └── page_meta.py             # Methodology, sources, exports, search pages
│   └── tests/                       # pytest unit tests for builder modules
│       ├── test_build_regression.py # Regression: built site output is stable
│       ├── test_data_loader.py      # Unit tests for data_loader helpers
│       ├── test_html_utils.py       # Unit tests for HTML rendering primitives
│       └── test_metrics.py          # Unit tests for derived metric logic
├── content/
│   ├── methodology/
│   │   ├── next-wave-roadmap.md      # Ranked delivery roadmap with effort and owners
│   │   ├── phase-3-plan.md          # Next-phase implementation plan
│   │   ├── qa-report.md
│   │   ├── ux-instrumentation-kpis.md  # UX event schema and KPI definitions
│   │   ├── wave-d-ux-data-architecture-backlog.md  # UX/data presentation backlog with acceptance criteria
│   │   └── ui-blueprint.md          # Reusable IA/UI component blueprint
│   │   └── scale-out-backlog.md
│   ├── recommendations/
│   │   └── model-text/              # Model drafting text for all 11 recommendations
│   └── templates/
├── site/                            # Generated static website (committed)
│   ├── assets/styles.css            # Design system stylesheet
│   ├── assets/shell.js              # Shared JS: view mode, nav, utilities
│   ├── exports/
│   ├── reports/                     # Per-LPA downloadable comparison bundles
│   │   └── onboarding/              # Per-authority onboarding gate outputs
│   │   └── ux-kpi-report.json       # Build-time KPI structure and targets artifact
│   ├── search-index.json            # Client-side search index
│   └── *.html                       # 28+ generated pages
└── .github/workflows/
    ├── ci.yml                       # PR and push: validate, build, link check
    ├── freshness.yml                # Monthly: URL and staleness check
    ├── pages.yml                    # Push to main: deploy to GitHub Pages
    └── stats-ingest.yml             # Quarterly: GOV.UK statistics freshness check
```

## Run Locally

```bash
./scripts/serve_local.sh
```

Or step by step:

```bash
python3 scripts/build_site.py
python3 -m http.server 4173 --directory site
```

## Quality Checks

Required before every commit (see `AGENTS.md`):

```bash
python3 scripts/validate_data.py
python3 scripts/build_site.py
python3 scripts/check_links.py
python3 scripts/check_metric_stability.py
python3 -m pytest scripts/tests/ -v
```

Optional checks:

```bash
python3 scripts/check_freshness.py --warn-only   # monthly URL freshness
python3 scripts/ingest_govuk_stats.py --warn-only  # quarterly stats freshness
```

## Contribution Workflow

1. Edit data CSVs or scripts.
2. Run `python3 scripts/validate_data.py` — fix all errors.
3. Run `python3 scripts/build_site.py` — regenerate site.
4. Run `python3 scripts/check_links.py` — confirm no broken links.
5. `git add . && git commit -m "..."` — commit everything including generated `site/`.
6. `git push` — push to `origin/main`.

See `AGENTS.md` for full agent operating rules.

## Site Pages

| Page | Description |
|------|-------------|
| `index.html` | Overview and navigation |
| `legislation.html` | Acts, regulations, and national policy index |
| `plans.html` | Plan hierarchy and all 16 LPA profiles |
| `contradictions.html` | Weighted-scored issue register with filters and linked contradiction detail pages |
| `bottlenecks.html` | Process delay heatmap by stage and pathway |
| `appeals.html` | PINS appeal decisions linked to contradictions |
| `recommendations.html` | Reform proposals with evidence traces, model text, and linked recommendation detail pages |
| `roadmap.html` | Delivery milestones |
| `baselines.html` | Official KPI baselines |
| `map.html` | National Leaflet.js map with decision speed overlay |
| `coverage.html` | Coverage tracker with onboarding gate status per authority |
| `compare.html` | Side-by-side LPA comparison page with URL presets |
| `benchmark.html` | Ranked LPA benchmark dashboard with trend sparklines, filters, provenance badges, and preset compare links |
| `reports.html` | Downloadable per-LPA comparison bundles with region/type filters and provenance tags |
| `consultation.html` | Status tracker, disclaimer, and PDF export |
| `search.html` | Full-text search across all content |
| `audience-policymakers.html` | View for policy makers |
| `audience-lpas.html` | View for local planning authorities |
| `audience-developers.html` | View for developers |
| `audience-public.html` | Plain-language public summary |
| `methodology.html` | Scoring model, evidence standards, and QA |
| `metric-methods.html` | Per-metric formula appendix for benchmark and report indicators |
| `sources.html` | Full evidence and citation index |
| `exports.html` | CSV and JSON dataset download index |

## Hosting

Deployed automatically to GitHub Pages on push to `main` via `.github/workflows/pages.yml`.
