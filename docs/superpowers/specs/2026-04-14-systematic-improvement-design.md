# Systematic Improvement Plan — Design Spec

**Date:** 2026-04-14
**Status:** Approved

## Overview

Four sequential phases to transform the UK Planning Analysis site from a functional Python-string-concatenation static site into a maintainable, data-rich, polished platform with proper developer tooling. Each phase is a self-contained deliverable — the site works correctly at every checkpoint.

**Execution order:** A (Architecture) → B (Data Quality) → C (Frontend) → D (Developer Experience)
**Approach:** Incremental page-group migration (Approach 2) — no big bang rewrites.

---

## Phase A: Architecture — Custom Jinja2-Based Site Generator

### Problem

The `builders/` package totals 4,478 lines of Python, of which approximately 60% is HTML assembly via string concatenation. `page_authorities.py` alone is 1,528 lines. HTML structure is entangled with data logic, making changes to either risky and tedious. There is no separation between data preparation and rendering.

### Design

#### A.1: SiteBuilder Framework

A thin framework class that owns the build lifecycle, backed by Jinja2 templates.

**New directory structure:**

```
scripts/
├── build_site.py                    # Entry point (~20 lines final): instantiate SiteBuilder, call build()
├── site_builder.py                  # SiteBuilder class: Jinja2 env, data context, page routing
├── builders/
│   ├── __init__.py
│   ├── config.py                    # Paths, version, section nav (unchanged)
│   ├── data_loader.py               # CSV/JSON loading (unchanged)
│   ├── metrics.py                   # Pure metric functions (unchanged)
│   ├── export_utils.py              # Export manifest, report bundles (unchanged)
│   ├── html_helpers.py              # NEW: Jinja2 custom filters and globals
│   └── context_providers/           # NEW: data preparation for templates
│       ├── __init__.py
│       ├── overview.py              # Context for index, search pages
│       ├── analysis.py              # Context for contradictions, bottlenecks, appeals, baselines
│       ├── authorities.py           # Context for plans, benchmark, compare, reports, coverage, trends
│       ├── recommendations.py       # Context for recommendations, roadmap, consultation
│       ├── methods.py               # Context for methodology, sources, exports, data-health
│       └── audiences.py             # Context for audience-* pages
├── templates/                       # NEW: Jinja2 templates
│   ├── base.html                    # Master layout: head, nav, shell utilities, footer
│   ├── macros/
│   │   ├── badges.html              # badge(), confidence_badge(), provenance_badge()
│   │   ├── tables.html              # filterable_table(), sortable_headers()
│   │   ├── cards.html               # card_kpi(), card_guidance(), card_hero()
│   │   ├── filters.html             # filter_row(), filter_chips()
│   │   ├── navigation.html          # breadcrumbs(), mini_toc(), next_steps()
│   │   └── charts.html              # sparkline_svg()
│   ├── pages/                       # One template per page type
│   │   ├── index.html
│   │   ├── methodology.html
│   │   ├── ...
│   │   └── audience_public.html
│   └── partials/
│       ├── page_purpose.html        # Start-here guidance block
│       ├── data_trust_panel.html    # Trust info section
│       ├── plain_language.html      # Plain-language guide
│       └── detail_sidebar.html      # Sticky TOC for detail pages
```

**SiteBuilder responsibilities:**
- Initialize Jinja2 environment with template directory, custom filters, and globals
- Register context providers mapped to page names
- For each page: call context provider → render template → write output file
- Manage migration routing (old builder vs new template) during incremental migration

**Key separation principle:** Context providers prepare Python dicts of data. Templates render HTML from those dicts. No HTML in Python. No data logic in templates.

**html_helpers.py** registers Jinja2 custom filters and globals that replace the pure-function helpers currently in `html_utils.py`:
- `badge`, `confidence_badge`, `verification_badge`, `provenance_badge` → Jinja2 filters
- `sparkline_svg` → Jinja2 global callable
- `metric_help` → Jinja2 macro or filter
- `weighted_score` stays in `metrics.py` (data logic, not rendering)

#### A.2: Migration Mechanics

During migration, `build_site.py` has a routing table:

```python
TEMPLATE_PAGES = {"methodology", "sources"}  # grows each checkpoint
# All other pages use old builders

for page in ALL_PAGES:
    if page in TEMPLATE_PAGES:
        builder.render(page)
    else:
        old_builders[page]()
```

Once all pages are migrated, the routing layer and all old `page_*.py` modules are deleted.

**Verification per checkpoint:**
1. Migrate page group to templates
2. Run build, diff output against previous build
3. Accept intentional whitespace differences from Jinja2, update baseline snapshot
4. Run full CI check suite (validate, build, link check, metric drift, accessibility)
5. Commit and push

#### A.3: Migration Checkpoints

| Checkpoint | Pages | Rationale |
|---|---|---|
| **A.1** | Framework + `methodology.html` | Proves full pipeline on simplest content page. Establishes `base.html`, macros, `SiteBuilder`, one context provider. |
| **A.2** | `metric-methods.html`, `sources.html`, `exports.html`, `data-health.html` | Remaining Data & Methods pages. Same section, similar structure. Exercises table macros and data-health context. |
| **A.3** | `index.html`, `search.html`, `search-index.json` | Overview pages. Homepage is complex (KPI cards, section grids, hero) but no filter tables. Tests card macros. |
| **A.4** | `legislation.html`, `contradictions.html`, `bottlenecks.html`, `appeals.html`, `baselines.html` + 22 `contradiction-issue-*.html` | System Analysis. Exercises filter scripts, weighted scoring, detail page templates with sidebar TOC. |
| **A.5** | `recommendations.html`, `roadmap.html`, `consultation.html` + 11 `recommendation-rec-*.html` | Recommendations. Similar to A.4 but different data shape. |
| **A.6** | `plans.html`, 26 `plans-lpa-*.html`, `map.html`, `compare.html`, `benchmark.html`, `trends.html`, `reports.html`, `coverage.html` | Authority Insights — 35+ pages, heaviest data logic. By this point template patterns are battle-tested. |
| **A.7** | 4 `audience-*.html` + cleanup | Final pages. Delete old `page_*.py` modules, remove routing layer, delete `html_utils.py`. Update baseline snapshot. |

#### What Stays Unchanged

- `config.py` — paths, version, section navigation
- `data_loader.py` — CSV/JSON loading and data-health computation
- `metrics.py` — pure metric functions
- `export_utils.py` — JSON/CSV export, manifest generation

#### Expected Outcome

- Python code in `builders/`: ~1,800 lines (down from 4,478)
- 20-25 Jinja2 template files with shared macros
- `build_site.py` under 20 lines
- All 85 pages render correctly
- All existing CI checks pass

### Constraints

- Jinja2 is the only new dependency
- Every checkpoint produces a working, deployable site
- No intentional changes to page content or functionality during migration
- Existing validation, link check, metric drift, and accessibility checks must pass at every checkpoint

---

## Phase B: Data Quality & Completeness

### Problem

Coverage is at 26 LPAs. 10 contradiction records remain draft. Key benchmark metrics are analytical proxies. The GOV.UK ingest script checks freshness but doesn't pull data.

### Design

#### B.1: Cohort 4 Expansion

Add 8-10 new LPAs to bring total to 34-36. Selection criteria: geographic spread, authority type diversity, data availability (following existing `scale-out-backlog.md` pattern).

For each new LPA:
1. Add row to `pilot-lpas.csv` with full metadata
2. Add plan documents to `pilot-plan-documents.csv`
3. Add policy hierarchy entries to `policy-hierarchy.csv`
4. Add geo coordinates to `lpa-geo.csv`
5. Add data quality tier (B or C initially) to `lpa-data-quality.csv`
6. Add quarterly trend data to `lpa-quarterly-trends.csv`
7. Add issue incidence rows to `lpa-issue-incidence.csv`
8. Run onboarding pipeline, commit artifacts
9. Update schema if new enum values needed

**Cohort function refactor:** Replace hardcoded sets in `cohort_for_pid()` with data-driven lookup from `pilot-lpas.csv` (add `cohort` column). This supports arbitrary future cohorts without code changes.

#### B.2: Verification Push

Review remaining 10 draft contradiction records against source citations. Target: upgrade 7+ to `verified`.

For each upgrade:
- Verify every `linked_instruments` reference resolves
- Verify `source_url` citations are live and accessible
- Add `verification_notes` field to contradiction register (schema update required)
- Update `verification_state` from `draft` to `verified`

Leave records with genuinely thin evidence as `draft`.

#### B.3: Official Metric Replacement

Replace proxy metrics where GOV.UK publishes official equivalents:
- `validation_rework_proxy` → official PS2 validation return rates
- `delegated_ratio_proxy` → official delegated decision percentages

Implementation in `metrics.py`: check for official values in trend data before falling back to proxy formula. Update confidence badges from `medium`/`low` to `high` for replaced metrics. Proxy formulas remain as fallback where official data is unavailable.

#### B.4: Automated Ingest Pipeline

Upgrade `ingest_govuk_stats.py` from freshness checker to full data pipeline:
- Download PS1/PS2 live table CSVs programmatically
- Parse, validate, and map to internal schema fields
- Write updated rows to `official_baseline_metrics.csv` and `lpa-quarterly-trends.csv`
- Generate diff report showing what changed
- Append run history to `stats-ingest-history.json`
- Upgrade `stats-ingest.yml` CI workflow to run full pipeline quarterly

### Constraints

- New LPAs enter as quality tier B or C (not A) until verified
- Proxy metrics remain as fallback where official data unavailable
- Schema must be updated before data changes
- Only upgrade to `verified` where citation chain is complete and checkable

---

## Phase C: Frontend & Asset Pipeline

### Problem

After Phase A, inline `<script>` blocks are generated by Jinja2 templates (migrated from the old Python builders), duplicating the same JS patterns across 85 HTML files. CSS has potential dead selectors from earlier phases. Fonts are externally hosted. No asset minification or build step.

### Design

#### C.1: JavaScript Consolidation

Extract inline template scripts into shared JS modules:

```
site/assets/
├── shell.js          # Existing: view mode, nav, copy, events, comparison history
├── filters.js        # NEW: extracted from render_filter_script()
├── tables.js         # NEW: extracted from render_table_enhancements_script()
├── drawers.js        # NEW: extracted from render_mobile_drawer_script()
└── main.js           # NEW: entry point, initialises modules based on page data attributes
```

Templates declare capabilities via `data-features` attribute on `<body>` (e.g., `data-features="filters tables drawers"`). `main.js` reads this and initialises relevant modules. Inline `<script>` blocks are eliminated from all generated HTML.

#### C.2: Design System Tightening

- Audit `styles.css` for unused rules and remove dead selectors
- Standardise spacing tokens — replace hardcoded `px` values with CSS custom properties
- Add dark mode via `prefers-color-scheme` media query using existing CSS custom properties (`--bg`, `--surface`, `--ink`, `--accent`, etc.)
- Self-host Source Sans 3 font files — copy WOFF2 files to `site/assets/fonts/`, update `@font-face` rules, remove Google Fonts `<link>` tags
- Improve mobile table experience — reduce horizontal scroll dependency

#### C.3: Asset Build Step

Add `esbuild` as a lightweight bundler:

```
scripts/
├── build_assets.sh    # NEW: runs esbuild, copies fonts
```

Responsibilities:
- Bundle JS modules into a single minified `main.min.js`
- Minify `styles.css` into `styles.min.css`
- Copy self-hosted font files to `site/assets/fonts/`
- Templates reference `.min.` files in production, unminified in dev (`serve_local.sh`)

The Python build calls `build_assets.sh` as a post-step. `esbuild` is a single binary with no `node_modules` tree.

### Constraints

- No JS framework — vanilla JS only
- `esbuild` is the only new frontend dependency
- Static site output, no runtime server
- All pages must function without JS (progressive enhancement)

---

## Phase D: Developer Experience & Workflow Automation

### Problem

No declared Python dependencies. CI doesn't run pytest. Test coverage is shallow (25 tests covering only utility functions, zero tests for page builders). No pre-commit hooks. Stale `__pycache__/` directories committed. Report files clutter the root directory.

### Design

#### D.1: Project Foundation

**`pyproject.toml`** as single source of truth:

```toml
[project]
name = "uk-planning"
version = "15.0"
requires-python = ">=3.12"
dependencies = ["jinja2>=3.1"]

[project.optional-dependencies]
dev = ["pytest>=9.0", "ruff>=0.4"]

[tool.ruff]
target-version = "py312"

[tool.pytest.ini_options]
testpaths = ["scripts/tests"]
```

**Cleanup:**
- Update `.gitignore` to catch `__pycache__/` recursively and all report output files
- Remove committed `__pycache__/` directories from git tracking
- Move root-level report files (`metric-stability-report.*`, `freshness-report.txt`, etc.) to a `reports/` output directory, update scripts accordingly
- `BUILD_VERSION` in `config.py` reads from `pyproject.toml` instead of being hardcoded

#### D.2: Meaningful Test Coverage

New test files:

| Test file | Coverage |
|---|---|
| `test_context_providers.py` | Each context provider returns expected dict shape with required keys. Tests with minimal fixture data. |
| `test_template_rendering.py` | Each template renders without error given its context. Output contains expected structural elements (correct `<title>`, nav present, tables where expected, no empty `<tbody>`). |
| `test_site_integration.py` | Full build produces expected file set. All HTML passes basic structural validation. Replaces MD5-hash regression test with structural checks. |
| `test_ingest_pipeline.py` | Ingest script parses sample GOV.UK response correctly. Diff report and history append work. |
| `test_asset_build.py` | Asset build produces minified outputs. Font files present. |

Existing tests updated to reflect new module structure (`test_html_utils.py` → `test_html_helpers.py`).

#### D.3: Workflow Automation

**CI updates** (`ci.yml`):
- Add `pip install -e ".[dev]"` step
- Add `pytest scripts/tests/ -v` step
- Add `ruff check scripts/` step
- Add asset build verification step

**Makefile** for common operations:

```makefile
build        ## Build site and assets
validate     ## Run data validation
test         ## Run pytest suite
lint         ## Run ruff check
check        ## Run all checks (validate, build, lint, test, links, accessibility)
serve        ## Start local dev server
clean        ## Remove generated artifacts
```

**Pre-commit hooks** via `.pre-commit-config.yaml`:
- `ruff check` and `ruff format --check` on Python files
- `validate_data.py` when CSV files change
- Build verification when `templates/` or `builders/` change

**README.md updates:**
- Setup instructions (`pip install -e ".[dev]"`)
- `make check` as the single pre-commit command
- Template development workflow (edit template → build → preview)

### Constraints

- No dependencies beyond Jinja2 (runtime) + pytest + ruff (dev) + esbuild (frontend)
- Pre-commit hooks must not add more than a few seconds to commit time
- All existing CI checks continue to pass

---

## Success Criteria

| Phase | Criteria |
|---|---|
| **A** | All 85 pages render correctly via Jinja2 templates. `build_site.py` under 20 lines. Python builders under 1,800 lines. All CI checks pass. Old `page_*.py` modules deleted. |
| **B** | 34-36 LPAs in dataset. 7+ additional contradiction records upgraded to `verified`. At least 2 proxy metrics replaced with official data. Ingest pipeline runs end-to-end. |
| **C** | Zero inline `<script>` blocks in generated HTML. Dark mode functional. Fonts self-hosted. Assets minified. All pages function without JS. |
| **D** | `pyproject.toml` present. `pytest` in CI. 50+ tests covering context providers, templates, and integration. `make check` runs full validation suite. Pre-commit hooks active. |

## Dependency Chain

```
Phase A (Architecture) ← required before all others
  └── Phase B (Data Quality) ← can proceed once A is complete
        └── Phase C (Frontend) ← depends on templates from A being stable
              └── Phase D (Developer Experience) ← final layer, depends on stable C asset pipeline
```

Phases are strictly sequential. Each phase ships independently as a working, deployable site.
