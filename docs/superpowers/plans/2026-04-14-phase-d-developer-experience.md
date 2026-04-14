# Phase D: Developer Experience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add pytest and ruff to CI, create meaningful test coverage for context providers and templates, add a Makefile task runner, and set up pre-commit hooks.

**Architecture:** Three sub-phases — D.1 cleans up project foundation (.gitignore, report files, CI), D.2 adds meaningful test coverage, D.3 adds Makefile and pre-commit hooks. Each is a commit checkpoint.

**Tech Stack:** Python 3.12, pytest, ruff, GNU Make, pre-commit

**Design spec:** `docs/superpowers/specs/2026-04-14-systematic-improvement-design.md` (Phase D section)

---

## Task 1: Project Cleanup and CI Hardening

**Files:**
- Modify: `.gitignore` — add metric-stability-report files, .venv
- Modify: `.github/workflows/ci.yml` — add pytest and ruff steps
- Modify: `README.md` — update quality checks section

- [ ] **Step 1: Update .gitignore**

Add these lines to `.gitignore`:
```
metric-stability-report.txt
metric-stability-report.json
.venv/
```

- [ ] **Step 2: Add pytest and ruff to CI**

In `.github/workflows/ci.yml`, add two new steps after the `Install dependencies` step (change `pip install -e .` to `pip install -e ".[dev]"` to get pytest and ruff):

```yaml
      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Lint with ruff
        run: ruff check scripts/

      - name: Run tests
        run: pytest scripts/tests/ -v
```

Insert these BEFORE `Validate data schemas`.

Also update `pages.yml` to use `pip install -e ".[dev]"` (currently just `pip install -e .`).

- [ ] **Step 3: Verify CI changes locally**

```bash
pip install -e ".[dev]"
ruff check scripts/
pytest scripts/tests/ -v
python3 scripts/validate_data.py
python3 scripts/build_site.py
python3 scripts/check_links.py
```

- [ ] **Step 4: Commit**

```bash
git add .gitignore .github/workflows/ci.yml .github/workflows/pages.yml
git commit -m "chore: D.1 — clean up .gitignore, add pytest and ruff to CI"
git push origin main
```

---

## Task 2: Context Provider Tests

**Files:**
- Create: `scripts/tests/test_context_providers.py`

Test that each context provider returns a dict with required keys and correct types. Use minimal fixture data where possible; for providers that read real CSV data, test against the actual project data.

- [ ] **Step 1: Create test file**

Create `scripts/tests/test_context_providers.py`:

```python
"""Tests for context provider functions — verify each returns correct dict shape."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from builders.data_loader import load_scoring

# Required keys that base.html expects from every context
BASE_KEYS = {"output_filename", "title", "subhead", "active"}


def assert_base_context(ctx, expected_active):
    """Verify a context dict has all required base.html keys."""
    for key in BASE_KEYS:
        assert key in ctx, f"Missing key '{key}' in context"
    assert ctx["active"] == expected_active
    assert ctx["output_filename"].endswith(".html")
    assert isinstance(ctx["title"], str) and ctx["title"]
    assert isinstance(ctx["subhead"], str) and ctx["subhead"]


# --- Methods ---

def test_methodology_context():
    from builders.context_providers.methods import methodology_context
    ctx = methodology_context()
    assert_base_context(ctx, "methodology")
    assert "evidence_gaps" in ctx
    assert "severity_counts" in ctx


def test_metric_methods_context():
    from builders.context_providers.methods import metric_methods_context
    ctx = metric_methods_context()
    assert_base_context(ctx, "metric-methods")


def test_sources_context():
    from builders.context_providers.methods import sources_context
    ctx = sources_context()
    assert_base_context(ctx, "sources")
    assert "evidence_links" in ctx
    assert "baselines" in ctx
    assert isinstance(ctx["evidence_links"], list)


def test_exports_context():
    from builders.context_providers.methods import exports_context
    ctx = exports_context()
    assert_base_context(ctx, "exports")
    assert "dataset_names" in ctx
    assert len(ctx["dataset_names"]) >= 10


def test_data_health_context():
    from builders.context_providers.methods import data_health_context
    ctx = data_health_context()
    assert_base_context(ctx, "data-health")
    assert "health_rows" in ctx
    assert "health_counts" in ctx
    assert isinstance(ctx["health_rows"], list)


# --- Overview ---

def test_index_context():
    from builders.context_providers.overview import index_context
    ctx = index_context()
    assert_base_context(ctx, "index")
    assert "metric_cards" in ctx
    assert "avg_delta" in ctx
    assert isinstance(ctx["metric_cards"], list)


def test_search_context():
    from builders.context_providers.overview import search_context
    ctx = search_context()
    assert_base_context(ctx, "search")


# --- Analysis ---

def test_legislation_context():
    from builders.context_providers.analysis import legislation_context
    ctx = legislation_context()
    assert_base_context(ctx, "legislation")


def test_contradictions_context():
    from builders.context_providers.analysis import contradictions_context
    weights = load_scoring()
    ctx = contradictions_context(weights)
    assert_base_context(ctx, "contradictions")


def test_contradiction_detail_contexts():
    from builders.context_providers.analysis import contradiction_detail_contexts
    weights = load_scoring()
    contexts = contradiction_detail_contexts(weights)
    assert isinstance(contexts, list)
    assert len(contexts) >= 22  # at least 22 contradiction records
    for ctx in contexts:
        assert "output_filename" in ctx
        assert ctx["output_filename"].startswith("contradiction-")


def test_bottlenecks_context():
    from builders.context_providers.analysis import bottlenecks_context
    ctx = bottlenecks_context()
    assert_base_context(ctx, "bottlenecks")


def test_appeals_context():
    from builders.context_providers.analysis import appeals_context
    ctx = appeals_context()
    assert_base_context(ctx, "appeals")


def test_baselines_context():
    from builders.context_providers.analysis import baselines_context
    ctx = baselines_context()
    assert_base_context(ctx, "baselines")


# --- Recommendations ---

def test_recommendations_context():
    from builders.context_providers.recommendations import recommendations_context
    weights = load_scoring()
    ctx = recommendations_context(weights)
    assert_base_context(ctx, "recommendations")


def test_recommendation_detail_contexts():
    from builders.context_providers.recommendations import recommendation_detail_contexts
    contexts = recommendation_detail_contexts()
    assert isinstance(contexts, list)
    assert len(contexts) >= 11
    for ctx in contexts:
        assert "output_filename" in ctx
        assert ctx["output_filename"].startswith("recommendation-")


def test_roadmap_context():
    from builders.context_providers.recommendations import roadmap_context
    ctx = roadmap_context()
    assert_base_context(ctx, "roadmap")


def test_consultation_context():
    from builders.context_providers.recommendations import consultation_context
    ctx = consultation_context()
    assert_base_context(ctx, "consultation")


# --- Authorities ---

def test_plans_context():
    from builders.context_providers.authorities import plans_context
    ctx = plans_context()
    assert_base_context(ctx, "plans")


def test_plans_detail_contexts():
    from builders.context_providers.authorities import plans_detail_contexts
    contexts = plans_detail_contexts()
    assert isinstance(contexts, list)
    assert len(contexts) >= 34  # 34 LPAs
    for ctx in contexts:
        assert "output_filename" in ctx
        assert ctx["output_filename"].startswith("plans-")


def test_map_context():
    from builders.context_providers.authorities import map_context
    ctx = map_context()
    assert_base_context(ctx, "map")


def test_compare_context():
    from builders.context_providers.authorities import compare_context
    ctx = compare_context()
    assert_base_context(ctx, "compare")


def test_benchmark_context():
    from builders.context_providers.authorities import benchmark_context
    ctx = benchmark_context()
    assert_base_context(ctx, "benchmark")


def test_trends_context():
    from builders.context_providers.authorities import trends_context
    ctx = trends_context()
    assert_base_context(ctx, "trends")


def test_reports_context():
    from builders.context_providers.authorities import reports_context
    ctx = reports_context()
    assert_base_context(ctx, "reports")


def test_coverage_context():
    from builders.context_providers.authorities import coverage_context
    ctx = coverage_context()
    assert_base_context(ctx, "coverage")


# --- Audiences ---

def test_policymakers_context():
    from builders.context_providers.audiences import policymakers_context
    ctx = policymakers_context()
    assert_base_context(ctx, "policymakers")


def test_lpas_context():
    from builders.context_providers.audiences import lpas_context
    ctx = lpas_context()
    assert_base_context(ctx, "lpas")


def test_developers_context():
    from builders.context_providers.audiences import developers_context
    ctx = developers_context()
    assert_base_context(ctx, "developers")


def test_public_context():
    from builders.context_providers.audiences import public_context
    ctx = public_context()
    assert_base_context(ctx, "public")
```

- [ ] **Step 2: Run tests**

```bash
pytest scripts/tests/test_context_providers.py -v
```

Expected: All 28+ tests pass.

- [ ] **Step 3: Run full suite**

```bash
pytest scripts/tests/ -v
```

- [ ] **Step 4: Commit**

```bash
git add scripts/tests/test_context_providers.py
git commit -m "test: D.2 — add context provider shape tests (28 tests)"
git push origin main
```

---

## Task 3: Template Rendering Tests

**Files:**
- Create: `scripts/tests/test_template_rendering.py`

Test that each page template renders without error and produces valid HTML structure.

- [ ] **Step 1: Create test file**

Create `scripts/tests/test_template_rendering.py`:

```python
"""Tests for template rendering — verify each template produces valid HTML."""
import sys
from pathlib import Path
from html.parser import HTMLParser

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from site_builder import SiteBuilder
from builders.data_loader import load_scoring


class StructureChecker(HTMLParser):
    """Minimal HTML structure checker."""
    def __init__(self):
        super().__init__()
        self.has_doctype = False
        self.has_html_lang = False
        self.h1_count = 0
        self.has_main = False
        self.has_title = False
        self._in_title = False
        self.title_text = ""

    def handle_decl(self, decl):
        if decl.lower().startswith("doctype"):
            self.has_doctype = True

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html" and a.get("lang"):
            self.has_html_lang = True
        if tag == "h1":
            self.h1_count += 1
        if tag == "main":
            self.has_main = True
        if tag == "title":
            self._in_title = True
            self.has_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title_text += data


def check_html_structure(html_content, page_name):
    """Verify basic HTML structure requirements."""
    checker = StructureChecker()
    checker.feed(html_content)
    assert checker.has_html_lang, f"{page_name}: missing <html lang>"
    assert checker.h1_count == 1, f"{page_name}: expected 1 <h1>, found {checker.h1_count}"
    assert checker.has_main, f"{page_name}: missing <main>"
    assert checker.has_title, f"{page_name}: missing <title>"
    assert len(checker.title_text.strip()) > 0, f"{page_name}: empty <title>"


@pytest.fixture(scope="module")
def builder():
    return SiteBuilder()


def render_context(builder, template_path, context_fn):
    """Render a template and return the HTML string."""
    template = builder.env.get_template(template_path)
    ctx = context_fn()
    return template.render(**ctx)


# --- Methods pages ---

def test_render_methodology(builder):
    from builders.context_providers.methods import methodology_context
    html = render_context(builder, "pages/methodology.html", methodology_context)
    check_html_structure(html, "methodology")
    assert "Scoring Model" in html


def test_render_data_health(builder):
    from builders.context_providers.methods import data_health_context
    html = render_context(builder, "pages/data_health.html", data_health_context)
    check_html_structure(html, "data-health")


# --- Overview pages ---

def test_render_index(builder):
    from builders.context_providers.overview import index_context
    html = render_context(builder, "pages/index.html", index_context)
    check_html_structure(html, "index")
    assert "England at a glance" in html


def test_render_search(builder):
    from builders.context_providers.overview import search_context
    html = render_context(builder, "pages/search.html", search_context)
    check_html_structure(html, "search")
    assert "search-input" in html


# --- Audience pages ---

def test_render_audience_public(builder):
    from builders.context_providers.audiences import public_context
    html = render_context(builder, "pages/audience_public.html", public_context)
    check_html_structure(html, "audience-public")
    assert "What Is This Project?" in html


# --- Spot check a detail page ---

def test_render_contradiction_detail(builder):
    from builders.context_providers.analysis import contradiction_detail_contexts
    weights = load_scoring()
    contexts = contradiction_detail_contexts(weights)
    if contexts:
        ctx = contexts[0]
        template = builder.env.get_template("pages/contradiction_detail.html")
        html = template.render(**ctx)
        check_html_structure(html, ctx["output_filename"])
        assert "detail-layout" in html
```

- [ ] **Step 2: Run tests**

```bash
pytest scripts/tests/test_template_rendering.py -v
```

- [ ] **Step 3: Run full suite**

```bash
pytest scripts/tests/ -v
```

- [ ] **Step 4: Commit**

```bash
git add scripts/tests/test_template_rendering.py
git commit -m "test: D.2 — add template rendering structure tests"
git push origin main
```

---

## Task 4: Makefile

**Files:**
- Create: `Makefile`

- [ ] **Step 1: Create Makefile**

```makefile
.PHONY: build validate test lint check serve clean assets

build: ## Build site from CSV data
	python3 scripts/build_site.py

validate: ## Run data validation
	python3 scripts/validate_data.py

test: ## Run pytest suite
	pytest scripts/tests/ -v

lint: ## Run ruff lint check
	ruff check scripts/

check: validate build lint test links accessibility ## Run all checks
	@echo "All checks passed."

links: ## Check internal links
	python3 scripts/check_links.py

accessibility: ## Check accessibility basics
	python3 scripts/check_accessibility.py

serve: build ## Start local dev server
	python3 -m http.server 4173 --directory site

clean: ## Remove generated artifacts
	rm -rf site/assets/dist
	rm -f metric-stability-report.json metric-stability-report.txt
	find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} + 2>/dev/null || true

assets: ## Build minified assets
	bash scripts/build_assets.sh

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
```

- [ ] **Step 2: Test Makefile targets**

```bash
make help
make validate
make build
make test
make lint
make check
```

- [ ] **Step 3: Commit**

```bash
git add Makefile
git commit -m "chore: D.3 — add Makefile task runner"
git push origin main
```

---

## Task 5: Pre-commit Hooks

**Files:**
- Create: `.pre-commit-config.yaml`
- Modify: `pyproject.toml` — add pre-commit to dev dependencies

- [ ] **Step 1: Add pre-commit to dev dependencies**

In `pyproject.toml`, update the dev optional dependencies:

```toml
[project.optional-dependencies]
dev = ["pytest>=9.0", "ruff>=0.4", "pre-commit>=3.0"]
```

Install: `pip install -e ".[dev]"`

- [ ] **Step 2: Create .pre-commit-config.yaml**

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [check, scripts/]
      - id: ruff-format
        args: [--check, scripts/]
```

- [ ] **Step 3: Install pre-commit hooks**

```bash
pre-commit install
```

- [ ] **Step 4: Test hooks**

```bash
pre-commit run --all-files
```

Expected: All checks pass.

- [ ] **Step 5: Commit**

```bash
git add .pre-commit-config.yaml pyproject.toml
git commit -m "chore: D.3 — add pre-commit hooks for ruff lint and format"
git push origin main
```

---

## Task 6: Final README Update and Version Bump

**Files:**
- Modify: `README.md` — add setup instructions, make check documentation
- Modify: `scripts/builders/config.py` — bump to v16.0
- Modify: `pyproject.toml` — bump to 16.0

- [ ] **Step 1: Update README**

Add/update sections:
- Setup: `pip install -e ".[dev]"` and `pre-commit install`
- Quality checks: `make check` as single command
- Individual targets: `make build`, `make test`, `make lint`, `make validate`
- Note about pre-commit hooks running ruff on commit

- [ ] **Step 2: Bump version to v16.0**

- `scripts/builders/config.py`: `BUILD_VERSION = "v16.0"`
- `pyproject.toml`: `version = "16.0"`

- [ ] **Step 3: Rebuild and verify**

```bash
make check
```

Update baseline snapshot if needed.

- [ ] **Step 4: Commit**

```bash
git add README.md scripts/builders/config.py pyproject.toml site/ scripts/tests/baseline_snapshot.json
git commit -m "feat: complete Phase D — bump version to v16.0, update README with DX improvements"
git push origin main
```
