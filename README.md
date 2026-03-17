# UK Planning Analysis

Citation-backed analysis of England's planning system identifying contradictions, bottlenecks, and opportunities for reform. Published as a static website on GitHub Pages.

## Current State (v1.0 MVP)

- 16 core legislation and regulation records
- 31 national policy, PPG topic, and NPS records (full energy NPS suite included)
- 6 pilot LPAs with 22 plan document records (including neighbourhood plans)
- Policy precedence hierarchy mapping for all 6 pilot authorities
- 22 issues in contradiction register across all 6 process stages (weighted-scored)
- 12 bottleneck records with severity heatmap by stage and pathway
- 11 recommendations with model drafting text and official evidence traces
- 12 evidence links to GOV.UK planning statistics and PINS data
- 12 official baseline metrics (England aggregate and pilot LPA breakdowns)
- 6 implementation roadmap milestones
- QA report with scenario testing across 3 development pathways
- Scale-out backlog for expansion to all 317 England LPAs
- 23 generated site pages including split audience views, bottleneck heatmap, and CSV/JSON exports
- Monthly automated freshness check (warning-only mode)

## Repository Structure

```
uk-planning/
├── AGENTS.md                        # Agent operating rules (commit, push, README hygiene)
├── IMPLEMENTATION_PLAN.md           # Phased delivery plan
├── RELEASE_NOTES.md                 # Version release notes
├── README.md                        # This file
├── data/
│   ├── evidence/
│   │   ├── official_baseline_metrics.csv
│   │   └── recommendation_evidence_links.csv
│   ├── issues/
│   │   ├── bottleneck-heatmap.csv
│   │   ├── contradiction-register.csv
│   │   ├── implementation-roadmap.csv
│   │   └── recommendations.csv
│   ├── legislation/
│   │   └── england-core-legislation.csv
│   ├── plans/
│   │   ├── pilot-lpas.csv
│   │   ├── pilot-plan-documents.csv
│   │   └── policy-hierarchy.csv     # Precedence mapping per pilot LPA
│   ├── policy/
│   │   └── england-national-policy.csv
│   └── schemas/
│       ├── datasets.json            # Schema with FK, enum, and unique-ID rules
│       └── scoring.json             # Explicit weighting for issue scoring
├── scripts/
│   ├── build_site.py                # Generates all site HTML from CSV data
│   ├── check_freshness.py           # Monthly URL and staleness checker (warn-only)
│   ├── check_links.py               # Internal link integrity checker
│   ├── serve_local.sh               # Build and serve on localhost
│   └── validate_data.py             # Schema, FK, enum, and unique-ID validation
├── content/
│   ├── methodology/
│   │   ├── qa-report.md             # QA report with scenario testing
│   │   └── scale-out-backlog.md     # Plan for expansion to all England LPAs
│   ├── recommendations/
│   │   └── model-text/              # Model drafting text for all 11 recommendations
│   └── templates/                   # Entry templates for legislation, plans, issues
├── site/                            # Generated static website (committed)
│   ├── assets/styles.css
│   ├── exports/                     # CSV and JSON exports of all datasets
│   └── *.html                       # 23 generated pages
└── .github/workflows/
    ├── ci.yml                       # PR and push: validate, build, link check
    ├── pages.yml                    # Push to main: same checks then deploy to GitHub Pages
    └── freshness.yml                # Monthly: URL and staleness check (warn-only)
```

## Run Locally

Build and serve in one step:

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
python3 scripts/validate_data.py   # schema, FK, enum, unique IDs
python3 scripts/build_site.py      # regenerate site from data
python3 scripts/check_links.py     # internal link integrity
```

Freshness check (warning-only, runs monthly in CI):

```bash
python3 scripts/check_freshness.py --warn-only
```

These checks also run automatically in GitHub Actions on every push and pull request.

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
| `plans.html` | Plan hierarchy and pilot LPA profiles |
| `contradictions.html` | Weighted-scored issue register with filters |
| `bottlenecks.html` | Process delay heatmap by stage and pathway |
| `recommendations.html` | Reform proposals with model text and evidence traces |
| `roadmap.html` | Delivery milestones (quick wins and statutory reforms) |
| `baselines.html` | Official KPI baselines from GOV.UK and PINS |
| `audience-policymakers.html` | View for policy makers |
| `audience-lpas.html` | View for local planning authorities |
| `audience-developers.html` | View for developers |
| `audience-public.html` | Plain-language public summary |
| `methodology.html` | Scoring model, evidence standards, and QA |
| `sources.html` | Full evidence and citation index |
| `exports.html` | CSV and JSON dataset download index |

## Hosting

Deployed automatically to GitHub Pages on push to `main` via `.github/workflows/pages.yml`.
