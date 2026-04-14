# Phase A: Architecture Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate all 85 HTML pages from Python string concatenation to Jinja2 templates via an incremental page-group migration, establishing a clean separation between data logic (context providers) and rendering (templates).

**Architecture:** A `SiteBuilder` class manages the Jinja2 environment, loads data via context providers, and renders templates. During migration, a routing layer in `build_site.py` dispatches each page to either the old builder function or the new template renderer. Pages migrate in groups, one checkpoint at a time.

**Tech Stack:** Python 3.12, Jinja2 3.1+, pytest 9.0+, ruff

**Design spec:** `docs/superpowers/specs/2026-04-14-systematic-improvement-design.md`

---

## File Structure

### New files to create

```
scripts/
├── site_builder.py                          # SiteBuilder class
├── builders/
│   ├── html_helpers.py                      # Jinja2 custom filters and globals
│   └── context_providers/
│       ├── __init__.py
│       ├── methods.py                       # Context for methodology, metric-methods, sources, exports, data-health
│       ├── overview.py                      # Context for index, search
│       ├── analysis.py                      # Context for legislation, contradictions, bottlenecks, appeals, baselines + detail pages
│       ├── recommendations.py               # Context for recommendations, roadmap, consultation + detail pages
│       ├── authorities.py                   # Context for plans, profiles, map, compare, benchmark, trends, reports, coverage
│       └── audiences.py                     # Context for audience-* pages
├── templates/
│   ├── base.html                            # Master layout
│   ├── macros/
│   │   ├── badges.html
│   │   ├── tables.html
│   │   ├── cards.html
│   │   ├── filters.html
│   │   ├── navigation.html
│   │   └── charts.html
│   ├── pages/
│   │   ├── methodology.html
│   │   ├── metric_methods.html
│   │   ├── sources.html
│   │   ├── exports.html
│   │   ├── data_health.html
│   │   ├── index.html
│   │   ├── search.html
│   │   ├── legislation.html
│   │   ├── contradictions.html
│   │   ├── contradiction_detail.html
│   │   ├── bottlenecks.html
│   │   ├── appeals.html
│   │   ├── baselines.html
│   │   ├── recommendations.html
│   │   ├── recommendation_detail.html
│   │   ├── roadmap.html
│   │   ├── consultation.html
│   │   ├── plans.html
│   │   ├── plans_detail.html
│   │   ├── map.html
│   │   ├── compare.html
│   │   ├── benchmark.html
│   │   ├── trends.html
│   │   ├── reports.html
│   │   ├── coverage.html
│   │   ├── audience_policymakers.html
│   │   ├── audience_lpas.html
│   │   ├── audience_developers.html
│   │   └── audience_public.html
│   └── partials/
│       ├── page_purpose.html
│       ├── data_trust_panel.html
│       └── plain_language.html
```

### Files to modify

- `scripts/build_site.py` — add routing layer, then simplify to final form
- `scripts/builders/__init__.py` — no change needed

### Files to delete (at A.7 cleanup)

- `scripts/builders/html_utils.py`
- `scripts/builders/page_overview.py`
- `scripts/builders/page_analysis.py`
- `scripts/builders/page_authorities.py`
- `scripts/builders/page_recommendations.py`
- `scripts/builders/page_methods.py`
- `scripts/builders/page_audiences.py`
- `scripts/builders/page_trends.py`

### Files that stay unchanged

- `scripts/builders/config.py`
- `scripts/builders/data_loader.py`
- `scripts/builders/metrics.py`
- `scripts/builders/export_utils.py`

---

## Task 1: Add Jinja2 Dependency

**Files:**
- Create: `pyproject.toml`

- [ ] **Step 1: Create pyproject.toml with Jinja2 dependency**

```toml
[project]
name = "uk-planning"
version = "14.0"
requires-python = ">=3.12"
dependencies = ["jinja2>=3.1"]

[project.optional-dependencies]
dev = ["pytest>=9.0", "ruff>=0.4"]

[tool.ruff]
target-version = "py312"

[tool.pytest.ini_options]
testpaths = ["scripts/tests"]
```

- [ ] **Step 2: Install the project in editable mode**

Run: `pip install -e ".[dev]"`
Expected: Jinja2 and dev dependencies installed successfully.

- [ ] **Step 3: Verify Jinja2 is importable**

Run: `python3 -c "import jinja2; print(jinja2.__version__)"`
Expected: Version 3.1.x or higher printed.

- [ ] **Step 4: Verify existing tests still pass**

Run: `pytest scripts/tests/ -v`
Expected: All 25 tests pass.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add pyproject.toml with Jinja2 dependency"
git push origin main
```

---

## Task 2: Create SiteBuilder Framework

**Files:**
- Create: `scripts/site_builder.py`
- Create: `scripts/builders/html_helpers.py`
- Create: `scripts/builders/context_providers/__init__.py`
- Create: `scripts/templates/` directory structure

- [ ] **Step 1: Create template directory structure**

Run:
```bash
mkdir -p scripts/templates/macros scripts/templates/pages scripts/templates/partials
```

- [ ] **Step 2: Create html_helpers.py with Jinja2 filters**

Create `scripts/builders/html_helpers.py`. These are the pure rendering helpers from `html_utils.py` re-expressed as Jinja2 filters and globals:

```python
"""Jinja2 custom filters and globals for template rendering."""
import html as html_lib
import json

from .config import BUILD_VERSION, SECTION_CONFIG, PAGE_TO_SECTION
from .metrics import issue_detail_page, recommendation_detail_page


# --- Badge filters ---

def badge(label, css_class):
    return f'<span class="badge badge-{css_class}">{html_lib.escape(label)}</span>'


def confidence_badge(level):
    colors = {"high": "green", "medium": "amber", "low": "red"}
    return badge(level, colors.get(level, "grey"))


def verification_badge(state):
    colors = {"draft": "grey", "verified": "green", "legal-reviewed": "blue"}
    return badge(state, colors.get(state, "grey"))


def provenance_badge(kind):
    labels = {
        "official": ("Official stats", "blue"),
        "estimated": ("Analytical estimate", "amber"),
    }
    label, css = labels.get(kind, ("Unknown provenance", "grey"))
    return badge(label, css)


def metric_help(label, description, method_anchor=None):
    escaped_desc = html_lib.escape(description)
    method_link = ""
    if method_anchor:
        method_link = (
            f' <a class="inline-help-link" '
            f'href="metric-methods.html#{html_lib.escape(method_anchor)}">method</a>'
        )
    return (
        f'{html_lib.escape(label)} '
        f'<span class="inline-help" tabindex="0" role="note" '
        f'aria-label="{escaped_desc}" title="{escaped_desc}">?</span>'
        f'{method_link}'
    )


# --- Chart helpers ---

def sparkline_svg(values, width=120, height=28):
    if not values:
        return ""
    nums = [float(v) for v in values]
    vmin = min(nums)
    vmax = max(nums)
    span = (vmax - vmin) if vmax != vmin else 1.0
    points = []
    for i, n in enumerate(nums):
        x = (i / (len(nums) - 1)) * (width - 2) + 1 if len(nums) > 1 else width / 2
        y = height - (((n - vmin) / span) * (height - 6) + 3)
        points.append(f"{x:.1f},{y:.1f}")
    pts = " ".join(points)
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="trend sparkline">'
        f'<polyline points="{pts}" fill="none" stroke="#00695c" stroke-width="2" />'
        f'</svg>'
    )


# --- Cell rendering ---

URL_COLUMNS = {"source_url", "url"}
TRUNCATE_COLUMNS = {"summary", "inspector_finding"}


def render_cell(key, value):
    if key in URL_COLUMNS and value and (value.startswith("http://") or value.startswith("https://")):
        escaped = html_lib.escape(value)
        return f'<a href="{escaped}" target="_blank" rel="noopener noreferrer">Link</a>'
    if key == "issue_id" and value:
        href = issue_detail_page(value)
        return f'<a href="{html_lib.escape(href)}">{html_lib.escape(value)}</a>'
    if key == "recommendation_id" and value:
        href = recommendation_detail_page(value)
        return f'<a href="{html_lib.escape(href)}">{html_lib.escape(value)}</a>'
    if key in TRUNCATE_COLUMNS and value:
        return f'<div class="cell-truncate">{html_lib.escape(value)}</div>'
    return html_lib.escape(value)


# --- Navigation helpers ---

def default_breadcrumbs(active):
    section = PAGE_TO_SECTION.get(active, "overview")
    crumbs = [("index.html", "Overview")]
    if active == "index":
        return crumbs
    section_href = SECTION_CONFIG[section]["href"]
    crumbs.append((section_href, SECTION_CONFIG[section]["label"]))
    for key, label, href in SECTION_CONFIG[section]["children"]:
        if key == active:
            if href != section_href:
                crumbs.append((href, label))
            break
    return crumbs


DEFAULT_PURPOSE = {
    "methodology": {
        "what": "How scoring, evidence standards, and quality controls are applied.",
        "who": "Users who need to validate analytical rigor and assumptions.",
        "how": "Read scoring dimensions first, then review quality checks and limitations.",
        "data": "Method definitions are versioned in schema and scoring files and reflected in generated outputs.",
    },
    "metric-methods": {
        "what": "Per-metric definitions, formulas, provenance, and confidence rules used in benchmark and report outputs.",
        "who": "Analysts, policy teams, and reviewers validating interpretation and comparability.",
        "how": "Open a metric section from tooltip method links, then verify formula scope and provenance before comparing LPAs.",
        "data": "Formulas are implemented in scripts/build_site.py and draw from trend, issue, quality, and plan-document datasets.",
    },
    "sources": {
        "what": "Source index and citations used across the site.",
        "who": "Users verifying data origin and citation reliability.",
        "how": "Use source categories and links to verify a metric, issue, or recommendation claim.",
        "data": "Entries include source URLs and retrieval timestamps where available.",
    },
    "exports": {
        "what": "Machine-readable dataset downloads plus manifest metadata.",
        "who": "Analysts and technical users reusing the data externally.",
        "how": "Download CSV or JSON datasets, then check manifest.json for hashes and version metadata.",
        "data": "Export artifacts are generated during site build and tied to versioned source datasets.",
    },
    "data-health": {
        "what": "Freshness status for core datasets and update age in days.",
        "who": "Anyone assessing confidence before relying on metrics or rankings.",
        "how": "Check status badges and age values, then prioritize stale or critical datasets for refresh.",
        "data": "Health is computed from date fields in monitored datasets against configured thresholds.",
    },
}
# NOTE: Remaining page purposes will be added in later tasks as pages migrate.
# Copy from the full dict in html_utils.py:default_purpose() for each page.


def register_helpers(env):
    """Register all custom filters and globals on a Jinja2 Environment."""
    env.filters["badge"] = badge
    env.filters["confidence_badge"] = confidence_badge
    env.filters["verification_badge"] = verification_badge
    env.filters["provenance_badge"] = provenance_badge
    env.filters["render_cell"] = render_cell

    env.globals["badge"] = badge
    env.globals["confidence_badge"] = confidence_badge
    env.globals["verification_badge"] = verification_badge
    env.globals["provenance_badge"] = provenance_badge
    env.globals["metric_help"] = metric_help
    env.globals["sparkline_svg"] = sparkline_svg
    env.globals["render_cell"] = render_cell
    env.globals["default_breadcrumbs"] = default_breadcrumbs
    env.globals["DEFAULT_PURPOSE"] = DEFAULT_PURPOSE
    env.globals["BUILD_VERSION"] = BUILD_VERSION
    env.globals["SECTION_CONFIG"] = SECTION_CONFIG
    env.globals["PAGE_TO_SECTION"] = PAGE_TO_SECTION
```

- [ ] **Step 3: Create context_providers/__init__.py**

Create `scripts/builders/context_providers/__init__.py`:

```python
"""Context providers prepare template data dicts. No HTML generation here."""
```

- [ ] **Step 4: Create SiteBuilder class**

Create `scripts/site_builder.py`:

```python
"""SiteBuilder: Jinja2-based static site generator for uk-planning."""
import sys
from pathlib import Path

import jinja2

sys.path.insert(0, str(Path(__file__).resolve().parent))

from builders.config import SITE
from builders.html_helpers import register_helpers


class SiteBuilder:
    def __init__(self, template_dir=None):
        if template_dir is None:
            template_dir = Path(__file__).resolve().parent / "templates"
        self.template_dir = template_dir
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        register_helpers(self.env)
        self._pages = {}

    def register(self, page_name, template_path, context_fn):
        """Register a page: name, template file path, and a callable returning a context dict."""
        self._pages[page_name] = (template_path, context_fn)

    def render_page(self, page_name):
        """Render a single registered page and write to site/."""
        template_path, context_fn = self._pages[page_name]
        template = self.env.get_template(template_path)
        context = context_fn()
        html = template.render(**context)
        out_path = SITE / context.get("output_filename", f"{page_name}.html")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")

    def render_all(self):
        """Render all registered pages."""
        for page_name in self._pages:
            self.render_page(page_name)

    @property
    def registered_pages(self):
        return set(self._pages.keys())
```

- [ ] **Step 5: Verify imports work**

Run: `python3 -c "from site_builder import SiteBuilder; print('OK')"` (from `scripts/` dir)
Expected: `OK`

Run: `python3 -c "from builders.html_helpers import register_helpers; print('OK')"` (from `scripts/` dir)
Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add scripts/site_builder.py scripts/builders/html_helpers.py scripts/builders/context_providers/__init__.py scripts/templates/
git commit -m "feat: add SiteBuilder framework, html_helpers, and template directory structure"
git push origin main
```

---

## Task 3: Create Base Template and Macros

**Files:**
- Create: `scripts/templates/base.html`
- Create: `scripts/templates/macros/badges.html`
- Create: `scripts/templates/macros/cards.html`
- Create: `scripts/templates/macros/tables.html`
- Create: `scripts/templates/macros/filters.html`
- Create: `scripts/templates/macros/navigation.html`
- Create: `scripts/templates/macros/charts.html`
- Create: `scripts/templates/partials/page_purpose.html`
- Create: `scripts/templates/partials/data_trust_panel.html`
- Create: `scripts/templates/partials/plain_language.html`

- [ ] **Step 1: Create base.html master layout**

This is the Jinja2 equivalent of the `page()` function in `html_utils.py`. Create `scripts/templates/base.html`:

```html
{# Master layout — equivalent of html_utils.page() #}
{% set section = PAGE_TO_SECTION.get(active, "overview") %}
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{ title }}</title>
    <link rel="stylesheet" href="assets/styles.css" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet" />
    {% block head_extra %}{% endblock %}
  </head>
  <body>
    <a class="skip-link" href="#main-content">Skip to main content</a>
    <a class="skip-link" href="#filters-start">Skip to filters</a>
    <a class="skip-link" href="#table-start">Skip to data table</a>
    <a class="skip-link" href="#evidence-start">Skip to evidence</a>
    <div class="layout">
      <header>
        <h1>{{ title }}</h1>
        <p class="subhead">{{ subhead }}</p>
        <div class="header-search"><span class="search-icon" aria-hidden="true">&#128269;</span><a href="search.html">Search</a></div>
      </header>
      <button class="nav-hamburger" aria-label="Toggle navigation" aria-expanded="true">&#9776;</button>
      <div class="nav-panel nav-panel--open">
        <nav class="top-nav" aria-label="Main sections">
          {% for key, cfg in SECTION_CONFIG.items() if key != "audiences" %}
          <a class="top-tab{{ ' active' if key == section else '' }}" href="{{ cfg.href }}">{{ cfg.label }}</a>
          {% endfor %}
        </nav>
        <nav class="sub-nav" aria-label="Section pages">
          {% for key, label, href in SECTION_CONFIG[section].children %}
          <a{{ ' class="active"' if key == active else '' }} href="{{ href }}">{{ label }}</a>
          {% endfor %}
        </nav>
      </div>
      {% include "partials/_breadcrumbs.html" %}
      <button type="button" class="print-export" onclick="window.print()">Print / PDF</button>
      {% include "partials/_shell_utilities.html" %}
      <main id="main-content">
        {% include "partials/plain_language.html" %}
        {% if purpose %}
        {% include "partials/page_purpose.html" %}
        {% endif %}
        {% if context_text %}
        <section class="card guided-only"><p>{{ context_text }}</p></section>
        {% endif %}
        {% if show_trust_panel %}
        {% include "partials/data_trust_panel.html" %}
        {% endif %}
        {% block content %}{% endblock %}
        {% if next_steps %}
        <section class="card guided-only"><h2>Next actions</h2><ul>
          {% for href, label in next_steps %}
          <li><a href="{{ href }}">{{ label }}</a></li>
          {% endfor %}
        </ul></section>
        {% endif %}
      </main>
      {% include "partials/_footer.html" %}
    </div>
    <button id="back-to-top" class="back-to-top" aria-label="Back to top" style="display:none;">&uarr;</button>
    <script src="assets/shell.js"></script>
    {% block scripts %}{% endblock %}
  </body>
</html>
```

- [ ] **Step 2: Create partials used by base.html**

Create `scripts/templates/partials/_breadcrumbs.html`:

```html
{% set crumbs = breadcrumbs if breadcrumbs is defined and breadcrumbs else default_breadcrumbs(active) %}
<div class="breadcrumbs">
  {% for href, label in crumbs %}
  <a href="{{ href }}">{{ label }}</a>{{ " &gt; " if not loop.last else "" }}
  {% endfor %}
</div>
```

Create `scripts/templates/partials/_shell_utilities.html`:

```html
<section class="shell-utilities">
  <button type="button" class="utility-toggle" aria-expanded="true">Settings &amp; trust info</button>
  <div class="utility-body">
    <div class="utility-row">
      <label>View mode
        <select id="view-mode-toggle" aria-label="Toggle guided or expert mode">
          <option value="guided">Guided</option>
          <option value="expert">Expert</option>
        </select>
      </label>
      <label><input type="checkbox" id="plain-language-toggle" /> Plain-language mode</label>
      <button type="button" data-copy-view>Copy this view</button>
    </div>
    <p class="small">Trust legend:
      {{ provenance_badge("official") }} Official statistic
      {{ provenance_badge("estimated") }} Analytical estimate
      {{ confidence_badge("high") }} Confidence example
    </p>
  </div>
</section>
```

Create `scripts/templates/partials/_footer.html`:

```html
<footer class="site-footer">
  <div class="footer-inner">
    <nav class="footer-nav" aria-label="Footer navigation">
      {% for key, cfg in SECTION_CONFIG.items() if key != "audiences" %}
      <a href="{{ cfg.href }}">{{ cfg.label }}</a>
      {% endfor %}
      <a href="search.html">Search</a>
      <a href="audience-policymakers.html">For Audiences</a>
    </nav>
    <div class="footer-meta">
      <p>{{ BUILD_VERSION }} &middot; Built with open data &middot;
        <a href="methodology.html">Methodology</a> &middot;
        <a href="data-health.html">Data Health</a> &middot;
        <a href="exports.html">Exports</a></p>
    </div>
  </div>
</footer>
```

- [ ] **Step 3: Create page_purpose.html partial**

Create `scripts/templates/partials/page_purpose.html`:

```html
<section class="card card-guidance guided-only">
  <h2>Start here</h2>
  <dl class="purpose-grid">
    <dt>What this page shows</dt><dd>{{ purpose.what }}</dd>
    <dt>Who this is for</dt><dd>{{ purpose.who }}</dd>
    <dt>How to interpret</dt><dd>{{ purpose.how }}</dd>
    <dt>Data trust and freshness</dt><dd>{{ purpose.data }}</dd>
  </dl>
</section>
```

- [ ] **Step 4: Create plain_language.html partial**

Create `scripts/templates/partials/plain_language.html`:

```html
<section class="card plain-language-panel">
  <h2>Plain-language guide</h2>
  <p>This page helps you understand <strong>{{ title }}</strong> without specialist planning jargon.
     Use the start-here notes first, then open linked detail pages for evidence and next actions.</p>
  <p class="small">Common terms: <strong>s106</strong> (legal agreement on development obligations),
     <strong>NSIP</strong> (nationally significant infrastructure project),
     <strong>verification state</strong> (draft or reviewed data status).</p>
</section>
```

- [ ] **Step 5: Create data_trust_panel.html partial**

Create `scripts/templates/partials/data_trust_panel.html`:

```html
{% if trust_panel_rows %}
{% set oldest = trust_panel_rows|sort(attribute='sort_age', reverse=true)|first %}
<section class="card card-guidance guided-only">
  <h3>Data trust panel</h3>
  <p><strong>Source tiers:</strong> Official statistics, administrative references, analytical estimates.</p>
  <p><strong>Known caveat:</strong> Some authority metrics are estimated proxies and should be interpreted directionally.</p>
  <p><strong>Latest trust check:</strong> Oldest monitored dataset: {{ oldest.dataset }} ({{ oldest.age_days }} days)</p>
  <p class="small">See methodology and metric-methods for full caveat details.</p>
</section>
{% endif %}
```

- [ ] **Step 6: Create macro templates**

Create `scripts/templates/macros/badges.html`:

```html
{% macro badge_html(label, css_class) %}
<span class="badge badge-{{ css_class }}">{{ label }}</span>
{% endmacro %}

{% macro confidence_badge_html(level) %}
{% set colors = {"high": "green", "medium": "amber", "low": "red"} %}
{{ badge_html(level, colors.get(level, "grey")) }}
{% endmacro %}

{% macro verification_badge_html(state) %}
{% set colors = {"draft": "grey", "verified": "green", "legal-reviewed": "blue"} %}
{{ badge_html(state, colors.get(state, "grey")) }}
{% endmacro %}
```

Create `scripts/templates/macros/tables.html`:

```html
{% macro data_table(rows, columns, table_id="") %}
<section class="card"{% if table_id %} id="table-start"{% endif %}>
  <table{% if table_id %} id="{{ table_id }}" class="dense-table"{% endif %}>
    <thead><tr>
      {% for key, label in columns %}
      <th>{{ label }}</th>
      {% endfor %}
    </tr></thead>
    <tbody>
      {% for row in rows %}
      <tr{% if data_attrs %} {{ data_attrs(row) }}{% endif %}>
        {% for key, label in columns %}
        <td>{{ render_cell(key, row.get(key, "") or "") }}</td>
        {% endfor %}
      </tr>
      {% endfor %}
    </tbody>
  </table>
</section>
{% endmacro %}

{% macro table_guide(title, bullets) %}
<section class="card">
  <h3>{{ title }}</h3>
  <ul>
    {% for item in bullets %}
    <li>{{ item }}</li>
    {% endfor %}
  </ul>
</section>
{% endmacro %}
```

Create `scripts/templates/macros/cards.html`:

```html
{% macro card_kpi(title, value, source_line) %}
<article class="card card-kpi">
  <h3>{{ title }}</h3>
  <p class="kpi-value">{{ value }}</p>
  <p class="small">Source: {{ source_line }}</p>
</article>
{% endmacro %}

{% macro card_hero(title, text) %}
<section class="card card-hero">
  <h2>{{ title }}</h2>
  <p>{{ text }}</p>
</section>
{% endmacro %}

{% macro card_guidance(title, content) %}
<section class="card card-guidance guided-only">
  <h2>{{ title }}</h2>
  {{ content }}
</section>
{% endmacro %}
```

Create `scripts/templates/macros/filters.html`:

```html
{% macro filter_row(table_id, text_label, filter_defs) %}
<section class="card" id="filters-start">
  <div class="filter-row">
    <label class="filter-item">{{ text_label }}
      <input type="search" aria-label="{{ text_label }}" data-table="{{ table_id }}" data-filter="search" placeholder="Type to search..." />
    </label>
    {% for field, label, options in filter_defs %}
    <label class="filter-item">{{ label }}
      <select data-table="{{ table_id }}" data-filter="{{ field }}">
        <option value="">All</option>
        {% for opt in options %}
        <option>{{ opt }}</option>
        {% endfor %}
      </select>
    </label>
    {% endfor %}
  </div>
  <p class="small" data-filter-count-for="{{ table_id }}" aria-live="polite" role="status"></p>
</section>
{% endmacro %}
```

Create `scripts/templates/macros/navigation.html`:

```html
{% macro detail_toc(items) %}
<section class="card detail-toc" aria-label="Detail page sections">
  <h3>On this page</h3>
  <div class="detail-toc-links">
    {% for anchor, label in items %}
    <a href="#{{ anchor }}">{{ label }}</a>
    {% endfor %}
  </div>
</section>
{% endmacro %}

{% macro metric_context_block(items) %}
<section class="card guided-only" id="evidence-start">
  <h3>Metric context</h3>
  <table><thead><tr><th>Metric</th><th>Definition</th><th>Why it matters</th><th>Source and confidence</th></tr></thead>
  <tbody>
    {% for item in items %}
    <tr>
      <td>{{ item.metric }}</td>
      <td>{{ item.definition }}</td>
      <td>{{ item.why }}</td>
      <td>{{ item.source }}</td>
    </tr>
    {% endfor %}
  </tbody></table>
</section>
{% endmacro %}
```

Create `scripts/templates/macros/charts.html`:

```html
{% macro sparkline(values, width=120, height=28) %}
{{ sparkline_svg(values, width, height) }}
{% endmacro %}
```

- [ ] **Step 7: Commit**

```bash
git add scripts/templates/
git commit -m "feat: add base template, macros, and partials for Jinja2 rendering"
git push origin main
```

---

## Task 4: Write Tests for SiteBuilder and Helpers

**Files:**
- Create: `scripts/tests/test_site_builder.py`
- Create: `scripts/tests/test_html_helpers.py`

- [ ] **Step 1: Write SiteBuilder unit tests**

Create `scripts/tests/test_site_builder.py`:

```python
"""Tests for SiteBuilder framework."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from site_builder import SiteBuilder


@pytest.fixture
def tmp_builder(tmp_path):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    (template_dir / "test.html").write_text("Hello {{ name }}!")
    return SiteBuilder(template_dir=template_dir)


def test_register_page(tmp_builder):
    tmp_builder.register("test", "test.html", lambda: {"name": "World", "output_filename": "test.html"})
    assert "test" in tmp_builder.registered_pages


def test_render_page(tmp_builder, tmp_path):
    import builders.config as config
    original_site = config.SITE
    config.SITE = tmp_path / "site"
    config.SITE.mkdir()
    try:
        tmp_builder.register("test", "test.html", lambda: {"name": "World", "output_filename": "test.html"})
        tmp_builder.render_page("test")
        output = (config.SITE / "test.html").read_text()
        assert "Hello World!" == output
    finally:
        config.SITE = original_site
```

- [ ] **Step 2: Write html_helpers unit tests**

Create `scripts/tests/test_html_helpers.py`:

```python
"""Tests for Jinja2 html_helpers."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from builders.html_helpers import (
    badge, confidence_badge, verification_badge, provenance_badge,
    sparkline_svg, render_cell, default_breadcrumbs,
)


def test_badge():
    result = badge("test", "green")
    assert 'class="badge badge-green"' in result
    assert "test" in result


def test_confidence_badge_high():
    result = confidence_badge("high")
    assert "badge-green" in result


def test_confidence_badge_unknown():
    result = confidence_badge("unknown")
    assert "badge-grey" in result


def test_verification_badge():
    result = verification_badge("verified")
    assert "badge-green" in result


def test_provenance_badge_official():
    result = provenance_badge("official")
    assert "Official stats" in result
    assert "badge-blue" in result


def test_provenance_badge_estimated():
    result = provenance_badge("estimated")
    assert "Analytical estimate" in result


def test_sparkline_svg_empty():
    assert sparkline_svg([]) == ""


def test_sparkline_svg_values():
    result = sparkline_svg([10, 20, 30])
    assert "<svg" in result
    assert "polyline" in result


def test_render_cell_plain():
    result = render_cell("name", "Test")
    assert result == "Test"


def test_render_cell_url():
    result = render_cell("source_url", "https://example.com")
    assert 'href="https://example.com"' in result
    assert "Link" in result


def test_render_cell_issue_id():
    result = render_cell("issue_id", "ISSUE-001")
    assert "contradiction-issue-001.html" in result


def test_default_breadcrumbs_index():
    crumbs = default_breadcrumbs("index")
    assert crumbs == [("index.html", "Overview")]


def test_default_breadcrumbs_methodology():
    crumbs = default_breadcrumbs("methodology")
    assert len(crumbs) >= 2
    assert crumbs[0] == ("index.html", "Overview")
```

- [ ] **Step 3: Run tests**

Run: `pytest scripts/tests/test_site_builder.py scripts/tests/test_html_helpers.py -v`
Expected: All tests pass.

- [ ] **Step 4: Run full test suite to check no regressions**

Run: `pytest scripts/tests/ -v`
Expected: All tests pass (original 25 + new tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/tests/test_site_builder.py scripts/tests/test_html_helpers.py
git commit -m "test: add SiteBuilder and html_helpers unit tests"
git push origin main
```

---

## Task 5: Checkpoint A.1 — Migrate methodology.html

**Files:**
- Create: `scripts/builders/context_providers/methods.py`
- Create: `scripts/templates/pages/methodology.html`
- Modify: `scripts/build_site.py` — add routing layer

- [ ] **Step 1: Create methods context provider**

Create `scripts/builders/context_providers/methods.py`:

```python
"""Context providers for Data & Methods pages."""
from ..config import ROOT
from ..data_loader import read_csv, compute_data_health
from ..html_helpers import badge, DEFAULT_PURPOSE


def methodology_context():
    """Prepare template context for methodology.html."""
    gaps_path = ROOT / "data/evidence/evidence-gaps.csv"
    gaps = []
    severity_counts = {}
    if gaps_path.exists():
        gaps = read_csv(gaps_path)
        for g in gaps:
            sev = g.get("severity", "unknown")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

    return {
        "output_filename": "methodology.html",
        "title": "Methodology",
        "subhead": "Taxonomy, scoring model, evidence standards, and quality controls.",
        "active": "methodology",
        "context_text": "This page explains how datasets are scored, validated, and linked to evidence so findings are transparent and reproducible.",
        "purpose": DEFAULT_PURPOSE.get("methodology"),
        "show_trust_panel": False,
        "next_steps": [
            ("metric-methods.html", "Open metric methods appendix"),
            ("sources.html", "Open sources and citations"),
            ("exports.html", "Open data exports"),
            ("data-health.html", "Open data health monitoring"),
        ],
        "evidence_gaps": gaps,
        "severity_counts": severity_counts,
    }


def metric_methods_context():
    """Prepare template context for metric-methods.html."""
    return {
        "output_filename": "metric-methods.html",
        "title": "Metric Methods Appendix",
        "subhead": "Definitions, formulas, provenance, and confidence logic for benchmark and report metrics.",
        "active": "metric-methods",
        "context_text": "Use this appendix to interpret benchmark/report indicators correctly and to understand which values are official statistics versus analytical estimates.",
        "purpose": DEFAULT_PURPOSE.get("metric-methods"),
        "show_trust_panel": False,
        "next_steps": [
            ("benchmark.html", "Return to benchmark"),
            ("reports.html", "Return to reports"),
            ("methodology.html", "Return to methodology"),
        ],
    }


def sources_context():
    """Prepare template context for sources.html."""
    evidence = read_csv(ROOT / "data/evidence/recommendation_evidence_links.csv")
    baselines = read_csv(ROOT / "data/evidence/official_baseline_metrics.csv")
    return {
        "output_filename": "sources.html",
        "title": "Sources and Citations",
        "subhead": "Official data sources, evidence links, and baseline metrics.",
        "active": "sources",
        "context_text": "Use this reference page to verify evidence links, source tables, and citations used throughout the analysis.",
        "purpose": DEFAULT_PURPOSE.get("sources"),
        "show_trust_panel": False,
        "next_steps": [
            ("methodology.html", "Open methodology"),
            ("recommendations.html", "Open recommendations"),
            ("exports.html", "Open data exports"),
        ],
        "evidence_links": evidence,
        "baselines": baselines,
    }


def exports_context():
    """Prepare template context for exports.html."""
    dataset_names = [
        "contradiction-register", "recommendations", "recommendation_evidence_links",
        "official_baseline_metrics", "implementation-roadmap", "bottleneck-heatmap",
        "appeal-decisions", "lpa-data-quality", "lpa-quarterly-trends",
        "lpa-issue-incidence",
    ]
    return {
        "output_filename": "exports.html",
        "title": "Data Exports",
        "subhead": "Download datasets in CSV and JSON format.",
        "active": "exports",
        "context_text": "Download the core datasets in machine-readable form for external analysis, QA checks, or reuse in other tools.",
        "purpose": DEFAULT_PURPOSE.get("exports"),
        "show_trust_panel": False,
        "next_steps": [
            ("data-health.html", "Open data health"),
            ("reports.html", "Open report bundles"),
            ("methodology.html", "Open methodology"),
        ],
        "dataset_names": dataset_names,
    }


def data_health_context():
    """Prepare template context for data-health.html."""
    rows, counts = compute_data_health()
    # Add a sort key for age
    for row in rows:
        row["sort_age"] = row["age_days"] if isinstance(row["age_days"], int) else 9999
    return {
        "output_filename": "data-health.html",
        "title": "Data Health",
        "subhead": "Freshness and reliability monitoring for core operational datasets.",
        "active": "data-health",
        "context_text": "Use this page to assess whether evidence datasets are up to date before relying on benchmark outputs or recommendations.",
        "purpose": DEFAULT_PURPOSE.get("data-health"),
        "show_trust_panel": True,
        "trust_panel_rows": rows,
        "next_steps": [
            ("benchmark.html", "Return to benchmark"),
            ("reports.html", "Return to reports"),
            ("sources.html", "Review source index"),
        ],
        "health_rows": sorted(rows, key=lambda r: r["sort_age"], reverse=True),
        "health_counts": counts,
    }
```

- [ ] **Step 2: Create methodology.html template**

Create `scripts/templates/pages/methodology.html`:

```html
{% extends "base.html" %}
{% from "macros/badges.html" import badge_html %}
{% from "macros/tables.html" import table_guide %}

{% block content %}
<section class="card"><h2>Evidence Standard</h2>
<p>Every recommendation references at least one official dataset row from GOV.UK planning statistics or PINS casework data.</p></section>

<section class="card"><h2>Scoring Model</h2>
<p>Issues scored on five dimensions with explicit weights. See <code>data/schemas/scoring.json</code>.</p></section>

<section class="card"><h2>Verification States</h2>
<p>Records carry a verification state: <strong>draft</strong>, <strong>verified</strong>, or <strong>legal-reviewed</strong>.</p></section>

<section class="card"><h2>Confidence Levels</h2>
<p>Findings carry confidence labels: <strong>high</strong>, <strong>medium</strong>, or <strong>low</strong>.</p></section>

<section class="card"><h2>Derived authority metrics</h2>
<p>Benchmark and report pages include derived indicators for validation rework, delegated share, plan age, consultation lag, and backlog pressure. These are analytical estimates and are shown with confidence labels tied to authority data-quality tier.</p></section>

<section class="card"><p>See <a href="metric-methods.html">metric methods appendix</a> for formula notes and interpretation guidance.</p></section>

<section class="card"><h2>Validation</h2>
<p>Schema, FK, enum, and unique-ID checks run via <code>scripts/validate_data.py</code>. Internal links checked via <code>scripts/check_links.py</code>.</p></section>

<section class="card"><h2>Governance cadence</h2>
<ul>
  <li><strong>Monthly:</strong> refresh datasets, regenerate site, and review data health warnings.</li>
  <li><strong>Quarterly:</strong> publish methodology and metric provenance update notes with each GOV.UK statistics cycle.</li>
  <li><strong>Annually:</strong> reconcile legal and policy references against current in-force instruments and guidance.</li>
</ul></section>

<section class="card"><h2>Owner responsibilities</h2>
<ul>
  <li><strong>Data lead:</strong> schema updates, quality thresholds, and freshness triage.</li>
  <li><strong>Data engineer:</strong> ingestion reliability and build automation.</li>
  <li><strong>Methodology lead:</strong> confidence rules, provenance policy, and publication notes.</li>
  <li><strong>Product/editorial lead:</strong> release notes, audience guidance, and change communication.</li>
</ul></section>

<section class="card"><h2>How scoring works in 3 steps</h2>
<ol>
  <li>Collect issue-level values for severity, frequency, legal risk, delay impact, and fixability.</li>
  <li>Apply explicit weighting from scoring.json.</li>
  <li>Rank and review with confidence and verification labels.</li>
</ol></section>

{% if evidence_gaps %}
<section class="card"><h2>Evidence Gaps</h2>
<p>Known gaps in evidence coverage, tracked for remediation.</p>
<p>
  {% set severity_colors = {"high": "red", "medium": "amber", "low": "green"} %}
  {% for sev in ["high", "medium", "low"] %}
  {% if severity_counts.get(sev) %}
  {{ badge(sev, severity_colors[sev]) }} {{ severity_counts[sev] }} &nbsp;
  {% endif %}
  {% endfor %}
</p>
<table><thead><tr><th>Record</th><th>Type</th><th>Gap</th><th>Severity</th><th>Remediation</th></tr></thead>
<tbody>
  {% for g in evidence_gaps %}
  <tr>
    <td>{{ g.get("record_id", "") }}</td>
    <td>{{ g.get("record_type", "") }}</td>
    <td>{{ g.get("gap_description", "") }}</td>
    <td>{{ badge(g.get("severity", "unknown"), severity_colors.get(g.get("severity", ""), "grey")) }}</td>
    <td>{{ g.get("remediation_path", "") }}</td>
  </tr>
  {% endfor %}
</tbody></table></section>
{% endif %}
{% endblock %}
```

- [ ] **Step 3: Add routing layer to build_site.py**

Modify `scripts/build_site.py` to route `methodology` through the new template system while keeping all other pages on the old builders:

```python
#!/usr/bin/env python3
"""Build static site from CSV datasets — hybrid routing during template migration."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from builders.config import ROOT
from builders.data_loader import read_csv, load_scoring
from builders.export_utils import write_exports, write_exports_manifest, build_ux_kpi_report
from builders.page_overview import build_index, build_search_index, build_search
from builders.page_analysis import (
    build_legislation, build_contradictions, build_contradiction_details,
    build_bottlenecks, build_appeals, build_baselines,
)
from builders.page_authorities import (
    build_plans, build_map, build_compare, build_benchmark,
    build_reports, build_coverage,
)
from builders.page_trends import build_trends
from builders.page_recommendations import (
    build_recommendations, build_recommendation_details,
    build_roadmap, build_consultation,
)
from builders.page_methods import (
    build_metric_methods, build_sources,
    build_exports_index, build_data_health,
)
from builders.page_audiences import (
    build_audience_policymakers, build_audience_lpas,
    build_audience_developers, build_audience_public,
)
from site_builder import SiteBuilder
from builders.context_providers.methods import methodology_context


def main():
    weights = load_scoring()

    # --- Template-rendered pages ---
    builder = SiteBuilder()
    builder.register("methodology", "pages/methodology.html", methodology_context)
    builder.render_all()

    # --- Old builder pages ---
    build_index()
    build_legislation()
    build_plans()
    build_contradictions(weights)
    build_recommendations(weights)
    build_contradiction_details(weights)
    build_recommendation_details()
    build_roadmap()
    build_baselines()
    build_bottlenecks()
    build_appeals()
    build_map()
    build_compare()
    build_benchmark()
    build_trends()
    build_reports()
    build_coverage()
    build_data_health()
    build_consultation()
    build_search_index()
    build_search()
    build_audience_policymakers()
    build_audience_lpas()
    build_audience_developers()
    build_audience_public()
    # build_methodology() removed — now rendered via template
    build_metric_methods()
    build_sources()
    build_exports_index()
    build_ux_kpi_report()

    # Write exports
    exports_data = {
        "contradiction-register": read_csv(ROOT / "data/issues/contradiction-register.csv"),
        "recommendations": read_csv(ROOT / "data/issues/recommendations.csv"),
        "recommendation_evidence_links": read_csv(ROOT / "data/evidence/recommendation_evidence_links.csv"),
        "official_baseline_metrics": read_csv(ROOT / "data/evidence/official_baseline_metrics.csv"),
        "implementation-roadmap": read_csv(ROOT / "data/issues/implementation-roadmap.csv"),
        "bottleneck-heatmap": read_csv(ROOT / "data/issues/bottleneck-heatmap.csv"),
        "appeal-decisions": read_csv(ROOT / "data/evidence/appeal-decisions.csv"),
        "lpa-data-quality": read_csv(ROOT / "data/plans/lpa-data-quality.csv"),
        "lpa-quarterly-trends": read_csv(ROOT / "data/evidence/lpa-quarterly-trends.csv"),
        "lpa-issue-incidence": read_csv(ROOT / "data/issues/lpa-issue-incidence.csv"),
    }
    write_exports(exports_data)
    write_exports_manifest(exports_data)

    print("Built site pages from CSV data.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Build site and verify methodology page**

Run: `python3 scripts/build_site.py`
Expected: "Built site pages from CSV data."

- [ ] **Step 5: Diff the methodology page output against the old version**

Before this step, save the old methodology page for comparison:

Run: `python3 scripts/check_links.py`
Expected: No broken links.

Run: `python3 scripts/check_accessibility.py`
Expected: Accessibility checks pass.

Note: The Jinja2 output may have whitespace differences from the old string-concatenation output. This is expected and acceptable. The **content and structure** must be identical.

- [ ] **Step 6: Run full test suite**

Run: `pytest scripts/tests/ -v`
Expected: All tests pass. The build regression test may need a baseline snapshot update if the methodology page whitespace changed.

- [ ] **Step 7: Update baseline snapshot if needed**

If `test_build_regression.py` fails due to methodology.html hash change:

Run:
```python
python3 -c "
import json
from pathlib import Path
from scripts.tests.test_build_regression import snapshot_site
Path('scripts/tests/baseline_snapshot.json').write_text(json.dumps(snapshot_site(), indent=2))
"
```

- [ ] **Step 8: Commit — Checkpoint A.1**

```bash
git add scripts/build_site.py scripts/site_builder.py scripts/builders/html_helpers.py \
       scripts/builders/context_providers/ scripts/templates/ \
       scripts/tests/ pyproject.toml site/methodology.html
git commit -m "feat: checkpoint A.1 — migrate methodology.html to Jinja2 template"
git push origin main
```

---

## Task 6: Checkpoint A.2 — Remaining Data & Methods Pages

**Files:**
- Create: `scripts/templates/pages/metric_methods.html`
- Create: `scripts/templates/pages/sources.html`
- Create: `scripts/templates/pages/exports.html`
- Create: `scripts/templates/pages/data_health.html`
- Modify: `scripts/build_site.py` — route 4 more pages through templates
- Modify: `scripts/builders/context_providers/methods.py` — already has context functions from Task 5

- [ ] **Step 1: Create metric_methods.html template**

Create `scripts/templates/pages/metric_methods.html`. This page has many static content sections with anchored IDs. The template should reproduce the exact structure from `build_metric_methods()` in `page_methods.py`.

```html
{% extends "base.html" %}
{% from "macros/tables.html" import table_guide %}

{% block content %}
<section class="card"><h2>Purpose</h2>
<p>This appendix defines how benchmark and report metrics are calculated, what each metric signals, and which inputs are official versus analytical estimates.</p></section>

{{ table_guide("How to use this appendix", [
    "Use metric definitions before comparing authorities.",
    "Check the provenance and confidence line for each metric.",
    "Treat analytical estimates as directional indicators, not statutory facts.",
    "Re-check formulas after major methodology releases.",
]) }}

<section class="card" id="major-speed"><h2>Speed (%)</h2>
<p><strong>Definition:</strong> Latest major applications determined in time for each authority.</p>
<p><strong>Formula:</strong> value from latest quarter in <code>lpa-quarterly-trends.csv</code> (<code>major_in_time_pct</code>).</p>
<p><strong>Provenance:</strong> official statistics (GOV.UK P151).</p></section>

<section class="card" id="speed-delta"><h2>4Q Delta (pp)</h2>
<p><strong>Definition:</strong> Change in major decision speed over the tracked window.</p>
<p><strong>Formula:</strong> latest <code>major_in_time_pct</code> minus first available <code>major_in_time_pct</code> for each authority.</p>
<p><strong>Provenance:</strong> official statistics (derived from GOV.UK P151 trend series).</p></section>

<section class="card" id="appeal-rate"><h2>Appeal %</h2>
<p><strong>Definition:</strong> Latest appeals overturned percentage.</p>
<p><strong>Formula:</strong> value from latest quarter in <code>lpa-quarterly-trends.csv</code> (<code>appeals_overturned_pct</code>).</p>
<p><strong>Provenance:</strong> official statistics (GOV.UK P152).</p></section>

<section class="card" id="issues"><h2>Issues and High Severity</h2>
<p><strong>Definition:</strong> Count of linked issues and high-severity subset for each authority.</p>
<p><strong>Formula:</strong> direct values from <code>lpa-issue-incidence.csv</code> fields <code>total_linked_issues</code> and <code>high_severity_issues</code>.</p>
<p><strong>Provenance:</strong> analytical estimate layer.</p></section>

<section class="card" id="quality-tier"><h2>Quality tier and coverage score</h2>
<p><strong>Definition:</strong> Evidence completeness and quality indicator for each authority.</p>
<p><strong>Formula:</strong> values from <code>lpa-data-quality.csv</code> (<code>data_quality_tier</code>, <code>coverage_score</code>).</p>
<p><strong>Provenance:</strong> analytical estimate layer.</p></section>

<section class="card" id="validation-rework"><h2>Validation rework proxy (%)</h2>
<p><strong>Definition:</strong> Estimated share of submissions requiring rework at validation stage.</p>
<p><strong>Formula:</strong> <code>BAS-007 baseline + quality-tier adjustment + issue-pressure adjustment + trend-volatility adjustment</code>, lower-bounded at 5.0.</p>
<p><strong>Provenance:</strong> analytical estimate seeded by official baseline metric.</p></section>

<section class="card" id="delegated-share"><h2>Delegated decision share proxy (%)</h2>
<p><strong>Definition:</strong> Estimated proportion of decisions made under delegated powers.</p>
<p><strong>Formula:</strong> authority-type baseline adjusted by high-severity issue load, latest speed, and latest appeal rate; bounded to 70-95.</p>
<p><strong>Provenance:</strong> analytical estimate.</p></section>

<section class="card" id="plan-age"><h2>Plan age (years)</h2>
<p><strong>Definition:</strong> Years since latest adopted or in-force tracked plan document.</p>
<p><strong>Formula:</strong> <code>(today - max(adoption_or_publication_date of adopted/in-force docs)) / 365.25</code>.</p>
<p><strong>Provenance:</strong> analytical derivation from authority plan-document records.</p></section>

<section class="card" id="consult-lag"><h2>Consultation lag proxy (weeks)</h2>
<p><strong>Definition:</strong> Estimated consultation-stage delay pressure.</p>
<p><strong>Formula:</strong> baseline constant + high-severity adjustment + stage-risk adjustment + quality-tier adjustment; capped at 10.0 weeks.</p>
<p><strong>Provenance:</strong> analytical estimate.</p></section>

<section class="card" id="backlog-pressure"><h2>Backlog pressure index (0-100)</h2>
<p><strong>Definition:</strong> Composite pressure indicator for authority planning throughput risk.</p>
<p><strong>Formula:</strong> weighted sum of issue count, high-severity count, speed gap vs England average, and plan-age factor; capped at 100.</p>
<p><strong>Provenance:</strong> analytical estimate.</p></section>

<section class="card" id="analytical-confidence"><h2>Analytical confidence</h2>
<p><strong>Definition:</strong> Confidence label for estimated metrics.</p>
<p><strong>Formula:</strong> quality tier A -> high, B -> medium, C/other -> low.</p>
<p><strong>Usage:</strong> confidence applies to analytical estimates only, not official series.</p></section>
{% endblock %}
```

- [ ] **Step 2: Create sources.html template**

Create `scripts/templates/pages/sources.html`:

```html
{% extends "base.html" %}
{% from "macros/tables.html" import data_table, table_guide %}

{% block content %}
<section class="card"><h2>Evidence Links</h2></section>

<section class="card"><h3>Source reliability tiers</h3>
<ul>
  <li><strong>Tier 1:</strong> Official statistics and statutory publications.</li>
  <li><strong>Tier 2:</strong> Formal policy guidance and ministerial publications.</li>
  <li><strong>Tier 3:</strong> Analytical estimates and inferred operational evidence.</li>
</ul></section>

{{ table_guide("How to read this table", [
    "Each row links a recommendation to a source record.",
    "Baseline values and windows describe current evidence levels.",
    "Use source URLs to verify references directly.",
]) }}

<section class="card"><table><thead><tr>
  <th>ID</th><th>Rec</th><th>Source</th><th>Metric</th><th>Baseline</th><th>URL</th>
</tr></thead><tbody>
  {% for row in evidence_links %}
  <tr>
    <td>{{ row.get("link_id", "") }}</td>
    <td>{{ render_cell("recommendation_id", row.get("recommendation_id", "")) }}</td>
    <td>{{ row.get("source_dataset", "") }}</td>
    <td>{{ row.get("metric_name", "") }}</td>
    <td>{{ row.get("baseline_value", "") }}</td>
    <td>{{ render_cell("source_url", row.get("source_url", "")) }}</td>
  </tr>
  {% endfor %}
</tbody></table></section>

<section class="card"><h2>Official Baseline Metrics</h2></section>

{{ table_guide("How to read this table", [
    "Each row is a baseline metric with source table and geography.",
    "Use values with period and source context for valid comparisons.",
    "Official source links provide direct verification.",
]) }}

<section class="card"><table><thead><tr>
  <th>ID</th><th>Metric</th><th>Table</th><th>Geography</th><th>Value</th><th>URL</th>
</tr></thead><tbody>
  {% for row in baselines %}
  <tr>
    <td>{{ row.get("metric_id", "") }}</td>
    <td>{{ row.get("metric_name", "") }}</td>
    <td>{{ row.get("source_table", "") }}</td>
    <td>{{ row.get("geography", "") }}</td>
    <td>{{ row.get("value", "") }}</td>
    <td>{{ render_cell("source_url", row.get("source_url", "")) }}</td>
  </tr>
  {% endfor %}
</tbody></table></section>
{% endblock %}
```

- [ ] **Step 3: Create exports.html template**

Create `scripts/templates/pages/exports.html`:

```html
{% extends "base.html" %}

{% block content %}
<section class="card"><h2>Machine-Readable Exports</h2>
<p>All core datasets are available in CSV and JSON format for external analysis.</p>
<ul>
  {% for name in dataset_names %}
  <li><a href="exports/{{ name }}.csv">{{ name }}.csv</a> | <a href="exports/{{ name }}.json">{{ name }}.json</a></li>
  {% endfor %}
</ul></section>

<section class="card"><h2>Version Manifest</h2>
<p>Build manifest includes dataset hashes, row counts, and generation timestamp.</p>
<p><a href="exports/manifest.json">manifest.json</a></p></section>
{% endblock %}
```

- [ ] **Step 4: Create data_health.html template**

Create `scripts/templates/pages/data_health.html`:

```html
{% extends "base.html" %}
{% from "macros/tables.html" import table_guide %}

{% block content %}
<section class="card"><p>Monitors freshness of core operational datasets and highlights stale or critical update risk windows.</p></section>

<section class="grid">
  <article class="card"><h3>Fresh datasets</h3><p>{{ health_counts.get("fresh", 0) }}</p></article>
  <article class="card"><h3>Stale datasets</h3><p>{{ health_counts.get("stale", 0) }}</p></article>
  <article class="card"><h3>Critical datasets</h3><p>{{ health_counts.get("critical", 0) }}</p></article>
</section>

{{ table_guide("How to read this table", [
    "Each row is one monitored dataset.",
    "Age in days is measured from the most recent tracked date field.",
    "Fresh, stale, and critical statuses are threshold-based.",
    "Prioritise stale and critical datasets for update before high-stakes use.",
]) }}

<section class="card"><table><thead><tr>
  <th>Dataset</th><th>Status</th><th>Rows</th><th>Last updated</th><th>Age (days)</th><th>Path</th>
</tr></thead><tbody>
  {% for row in health_rows %}
  <tr>
    <td>{{ row.dataset }}</td>
    <td>{{ row.status_badge }}</td>
    <td>{{ row.row_count }}</td>
    <td>{{ row.last_updated }}</td>
    <td>{{ row.age_days }}</td>
    <td><code>{{ row.source_path }}</code></td>
  </tr>
  {% endfor %}
</tbody></table></section>
{% endblock %}
```

- [ ] **Step 5: Update build_site.py routing**

Add the 4 new pages to the template routing in `build_site.py` and remove their old builder calls:

```python
# In the template-rendered section, add:
from builders.context_providers.methods import (
    methodology_context, metric_methods_context,
    sources_context, exports_context, data_health_context,
)

# Register all 5 Data & Methods pages:
builder.register("methodology", "pages/methodology.html", methodology_context)
builder.register("metric-methods", "pages/metric_methods.html", metric_methods_context)
builder.register("sources", "pages/sources.html", sources_context)
builder.register("exports", "pages/exports.html", exports_context)
builder.register("data-health", "pages/data_health.html", data_health_context)

# Remove these old builder calls:
# build_metric_methods()
# build_sources()
# build_exports_index()
# build_data_health()
```

- [ ] **Step 6: Build and verify**

Run: `python3 scripts/build_site.py`
Expected: Builds successfully.

Run: `python3 scripts/check_links.py`
Expected: No broken links.

Run: `python3 scripts/check_accessibility.py`
Expected: Passes.

- [ ] **Step 7: Run tests, update baseline snapshot**

Run: `pytest scripts/tests/ -v`

Update baseline snapshot if hashes changed:
```bash
python3 -c "
import json
from pathlib import Path
from scripts.tests.test_build_regression import snapshot_site
Path('scripts/tests/baseline_snapshot.json').write_text(json.dumps(snapshot_site(), indent=2))
"
```

Run: `pytest scripts/tests/ -v`
Expected: All pass.

- [ ] **Step 8: Commit — Checkpoint A.2**

```bash
git add scripts/ site/ templates/
git commit -m "feat: checkpoint A.2 — migrate remaining Data & Methods pages to Jinja2"
git push origin main
```

---

## Tasks 7-10: Remaining Checkpoints (A.3 through A.7)

The pattern is now established. Each remaining checkpoint follows the same process:

1. Create context provider (in the appropriate `context_providers/*.py` file)
2. Create page template(s) (in `templates/pages/`)
3. Update routing in `build_site.py`
4. Build, verify (links, accessibility), run tests, update baseline
5. Commit and push

### Task 7: Checkpoint A.3 — Overview Pages (index, search)

**Files:**
- Create: `scripts/builders/context_providers/overview.py`
- Create: `scripts/templates/pages/index.html`
- Create: `scripts/templates/pages/search.html`
- Modify: `scripts/build_site.py`

The `overview.py` context provider extracts the KPI card logic, trend delta computation, and homepage section data from `page_overview.py:build_index()`. The `index.html` template uses card macros for the KPI strip and section grids. `build_search_index()` continues as a Python function (it writes JSON, not HTML). `build_search()` migrates to a template.

Context provider must include: `metric_cards` list, `avg_delta`, `delta_arrow`, audience card data, section navigation data.

### Task 8: Checkpoint A.4 — System Analysis Pages

**Files:**
- Create: `scripts/builders/context_providers/analysis.py`
- Create: `scripts/templates/pages/legislation.html`
- Create: `scripts/templates/pages/contradictions.html`
- Create: `scripts/templates/pages/contradiction_detail.html`
- Create: `scripts/templates/pages/bottlenecks.html`
- Create: `scripts/templates/pages/appeals.html`
- Create: `scripts/templates/pages/baselines.html`
- Modify: `scripts/build_site.py`

The `analysis.py` context provider must handle: weighted scoring for contradictions, filter definitions, detail page context for each of the 22 contradiction records. The contradiction detail template uses the sidebar TOC partial. The filter and table enhancement scripts are injected via `{% block scripts %}` in the templates.

### Task 9: Checkpoint A.5 — Recommendations Pages

**Files:**
- Create: `scripts/builders/context_providers/recommendations.py`
- Create: `scripts/templates/pages/recommendations.html`
- Create: `scripts/templates/pages/recommendation_detail.html`
- Create: `scripts/templates/pages/roadmap.html`
- Create: `scripts/templates/pages/consultation.html`
- Modify: `scripts/build_site.py`

The `recommendations.py` context provider extracts data logic from `page_recommendations.py`. The recommendation detail template renders status timeline, linked contradictions, milestones, and evidence rows.

### Task 10: Checkpoint A.6 — Authority Insights Pages

**Files:**
- Create: `scripts/builders/context_providers/authorities.py`
- Create: `scripts/templates/pages/plans.html`
- Create: `scripts/templates/pages/plans_detail.html`
- Create: `scripts/templates/pages/map.html`
- Create: `scripts/templates/pages/compare.html`
- Create: `scripts/templates/pages/benchmark.html`
- Create: `scripts/templates/pages/trends.html`
- Create: `scripts/templates/pages/reports.html`
- Create: `scripts/templates/pages/coverage.html`
- Modify: `scripts/build_site.py`

This is the largest checkpoint — 35+ pages. The `authorities.py` context provider is the most complex, extracting the benchmark ranking, metric bundle derivation, peer grouping, and per-LPA profile data from the 1,528-line `page_authorities.py`. The `build_plans()` function generates 26 individual LPA profile pages via a loop, which becomes a loop in the SiteBuilder calling `plans_detail.html` with per-LPA context.

Key complexity: the benchmark page has filter scripts, table enhancement scripts, mobile drawer scripts, and preset configurations that must be reproduced in template `{% block scripts %}`.

### Task 11: Checkpoint A.7 — Audience Pages + Final Cleanup

**Files:**
- Create: `scripts/builders/context_providers/audiences.py`
- Create: `scripts/templates/pages/audience_policymakers.html`
- Create: `scripts/templates/pages/audience_lpas.html`
- Create: `scripts/templates/pages/audience_developers.html`
- Create: `scripts/templates/pages/audience_public.html`
- Modify: `scripts/build_site.py` — simplify to final form
- Delete: `scripts/builders/html_utils.py`
- Delete: `scripts/builders/page_overview.py`
- Delete: `scripts/builders/page_analysis.py`
- Delete: `scripts/builders/page_authorities.py`
- Delete: `scripts/builders/page_recommendations.py`
- Delete: `scripts/builders/page_methods.py`
- Delete: `scripts/builders/page_audiences.py`
- Delete: `scripts/builders/page_trends.py`
- Modify: `scripts/tests/test_html_utils.py` — delete (replaced by `test_html_helpers.py`)
- Modify: `scripts/tests/test_build_regression.py` — update baseline

**Final `build_site.py`:**

```python
#!/usr/bin/env python3
"""Build static site from CSV datasets using Jinja2 templates."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from builders.config import ROOT
from builders.data_loader import read_csv, load_scoring
from builders.export_utils import write_exports, write_exports_manifest, build_ux_kpi_report
from site_builder import SiteBuilder

# Import all context provider registration functions
from builders.context_providers.overview import register_overview_pages
from builders.context_providers.analysis import register_analysis_pages
from builders.context_providers.authorities import register_authority_pages
from builders.context_providers.recommendations import register_recommendation_pages
from builders.context_providers.methods import register_methods_pages
from builders.context_providers.audiences import register_audience_pages


def main():
    builder = SiteBuilder()
    weights = load_scoring()

    register_overview_pages(builder)
    register_analysis_pages(builder, weights)
    register_authority_pages(builder)
    register_recommendation_pages(builder, weights)
    register_methods_pages(builder)
    register_audience_pages(builder)

    builder.render_all()

    # Write exports (non-HTML, stays in Python)
    exports_data = {
        "contradiction-register": read_csv(ROOT / "data/issues/contradiction-register.csv"),
        "recommendations": read_csv(ROOT / "data/issues/recommendations.csv"),
        "recommendation_evidence_links": read_csv(ROOT / "data/evidence/recommendation_evidence_links.csv"),
        "official_baseline_metrics": read_csv(ROOT / "data/evidence/official_baseline_metrics.csv"),
        "implementation-roadmap": read_csv(ROOT / "data/issues/implementation-roadmap.csv"),
        "bottleneck-heatmap": read_csv(ROOT / "data/issues/bottleneck-heatmap.csv"),
        "appeal-decisions": read_csv(ROOT / "data/evidence/appeal-decisions.csv"),
        "lpa-data-quality": read_csv(ROOT / "data/plans/lpa-data-quality.csv"),
        "lpa-quarterly-trends": read_csv(ROOT / "data/evidence/lpa-quarterly-trends.csv"),
        "lpa-issue-incidence": read_csv(ROOT / "data/issues/lpa-issue-incidence.csv"),
    }
    write_exports(exports_data)
    write_exports_manifest(exports_data)
    build_ux_kpi_report()

    print("Built site pages from CSV data.")


if __name__ == "__main__":
    main()
```

Each context provider module exposes a `register_*_pages(builder, ...)` function that calls `builder.register()` for each page in its group. This keeps `build_site.py` clean and each provider self-contained.

**Final verification:**
- `python3 scripts/build_site.py` — builds all 85 pages
- `python3 scripts/check_links.py` — no broken links
- `python3 scripts/check_accessibility.py` — all pass
- `python3 scripts/check_metric_stability.py` — all pass
- `pytest scripts/tests/ -v` — all pass
- `ruff check scripts/` — clean
- `git diff --stat` — old `page_*.py` files deleted, templates added

**Commit:**
```bash
git add -A
git commit -m "feat: checkpoint A.7 — complete Jinja2 migration, delete old page builders"
git push origin main
```

---

## Post-Migration Verification

After Task 11, confirm the Phase A success criteria:

- [ ] All 85 pages render correctly via Jinja2 templates
- [ ] `build_site.py` is under 50 lines (target: ~35)
- [ ] Python code in `builders/` is under 2,000 lines (context providers + helpers + data_loader + metrics + config + exports)
- [ ] All old `page_*.py` files deleted
- [ ] All CI checks pass (`validate_data.py`, `build_site.py`, `check_links.py`, `check_metric_drift.py`, `check_metric_stability.py`, `check_accessibility.py`)
- [ ] `pytest scripts/tests/ -v` passes
- [ ] `ruff check scripts/` clean
- [ ] Update README.md repository structure section to reflect new template architecture
- [ ] Update `AGENTS.md` validation sequence if needed
