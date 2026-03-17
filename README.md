# UK Planning Analysis

Citation-backed analysis of England's planning system identifying contradictions, bottlenecks, and opportunities for reform. Published as a static website on GitHub Pages.

## Current State

- 16 core legislation and regulation records
- 20 national policy and PPG topic records
- 6 pilot LPAs with 18 plan document records
- 5 issues in contradiction register (weighted-scored, confidence and verification state)
- 5 recommendations with official evidence traces (GOV.UK planning statistics and PINS data)
- 12 official baseline metrics (England aggregate and pilot LPA breakdowns)
- 6 implementation roadmap milestones
- 20 generated site pages including split audience views and CSV/JSON exports
- Monthly automated freshness check (warning-only mode)

## Repository Structure

```
uk-planning/
├── AGENTS.md                        # Agent operating rules (commit, push, README hygiene)
├── IMPLEMENTATION_PLAN.md           # Phased delivery plan
├── README.md                        # This file
├── data/
│   ├── evidence/
│   │   ├── official_baseline_metrics.csv
│   │   └── recommendation_evidence_links.csv
│   ├── issues/
│   │   ├── contradiction-register.csv
│   │   ├── implementation-roadmap.csv
│   │   └── recommendations.csv
│   ├── legislation/
│   │   └── england-core-legislation.csv
│   ├── plans/
│   │   ├── pilot-lpas.csv
│   │   └── pilot-plan-documents.csv
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
├── site/                            # Generated static website (committed)
│   ├── assets/styles.css
│   ├── exports/                     # CSV and JSON exports of all datasets
│   └── *.html                       # 20 generated pages
├── content/                         # Source markdown and templates
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
| `recommendations.html` | Reform proposals with evidence traces |
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
