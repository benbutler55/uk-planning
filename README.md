# UK Planning Analysis

Citation-backed analysis of England's planning system identifying contradictions, bottlenecks, and opportunities for reform. Published as a static website on GitHub Pages.

## Current State (v4.0 Phase 4)

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
- Downloadable per-LPA report bundles (`reports/*.csv` and `reports/*.json`)
- Benchmark preset compare links and compare-page URL deep-linking (`?a=LPA-XX&b=LPA-YY`)
- Metric provenance badges across benchmark and reports (official stats vs analytical estimates)
- Context panels on generated pages to explain what each view shows and how to interpret it
- Quarterly automated GOV.UK statistics ingest check
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
│   ├── build_site.py
│   ├── check_freshness.py           # Monthly URL/staleness checker (warn-only)
│   ├── check_links.py
│   ├── ingest_govuk_stats.py        # Quarterly GOV.UK statistics ingest check
│   ├── serve_local.sh
│   └── validate_data.py
├── content/
│   ├── methodology/
│   │   ├── phase-3-plan.md          # Next-phase implementation plan
│   │   ├── qa-report.md
│   │   └── scale-out-backlog.md
│   ├── recommendations/
│   │   └── model-text/              # Model drafting text for all 11 recommendations
│   └── templates/
├── site/                            # Generated static website (committed)
│   ├── assets/styles.css
│   ├── exports/
│   ├── reports/                     # Per-LPA downloadable comparison bundles
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
| `contradictions.html` | Weighted-scored issue register with filters |
| `bottlenecks.html` | Process delay heatmap by stage and pathway |
| `appeals.html` | PINS appeal decisions linked to contradictions |
| `recommendations.html` | Reform proposals with evidence traces and model text |
| `roadmap.html` | Delivery milestones |
| `baselines.html` | Official KPI baselines |
| `map.html` | National Leaflet.js map with decision speed overlay |
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
| `sources.html` | Full evidence and citation index |
| `exports.html` | CSV and JSON dataset download index |

## Hosting

Deployed automatically to GitHub Pages on push to `main` via `.github/workflows/pages.yml`.
