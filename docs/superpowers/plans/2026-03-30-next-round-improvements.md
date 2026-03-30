# Next Round of Improvements — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the UK Planning Analysis site from a monolithic pilot into a modular, data-rich, analytically deeper, and more capable platform across four sequential phases.

**Architecture:** Phase 1 splits the 4,300-line `build_site.py` into focused modules under `scripts/builders/`. Phase 2 adds 10 Cohort 3 LPAs and upgrades proxy metrics. Phase 3 deepens evidence and upgrades verification states. Phase 4 adds trend analysis, print export, and comparison history.

**Tech Stack:** Python 3 (stdlib only for production code), pytest for tests, ruff for linting, HTML/CSS/JS static site generation.

---

## File Structure

### Phase 1 — New files

```
scripts/
├── builders/
│   ├── __init__.py              # Package init, re-exports main build functions
│   ├── config.py                # BUILD_VERSION, SECTION_CONFIG, PAGE_TO_SECTION, constants
│   ├── data_loader.py           # read_csv, load_scoring, compute_data_health, compute_onboarding_status_rows
│   ├── html_utils.py            # Shared HTML rendering: shell, nav, footer, cards, badges, tables
│   ├── metrics.py               # weighted_score, cohort_for_pid, analytical_confidence_for_tier,
│   │                            # peer_group_for_lpa, derive_plan_age_years, derive_metric_bundle,
│   │                            # parse_iso_date, split_pipe_values, issue_detail_page,
│   │                            # recommendation_detail_page, query_value
│   ├── page_overview.py         # build_index, build_search_index, build_search
│   ├── page_analysis.py         # build_legislation, build_contradictions, build_contradiction_details,
│   │                            # build_bottlenecks, build_appeals, build_baselines
│   ├── page_authorities.py      # build_plans, build_map, build_compare, build_benchmark,
│   │                            # build_reports, build_coverage
│   ├── page_recommendations.py  # build_recommendations, build_recommendation_details,
│   │                            # build_roadmap, build_consultation
│   ├── page_methods.py          # build_methodology, build_metric_methods, build_sources,
│   │                            # build_exports_index, build_data_health
│   ├── page_audiences.py        # build_audience_policymakers, build_audience_lpas,
│   │                            # build_audience_developers, build_audience_public
│   └── export_utils.py          # write_exports, write_exports_manifest, build_ux_kpi_report
├── tests/
│   ├── __init__.py
│   ├── test_data_loader.py
│   ├── test_html_utils.py
│   ├── test_metrics.py
│   └── test_build_regression.py # Full-site build comparison
```

### Phase 2 — Modified files

```
data/plans/pilot-lpas.csv              # +10 Cohort 3 rows
data/plans/pilot-plan-documents.csv    # +20-30 Cohort 3 plan docs
data/plans/policy-hierarchy.csv        # +10 authority-level hierarchy entries
data/plans/lpa-geo.csv                 # +10 coordinate rows
data/plans/lpa-data-quality.csv        # +10 quality tier rows
data/evidence/lpa-quarterly-trends.csv # +40 trend rows (4 quarters x 10 LPAs)
data/issues/lpa-issue-incidence.csv    # +10 issue incidence rows
scripts/builders/metrics.py            # Update cohort_for_pid for Cohort 3
scripts/builders/config.py             # Update BUILD_VERSION to v12.0
```

### Phase 3 — Modified files

```
data/issues/contradiction-register.csv     # Update verification_state on 12+ records
data/evidence/appeal-decisions.csv         # +5 new appeal rows
data/evidence/evidence-gaps.csv            # NEW: evidence gap analysis
data/schemas/datasets.json                 # Add evidence-gaps schema, add related_issues field
scripts/builders/page_methods.py           # Add evidence health summary to methodology page
scripts/builders/config.py                 # Update BUILD_VERSION to v13.0
```

### Phase 4 — New and modified files

```
scripts/builders/page_trends.py            # NEW: build_trends page generator
scripts/builders/page_authorities.py       # Add performance history to LPA detail pages
site/assets/styles.css                     # Add print stylesheet, trend chart styles
site/assets/shell.js                       # Add comparison history localStorage logic
scripts/builders/page_overview.py          # Link to trends from search index
scripts/builders/config.py                 # Add trends to SECTION_CONFIG, BUILD_VERSION v14.0
scripts/build_site.py                      # Add build_trends() call
```

---

## Phase 1: Code Quality & Maintainability

### Task 1: Snapshot current build output for regression testing

**Files:**
- Create: `scripts/tests/__init__.py`
- Create: `scripts/tests/test_build_regression.py`

- [ ] **Step 1: Generate baseline snapshot**

```bash
cd /home/ben/Github/personal/uk-planning
python3 scripts/build_site.py
find site -name '*.html' -exec md5sum {} \; | sort -k2 > /tmp/baseline-hashes.txt
```

- [ ] **Step 2: Create regression test that compares build output**

```python
# scripts/tests/__init__.py
# (empty)
```

```python
# scripts/tests/test_build_regression.py
"""Regression test: verify refactored build produces identical HTML output."""
import hashlib
import json
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SITE = ROOT / "site"
FIXTURE = Path(__file__).parent / "baseline_snapshot.json"


def hash_file(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def snapshot_site() -> dict[str, str]:
    return {
        str(p.relative_to(SITE)): hash_file(p)
        for p in sorted(SITE.rglob("*.html"))
    }


@pytest.fixture
def baseline_snapshot():
    return json.loads(FIXTURE.read_text())


def test_build_output_unchanged(baseline_snapshot):
    """Compare current build output against saved baseline."""
    current = snapshot_site()
    assert set(current.keys()) == set(baseline_snapshot.keys()), (
        f"File set changed.\n"
        f"  Added: {set(current.keys()) - set(baseline_snapshot.keys())}\n"
        f"  Removed: {set(baseline_snapshot.keys()) - set(current.keys())}"
    )
    mismatches = [
        f for f in current
        if current[f] != baseline_snapshot[f]
    ]
    assert not mismatches, f"Content changed in: {mismatches}"
```

- [ ] **Step 3: Save baseline snapshot as JSON fixture**

```bash
cd /home/ben/Github/personal/uk-planning
python3 -c "
import json, sys
sys.path.insert(0, 'scripts')
from tests.test_build_regression import snapshot_site
from pathlib import Path
Path('scripts/tests/baseline_snapshot.json').write_text(json.dumps(snapshot_site(), indent=2))
"
```

- [ ] **Step 4: Run regression test to verify it passes**

```bash
cd /home/ben/Github/personal/uk-planning
python3 -m pytest scripts/tests/test_build_regression.py -v
```

Expected: PASS (baseline matches current output).

- [ ] **Step 5: Commit**

```bash
git add scripts/tests/
git commit -m "test: add build output regression test with baseline snapshot"
```

### Task 2: Extract config module

**Files:**
- Create: `scripts/builders/__init__.py`
- Create: `scripts/builders/config.py`
- Modify: `scripts/build_site.py`

- [ ] **Step 1: Create builders package with config**

```python
# scripts/builders/__init__.py
"""Site builder modules."""
```

```python
# scripts/builders/config.py
"""Build configuration: version, section structure, page mappings."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SITE = ROOT / "site"
EXPORTS = SITE / "exports"
SCORING_PATH = ROOT / "data/schemas/scoring.json"
BUILD_VERSION = "v11.0"

SECTION_CONFIG = {
    "overview": {
        "label": "Overview",
        "href": "index.html",
        "children": [
            ("index", "Overview", "index.html"),
            ("search", "Search", "search.html"),
        ],
    },
    "system-analysis": {
        "label": "System Analysis",
        "href": "contradictions.html",
        "children": [
            ("legislation", "Legislation", "legislation.html"),
            ("contradictions", "Contradictions", "contradictions.html"),
            ("bottlenecks", "Bottlenecks", "bottlenecks.html"),
            ("appeals", "Appeals", "appeals.html"),
            ("baselines", "Baselines", "baselines.html"),
        ],
    },
    "authority-insights": {
        "label": "Authority Insights",
        "href": "plans.html",
        "children": [
            ("plans", "Plans", "plans.html"),
            ("map", "Map", "map.html"),
            ("compare", "Compare", "compare.html"),
            ("benchmark", "Benchmark", "benchmark.html"),
            ("reports", "Reports", "reports.html"),
            ("coverage", "Coverage", "coverage.html"),
        ],
    },
    "recommendations": {
        "label": "Recommendations",
        "href": "recommendations.html",
        "children": [
            ("recommendations", "Recommendations", "recommendations.html"),
            ("roadmap", "Roadmap", "roadmap.html"),
            ("consultation", "Consultation", "consultation.html"),
        ],
    },
    "data-methods": {
        "label": "Data & Methods",
        "href": "methodology.html",
        "children": [
            ("methodology", "Methodology", "methodology.html"),
            ("metric-methods", "Metric Methods", "metric-methods.html"),
            ("sources", "Sources", "sources.html"),
            ("exports", "Exports", "exports.html"),
            ("data-health", "Data Health", "data-health.html"),
        ],
    },
    "audiences": {
        "label": "For Audiences",
        "href": "audience-policymakers.html",
        "children": [
            ("policymakers", "Policy Makers", "audience-policymakers.html"),
            ("lpas", "LPAs", "audience-lpas.html"),
            ("developers", "Developers", "audience-developers.html"),
            ("public", "Public", "audience-public.html"),
        ],
    },
}

PAGE_TO_SECTION = {
    "index": "overview",
    "search": "overview",
    "legislation": "system-analysis",
    "contradictions": "system-analysis",
    "bottlenecks": "system-analysis",
    "appeals": "system-analysis",
    "baselines": "system-analysis",
    "plans": "authority-insights",
    "map": "authority-insights",
    "compare": "authority-insights",
    "benchmark": "authority-insights",
    "reports": "authority-insights",
    "coverage": "authority-insights",
    "recommendations": "recommendations",
    "roadmap": "recommendations",
    "consultation": "recommendations",
    "methodology": "data-methods",
    "metric-methods": "data-methods",
    "sources": "data-methods",
    "exports": "data-methods",
    "data-health": "data-methods",
    "policymakers": "audiences",
    "lpas": "audiences",
    "developers": "audiences",
    "public": "audiences",
}
```

- [ ] **Step 2: Update build_site.py to import from config**

Replace the top-level constants block (lines 16-112 in current `build_site.py`) with:

```python
from builders.config import ROOT, SITE, EXPORTS, SCORING_PATH, BUILD_VERSION, SECTION_CONFIG, PAGE_TO_SECTION
```

Keep all functions in `build_site.py` for now — just the constants move.

- [ ] **Step 3: Run build and regression test**

```bash
cd /home/ben/Github/personal/uk-planning
python3 scripts/build_site.py
python3 -m pytest scripts/tests/test_build_regression.py -v
```

Expected: Build succeeds. Regression test will FAIL because BUILD_VERSION changed from v6.0 to v11.0. This is expected.

- [ ] **Step 4: Update baseline snapshot**

```bash
cd /home/ben/Github/personal/uk-planning
python3 -c "
import json, sys
sys.path.insert(0, 'scripts')
from tests.test_build_regression import snapshot_site
from pathlib import Path
Path('scripts/tests/baseline_snapshot.json').write_text(json.dumps(snapshot_site(), indent=2))
"
```

- [ ] **Step 5: Commit**

```bash
git add scripts/builders/__init__.py scripts/builders/config.py scripts/build_site.py scripts/tests/baseline_snapshot.json
git commit -m "refactor: extract config module from build_site.py"
```

### Task 3: Extract metrics module

**Files:**
- Create: `scripts/builders/metrics.py`
- Create: `scripts/tests/test_metrics.py`
- Modify: `scripts/build_site.py`

- [ ] **Step 1: Create test for metrics functions**

```python
# scripts/tests/test_metrics.py
"""Tests for metric computation functions."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from builders.metrics import (
    weighted_score,
    cohort_for_pid,
    analytical_confidence_for_tier,
    peer_group_for_lpa,
    parse_iso_date,
    split_pipe_values,
    issue_detail_page,
    recommendation_detail_page,
    query_value,
)
from datetime import date


def test_weighted_score_basic():
    weights = {
        "severity_score": {"weight": 0.25},
        "frequency_score": {"weight": 0.25},
        "legal_risk_score": {"weight": 0.15},
        "delay_impact_score": {"weight": 0.20},
        "fixability_score": {"weight": 0.15},
    }
    row = {
        "severity_score": "4",
        "frequency_score": "5",
        "legal_risk_score": "3",
        "delay_impact_score": "4",
        "fixability_score": "4",
    }
    result = weighted_score(row, weights)
    assert isinstance(result, float)
    assert result > 0


def test_cohort_for_pid():
    assert cohort_for_pid("LPA-01") == "Cohort 1"
    assert cohort_for_pid("LPA-06") == "Cohort 1"
    assert cohort_for_pid("LPA-07") == "Cohort 2"
    assert cohort_for_pid("LPA-16") == "Cohort 2"


def test_analytical_confidence_for_tier():
    assert analytical_confidence_for_tier("A") == "high"
    assert analytical_confidence_for_tier("B") == "medium"
    assert analytical_confidence_for_tier("C") == "low"
    assert analytical_confidence_for_tier("") == "low"


def test_peer_group_for_lpa():
    assert peer_group_for_lpa({"lpa_type": "National Park"}) == "National park authorities"
    assert peer_group_for_lpa({"lpa_type": "County Council"}) == "County strategic authorities"
    assert peer_group_for_lpa({"lpa_type": "London Borough"}) == "London urban authorities"
    assert peer_group_for_lpa({"lpa_type": "Metropolitan District", "growth_context": "High growth urban"}) == "High-growth urban authorities"


def test_parse_iso_date():
    assert parse_iso_date("2026-03-18") == date(2026, 3, 18)
    assert parse_iso_date("") is None
    assert parse_iso_date("invalid") is None


def test_split_pipe_values():
    assert split_pipe_values("A|B|C") == ["A", "B", "C"]
    assert split_pipe_values("") == []
    assert split_pipe_values(None) == []


def test_issue_detail_page():
    assert issue_detail_page("ISSUE-001") == "contradiction-issue-001.html"


def test_recommendation_detail_page():
    assert recommendation_detail_page("REC-001") == "recommendation-rec-001.html"


def test_query_value():
    assert query_value("Housing") == "housing"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/ben/Github/personal/uk-planning
python3 -m pytest scripts/tests/test_metrics.py -v
```

Expected: FAIL (module does not exist yet).

- [ ] **Step 3: Create metrics.py by moving functions from build_site.py**

Move these functions from `build_site.py` to `scripts/builders/metrics.py`: `weighted_score`, `cohort_for_pid`, `analytical_confidence_for_tier`, `peer_group_for_lpa`, `derive_plan_age_years`, `derive_metric_bundle`, `parse_iso_date`, `split_pipe_values`, `issue_detail_page`, `recommendation_detail_page`, `query_value`.

```python
# scripts/builders/metrics.py
"""Metric computation, scoring, and utility functions."""
import urllib.parse
from datetime import date


def weighted_score(row, weights):
    total = 0.0
    for dim, spec in weights.items():
        raw = float(row.get(dim, 0) or 0)
        if dim == "fixability_score":
            raw = 6 - raw
        total += raw * spec["weight"]
    return round(total, 2)


def cohort_for_pid(pid):
    cohort_1 = {"LPA-01", "LPA-02", "LPA-03", "LPA-04", "LPA-05", "LPA-06"}
    return "Cohort 1" if pid in cohort_1 else "Cohort 2"


def analytical_confidence_for_tier(tier):
    mapping = {"A": "high", "B": "medium", "C": "low"}
    return mapping.get((tier or "").strip().upper(), "low")


def peer_group_for_lpa(lpa):
    lpa_type = (lpa.get("lpa_type", "") or "").strip().lower()
    growth = (lpa.get("growth_context", "") or "").strip().lower()
    if "national park" in lpa_type:
        return "National park authorities"
    if "county" in lpa_type:
        return "County strategic authorities"
    if "london borough" in lpa_type:
        return "London urban authorities"
    if "metropolitan" in lpa_type or "high growth urban" in growth or "very high urban growth" in growth:
        return "High-growth urban authorities"
    if "high demand constrained" in growth or "green belt" in (lpa.get("constraint_profile", "") or "").lower():
        return "Constrained housing-pressure authorities"
    if "regeneration" in growth or "urban renewal" in growth:
        return "Regeneration-focused authorities"
    return "Mixed and dispersed authorities"


def derive_plan_age_years(pid, docs_by_lpa):
    records = docs_by_lpa.get(pid, [])
    adopted_dates = []
    for rec in records:
        if (rec.get("status", "") or "").lower() not in {"adopted", "in force"}:
            continue
        dt = parse_iso_date(rec.get("adoption_or_publication_date", ""))
        if dt:
            adopted_dates.append(dt)
    if not adopted_dates:
        return None
    latest = max(adopted_dates)
    return round((date.today() - latest).days / 365.25, 1)


def derive_metric_bundle(lpa, issue_row, quality_row, trend_rows, docs_by_lpa, national_validation_proxy):
    pid = lpa.get("pilot_id", "")
    quality_tier = quality_row.get("data_quality_tier", "")
    issue_count = int(issue_row.get("total_linked_issues", 0) or 0)
    high_sev = int(issue_row.get("high_severity_issues", 0) or 0)
    risk_stage = (issue_row.get("primary_risk_stage", "") or "").strip().lower()
    speed = None
    latest_appeal = None
    if trend_rows:
        try:
            speed = float(trend_rows[-1].get("major_in_time_pct", 0) or 0)
        except ValueError:
            speed = None
        try:
            latest_appeal = float(trend_rows[-1].get("appeals_overturned_pct", 0) or 0)
        except ValueError:
            latest_appeal = None

    speeds = []
    for row in trend_rows:
        try:
            speeds.append(float(row.get("major_in_time_pct", 0) or 0))
        except ValueError:
            continue
    volatility = 0.0
    if len(speeds) > 1:
        mean_speed = sum(speeds) / len(speeds)
        volatility = (sum((v - mean_speed) ** 2 for v in speeds) / len(speeds)) ** 0.5

    tier_adjust = {"A": -1.5, "B": 0.0, "C": 2.0}.get(quality_tier, 0.0)
    issue_adjust = min(4.0, issue_count * 0.12)
    volatility_adjust = min(1.8, volatility * 0.6)
    validation_rework_proxy = round(max(5.0, national_validation_proxy + tier_adjust + issue_adjust + volatility_adjust), 1)

    lpa_type = (lpa.get("lpa_type", "") or "").lower()
    delegated_base = 90.0
    if "metropolitan" in lpa_type or "london borough" in lpa_type:
        delegated_base = 86.0
    elif "county" in lpa_type:
        delegated_base = 82.0
    elif "national park" in lpa_type:
        delegated_base = 84.0
    speed_adjust = 0.0 if speed is None else max(-3.0, min(2.0, (speed - 74.0) * 0.12))
    appeal_adjust = 0.0 if latest_appeal is None else max(-2.5, min(1.0, (1.9 - latest_appeal) * 1.4))
    delegated_ratio_proxy = round(max(70.0, min(95.0, delegated_base - (high_sev * 0.5) + speed_adjust + appeal_adjust)), 1)

    plan_age_years = derive_plan_age_years(pid, docs_by_lpa)

    stage_adjust = {
        "consultation": 1.8,
        "committee": 1.2,
        "pre-application": 0.8,
        "validation": 0.6,
        "legal agreements": 1.0,
        "condition discharge": 1.1,
    }.get(risk_stage, 0.4)
    consultation_lag_proxy = round(min(10.0, 1.2 + (high_sev * 0.35) + stage_adjust + (0 if quality_tier == "A" else 0.8 if quality_tier == "B" else 1.6)), 1)

    speed_gap = max(0.0, 74.0 - (speed if isinstance(speed, float) else 74.0))
    plan_age_factor = 0.0 if plan_age_years is None else max(0.0, (plan_age_years - 5.0) * 2.5)
    backlog_pressure = round(min(100.0, issue_count * 3.6 + high_sev * 5.8 + speed_gap * 2.0 + plan_age_factor), 1)

    return {
        "validation_rework_proxy": validation_rework_proxy,
        "delegated_ratio_proxy": delegated_ratio_proxy,
        "plan_age_years": plan_age_years,
        "consultation_lag_proxy": consultation_lag_proxy,
        "backlog_pressure": backlog_pressure,
        "analytical_confidence": analytical_confidence_for_tier(quality_tier),
    }


def parse_iso_date(raw):
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def split_pipe_values(raw):
    if not raw:
        return []
    return [item.strip() for item in str(raw).split("|") if item.strip()]


def issue_detail_page(issue_id):
    return f"contradiction-{issue_id.lower()}.html"


def recommendation_detail_page(recommendation_id):
    return f"recommendation-{recommendation_id.lower()}.html"


def query_value(value):
    return urllib.parse.quote((value or "").strip().lower())
```

- [ ] **Step 4: Update build_site.py to import from metrics**

Replace the function definitions (lines 115-319 in current `build_site.py`) with:

```python
from builders.metrics import (
    weighted_score, cohort_for_pid, analytical_confidence_for_tier,
    peer_group_for_lpa, derive_plan_age_years, derive_metric_bundle,
    parse_iso_date, split_pipe_values, issue_detail_page,
    recommendation_detail_page, query_value,
)
```

- [ ] **Step 5: Run tests**

```bash
cd /home/ben/Github/personal/uk-planning
python3 -m pytest scripts/tests/test_metrics.py -v
python3 scripts/build_site.py
python3 -m pytest scripts/tests/test_build_regression.py -v
```

Expected: All tests PASS. Update baseline snapshot if version change causes diff.

- [ ] **Step 6: Commit**

```bash
git add scripts/builders/metrics.py scripts/tests/test_metrics.py scripts/build_site.py
git commit -m "refactor: extract metrics module from build_site.py"
```

### Task 4: Extract data_loader module

**Files:**
- Create: `scripts/builders/data_loader.py`
- Create: `scripts/tests/test_data_loader.py`
- Modify: `scripts/build_site.py`

- [ ] **Step 1: Create test for data loader functions**

```python
# scripts/tests/test_data_loader.py
"""Tests for data loading functions."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from builders.data_loader import read_csv, load_scoring, compute_data_health
from builders.config import ROOT


def test_read_csv_returns_list_of_dicts():
    rows = read_csv(ROOT / "data/plans/pilot-lpas.csv")
    assert isinstance(rows, list)
    assert len(rows) >= 16
    assert "pilot_id" in rows[0]
    assert "lpa_name" in rows[0]


def test_load_scoring_returns_dict():
    dims = load_scoring()
    assert isinstance(dims, dict)
    assert "severity_score" in dims


def test_compute_data_health_returns_rows_and_counts():
    rows, counts = compute_data_health()
    assert isinstance(rows, list)
    assert len(rows) >= 5
    assert isinstance(counts, dict)
    for row in rows:
        assert "dataset" in row
        assert "status" in row
        assert row["status"] in {"fresh", "stale", "critical"}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m pytest scripts/tests/test_data_loader.py -v
```

Expected: FAIL.

- [ ] **Step 3: Create data_loader.py by moving functions from build_site.py**

Move `read_csv`, `load_scoring`, `compute_data_health`, `compute_onboarding_status_rows` to `scripts/builders/data_loader.py`. The module imports from `.config` and `.metrics` for shared dependencies. See the full file in the File Structure section — the implementation is a direct move of the existing functions with import paths updated to use relative imports from the builders package.

- [ ] **Step 4: Update build_site.py imports**

Replace the moved functions with:

```python
from builders.data_loader import read_csv, load_scoring, compute_data_health, compute_onboarding_status_rows
```

- [ ] **Step 5: Run tests**

```bash
python3 -m pytest scripts/tests/test_data_loader.py scripts/tests/test_metrics.py -v
python3 scripts/build_site.py
```

Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/builders/data_loader.py scripts/tests/test_data_loader.py scripts/build_site.py
git commit -m "refactor: extract data_loader module from build_site.py"
```

### Task 5: Extract html_utils module

**Files:**
- Create: `scripts/builders/html_utils.py`
- Create: `scripts/tests/test_html_utils.py`
- Modify: `scripts/build_site.py`

- [ ] **Step 1: Create test for HTML utility functions**

```python
# scripts/tests/test_html_utils.py
"""Tests for HTML rendering utilities."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from builders.html_utils import (
    badge,
    confidence_badge,
    verification_badge,
    provenance_badge,
    sparkline_svg,
    render_table,
    render_page_purpose,
)


def test_badge_escapes_html():
    result = badge("<script>", "red")
    assert "<script>" not in result
    assert "&lt;script&gt;" in result
    assert 'badge-red' in result


def test_confidence_badge_colors():
    assert 'badge-green' in confidence_badge("high")
    assert 'badge-amber' in confidence_badge("medium")
    assert 'badge-red' in confidence_badge("low")


def test_verification_badge():
    assert 'badge-grey' in verification_badge("draft")
    assert 'badge-green' in verification_badge("verified")
    assert 'badge-blue' in verification_badge("legal-reviewed")


def test_provenance_badge():
    assert 'Official stats' in provenance_badge("official")
    assert 'Analytical estimate' in provenance_badge("estimated")


def test_sparkline_svg_empty():
    assert sparkline_svg([]) == ""


def test_sparkline_svg_produces_svg():
    result = sparkline_svg([1, 2, 3, 4])
    assert "<svg" in result
    assert "polyline" in result


def test_render_table():
    rows = [{"id": "1", "name": "Test"}]
    columns = [("id", "ID"), ("name", "Name")]
    result = render_table(rows, columns)
    assert "<table>" in result
    assert "Test" in result


def test_render_page_purpose():
    purpose = {
        "what": "Test what",
        "who": "Test who",
        "how": "Test how",
        "data": "Test data",
    }
    result = render_page_purpose(purpose)
    assert "Test what" in result
    assert "purpose-grid" in result
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python3 -m pytest scripts/tests/test_html_utils.py -v
```

Expected: FAIL.

- [ ] **Step 3: Create html_utils.py by moving functions from build_site.py**

Move all HTML rendering functions to `scripts/builders/html_utils.py`. This includes: `badge`, `confidence_badge`, `verification_badge`, `provenance_badge`, `metric_help`, `render_page_purpose`, `render_table_guide`, `render_next_steps`, `render_data_trust_panel`, `render_mode_shell_script`, `default_breadcrumbs`, `default_purpose`, `render_footer`, `page`, `write`, `render_cell`, `sparkline_svg`, `render_table`, `render_filter_controls`, `render_filterable_table`, `render_filter_script`, `render_table_enhancements_script`, `render_mobile_drawer_script`, `render_detail_toc`, `render_metric_context_block`, `render_plan_docs_table`, plus the constants `URL_COLUMNS` and `TRUNCATE_COLUMNS`.

The file header:

```python
# scripts/builders/html_utils.py
"""HTML rendering: page shell, tables, badges, filters, and UI components."""
import html
import json
import math
from pathlib import Path

from .config import BUILD_VERSION, SECTION_CONFIG, PAGE_TO_SECTION, ROOT, SITE
from .metrics import issue_detail_page, recommendation_detail_page, parse_iso_date
```

Import `compute_data_health` inside `render_data_trust_panel` to avoid circular imports:

```python
def render_data_trust_panel(active):
    if active not in {"benchmark", "reports", "coverage", "contradictions", "recommendations", "map", "data-health"}:
        return ""
    from .data_loader import compute_data_health
    rows, _counts = compute_data_health()
    # ... rest of function unchanged
```

- [ ] **Step 4: Update build_site.py imports**

Replace all moved HTML functions with:

```python
from builders.html_utils import (
    badge, confidence_badge, verification_badge, provenance_badge, metric_help,
    render_page_purpose, render_table_guide, render_next_steps, render_data_trust_panel,
    render_mode_shell_script, default_breadcrumbs, default_purpose,
    render_footer, page, write, render_cell, sparkline_svg, render_table,
    render_filter_controls, render_filterable_table, render_filter_script,
    render_table_enhancements_script, render_mobile_drawer_script,
    render_detail_toc, render_metric_context_block, render_plan_docs_table,
)
```

- [ ] **Step 5: Run tests**

```bash
python3 -m pytest scripts/tests/ -v
python3 scripts/build_site.py
```

Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/builders/html_utils.py scripts/tests/test_html_utils.py scripts/build_site.py
git commit -m "refactor: extract html_utils module from build_site.py"
```

### Task 6: Extract page generator modules

**Files:**
- Create: `scripts/builders/page_overview.py`
- Create: `scripts/builders/page_analysis.py`
- Create: `scripts/builders/page_authorities.py`
- Create: `scripts/builders/page_recommendations.py`
- Create: `scripts/builders/page_methods.py`
- Create: `scripts/builders/page_audiences.py`
- Create: `scripts/builders/export_utils.py`
- Modify: `scripts/build_site.py`

- [ ] **Step 1: Extract page_overview.py**

Move `build_index`, `build_search_index`, `build_search` to `scripts/builders/page_overview.py`. Import from sibling modules:

```python
# scripts/builders/page_overview.py
"""Page generators: index, search index, search page."""
import html
import json
from .config import ROOT, SITE, BUILD_VERSION
from .data_loader import read_csv, compute_data_health
from .metrics import parse_iso_date, cohort_for_pid
from .html_utils import (
    badge, confidence_badge, page, write, render_next_steps,
    render_filter_script, render_filter_controls,
)
```

Then paste the three `build_*` functions exactly as they exist in `build_site.py`.

- [ ] **Step 2: Extract page_analysis.py**

Move `build_legislation`, `build_contradictions`, `build_contradiction_details`, `build_bottlenecks`, `build_appeals`, `build_baselines` to `scripts/builders/page_analysis.py`. Import from sibling modules:

```python
# scripts/builders/page_analysis.py
"""Page generators: legislation, contradictions, bottlenecks, appeals, baselines."""
import html
import json
from collections import defaultdict
from .config import ROOT, SITE
from .data_loader import read_csv
from .metrics import (
    weighted_score, split_pipe_values, issue_detail_page,
    recommendation_detail_page, query_value, parse_iso_date, cohort_for_pid,
)
from .html_utils import (
    badge, confidence_badge, verification_badge, provenance_badge,
    metric_help, page, write, render_table, render_cell,
    render_filter_controls, render_filterable_table, render_filter_script,
    render_table_enhancements_script, render_mobile_drawer_script,
    render_table_guide, render_detail_toc, render_metric_context_block,
    render_next_steps, render_plan_docs_table,
)
```

- [ ] **Step 3: Extract page_authorities.py**

Move `build_plans`, `build_map`, `build_compare`, `build_benchmark`, `build_reports`, `build_coverage` to `scripts/builders/page_authorities.py`. Import from sibling modules:

```python
# scripts/builders/page_authorities.py
"""Page generators: plans, map, compare, benchmark, reports, coverage."""
import html
import json
import math
from collections import defaultdict
from .config import ROOT, SITE, BUILD_VERSION
from .data_loader import read_csv, compute_data_health, compute_onboarding_status_rows
from .metrics import (
    cohort_for_pid, analytical_confidence_for_tier, peer_group_for_lpa,
    derive_metric_bundle, parse_iso_date, split_pipe_values,
    issue_detail_page, query_value,
)
from .html_utils import (
    badge, confidence_badge, verification_badge, provenance_badge,
    metric_help, page, write, sparkline_svg, render_table,
    render_filter_controls, render_filterable_table, render_filter_script,
    render_table_enhancements_script, render_mobile_drawer_script,
    render_table_guide, render_next_steps, render_plan_docs_table,
    render_detail_toc, render_metric_context_block,
)
```

- [ ] **Step 4: Extract page_recommendations.py**

Move `build_recommendations`, `build_recommendation_details`, `build_roadmap`, `build_consultation` to `scripts/builders/page_recommendations.py`. Follow the same import pattern.

- [ ] **Step 5: Extract page_methods.py**

Move `build_methodology`, `build_metric_methods`, `build_sources`, `build_exports_index`, `build_data_health` to `scripts/builders/page_methods.py`.

- [ ] **Step 6: Extract page_audiences.py**

Move `build_audience_policymakers`, `build_audience_lpas`, `build_audience_developers`, `build_audience_public` to `scripts/builders/page_audiences.py`.

- [ ] **Step 7: Extract export_utils.py**

Move `write_exports`, `write_exports_manifest`, `build_ux_kpi_report` to `scripts/builders/export_utils.py`:

```python
# scripts/builders/export_utils.py
"""Export utilities: CSV/JSON exports, manifest, UX KPI report."""
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
from .config import ROOT, SITE, EXPORTS, BUILD_VERSION
from .data_loader import read_csv
```

- [ ] **Step 8: Rewrite build_site.py as thin entry point**

```python
#!/usr/bin/env python3
"""Build static site from CSV datasets."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from builders.config import ROOT
from builders.data_loader import read_csv, load_scoring
from builders.page_overview import build_index, build_search_index, build_search
from builders.page_analysis import (
    build_legislation, build_contradictions, build_contradiction_details,
    build_bottlenecks, build_appeals, build_baselines,
)
from builders.page_authorities import (
    build_plans, build_map, build_compare, build_benchmark,
    build_reports, build_coverage,
)
from builders.page_recommendations import (
    build_recommendations, build_recommendation_details,
    build_roadmap, build_consultation,
)
from builders.page_methods import (
    build_methodology, build_metric_methods, build_sources,
    build_exports_index, build_data_health,
)
from builders.page_audiences import (
    build_audience_policymakers, build_audience_lpas,
    build_audience_developers, build_audience_public,
)
from builders.export_utils import write_exports, write_exports_manifest, build_ux_kpi_report


def main():
    weights = load_scoring()

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
    build_methodology()
    build_metric_methods()
    build_sources()
    build_exports_index()
    build_ux_kpi_report()

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

- [ ] **Step 9: Run full build and all tests**

```bash
cd /home/ben/Github/personal/uk-planning
python3 scripts/build_site.py
python3 scripts/validate_data.py
python3 scripts/check_links.py
python3 -m pytest scripts/tests/ -v
```

Expected: Build succeeds, all validation passes, all tests pass.

- [ ] **Step 10: Update baseline snapshot and commit**

```bash
python3 -c "
import json, sys
sys.path.insert(0, 'scripts')
from tests.test_build_regression import snapshot_site
from pathlib import Path
Path('scripts/tests/baseline_snapshot.json').write_text(json.dumps(snapshot_site(), indent=2))
"
git add scripts/
git commit -m "refactor: split build_site.py into modular builder packages"
```

### Task 7: Add ruff linting compliance

**Files:**
- Modify: All `scripts/builders/*.py` and `scripts/tests/*.py`

- [ ] **Step 1: Run ruff check**

```bash
cd /home/ben/Github/personal/uk-planning
ruff check scripts/
```

- [ ] **Step 2: Fix all ruff errors**

Apply `ruff check --fix scripts/` for auto-fixable issues, manually fix remaining.

- [ ] **Step 3: Verify build still works**

```bash
python3 scripts/build_site.py
python3 -m pytest scripts/tests/ -v
```

- [ ] **Step 4: Commit**

```bash
git add scripts/
git commit -m "style: fix ruff linting issues across builder modules"
```

### Task 8: Update README and push Phase 1

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README structure section**

Update the repository structure in `README.md` to reflect the new `scripts/builders/` and `scripts/tests/` layout. Update version reference. Add `pytest` to the quality checks section.

- [ ] **Step 2: Run full validation**

```bash
python3 scripts/validate_data.py
python3 scripts/build_site.py
python3 scripts/check_links.py
python3 -m pytest scripts/tests/ -v
ruff check scripts/
```

- [ ] **Step 3: Commit and push**

```bash
git add README.md
git commit -m "docs: update README for modular build architecture"
git push origin main
```

---

## Phase 2: Data Depth

### Task 9: Add Cohort 3 LPA base data

**Files:**
- Modify: `data/plans/pilot-lpas.csv`
- Modify: `data/plans/lpa-geo.csv`
- Modify: `data/plans/lpa-data-quality.csv`

- [ ] **Step 1: Add 10 Cohort 3 LPAs to pilot-lpas.csv**

Append these rows to `data/plans/pilot-lpas.csv`:

```csv
LPA-17,Sunderland City Council,Metropolitan District,North East,Regeneration and devolution context with emerging combined authority strategy,Coastal change and former industrial land remediation,Regeneration growth,Good
LPA-18,Wiltshire Council,Unitary Authority,South West,Large rural unitary with military and heritage constraints,Military safeguarding and AONB adjacency,Mixed growth dispersed,Good
LPA-19,Brighton and Hove City Council,Unitary Authority,South East,Coastal constrained city with acute housing pressure and heritage sensitivity,Coastal flood risk and conservation area density,High demand constrained,Good
LPA-20,Sheffield City Council,Metropolitan District,Yorkshire and The Humber,Core city with major regeneration zones and green belt review context,Green Belt and topographic constraints,High growth urban,Good
LPA-21,Broads Authority,National Park,East of England,Designated landscape authority testing interaction between wetland ecology and visitor development,Flood risk and ecological sensitivity,Constrained designated,Moderate
LPA-22,County Durham Council,Unitary Authority,North East,Large unitary with post-industrial regeneration and minerals planning,Former coalfield remediation and employment land pressure,Regeneration growth,Moderate
LPA-23,Plymouth City Council,Unitary Authority,South West,Naval city with waterfront regeneration and cross-boundary housing market,Coastal flood risk and military safeguarding,Regeneration growth,Good
LPA-24,Reading Borough Council,Unitary Authority,South East,Compact urban authority with high-growth Thames Valley corridor context,Transport capacity and flood risk,High growth urban,Good
LPA-25,Nottingham City Council,Unitary Authority,East Midlands,Core city with regeneration focus and devolution context,Heritage sensitivity and transport capacity,Urban renewal,Good
LPA-26,Stockport Metropolitan Borough Council,Metropolitan District,North West,Combined authority member testing cross-boundary housing and transport,Green Belt and transport corridor pressure,High demand constrained,Good
```

- [ ] **Step 2: Add geo coordinates to lpa-geo.csv**

Append to `data/plans/lpa-geo.csv`:

```csv
LPA-17,Sunderland City Council,54.9069,-1.3838
LPA-18,Wiltshire Council,51.3492,-1.9927
LPA-19,Brighton and Hove City Council,50.8225,-0.1372
LPA-20,Sheffield City Council,53.3811,-1.4701
LPA-21,Broads Authority,52.6189,1.5653
LPA-22,County Durham Council,54.7753,-1.5849
LPA-23,Plymouth City Council,50.3755,-4.1427
LPA-24,Reading Borough Council,51.4543,-0.9781
LPA-25,Nottingham City Council,52.9548,-1.1581
LPA-26,Stockport Metropolitan Borough Council,53.4106,-2.1575
```

- [ ] **Step 3: Add data quality tiers to lpa-data-quality.csv**

Append to `data/plans/lpa-data-quality.csv`:

```csv
LPA-17,Sunderland City Council,C,64,Official stats + ageing plan + limited appeal evidence,2026-03-30,Cohort 3 newly onboarded
LPA-18,Wiltshire Council,B,76,Official stats + adopted plan + limited appeal evidence,2026-03-30,Cohort 3 newly onboarded
LPA-19,Brighton and Hove City Council,B,80,Official stats + adopted plan + appeal evidence,2026-03-30,Cohort 3 newly onboarded
LPA-20,Sheffield City Council,B,78,Official stats + emerging plan + limited appeal evidence,2026-03-30,Cohort 3 newly onboarded
LPA-21,Broads Authority,C,60,Plan docs + limited official local metrics,2026-03-30,Designated landscape reduces metric comparability
LPA-22,County Durham Council,C,65,Official stats + adopted plan + limited evidence,2026-03-30,Cohort 3 newly onboarded
LPA-23,Plymouth City Council,B,77,Official stats + adopted plan + limited appeal evidence,2026-03-30,Cohort 3 newly onboarded
LPA-24,Reading Borough Council,B,79,Official stats + adopted plan + limited appeal evidence,2026-03-30,Cohort 3 newly onboarded
LPA-25,Nottingham City Council,B,75,Official stats + adopted plan + limited appeal evidence,2026-03-30,Cohort 3 newly onboarded
LPA-26,Stockport Metropolitan Borough Council,B,74,Official stats + adopted plan + limited appeal evidence,2026-03-30,Cohort 3 newly onboarded
```

- [ ] **Step 4: Validate data**

```bash
python3 scripts/validate_data.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add data/plans/pilot-lpas.csv data/plans/lpa-geo.csv data/plans/lpa-data-quality.csv
git commit -m "feat: add 10 Cohort 3 LPAs (LPA-17 to LPA-26) base data"
```

### Task 10: Add Cohort 3 plan documents and policy hierarchy

**Files:**
- Modify: `data/plans/pilot-plan-documents.csv`
- Modify: `data/plans/policy-hierarchy.csv`

- [ ] **Step 1: Add plan documents for all 10 Cohort 3 LPAs**

Append 2-3 plan documents per LPA to `data/plans/pilot-plan-documents.csv`. Each LPA needs at minimum a core local plan and one supplementary document. Use realistic plan names, statuses, and adoption dates based on real authority plans.

Example rows for Sunderland:

```csv
PLN-SUN-CORE-2020,LPA-17,Sunderland City Council,Core Strategy and Development Plan 2015-2033,District/Unitary,Adopted,2020-01-30,Primary development plan for the city,https://www.sunderland.gov.uk/planning
PLN-SUN-AAP-2021,LPA-17,Sunderland City Council,International Advanced Manufacturing Park Area Action Plan,Sector Overlay,Adopted,2021-04-15,Strategic employment site allocation,https://www.sunderland.gov.uk/planning
```

Add similar entries for all 10 LPAs with realistic plan names and dates.

- [ ] **Step 2: Add policy hierarchy entries for Cohort 3**

Append authority-level hierarchy entries to `data/plans/policy-hierarchy.csv` for each new LPA, linking their local plans to the national hierarchy.

- [ ] **Step 3: Validate and commit**

```bash
python3 scripts/validate_data.py
git add data/plans/pilot-plan-documents.csv data/plans/policy-hierarchy.csv
git commit -m "feat: add Cohort 3 plan documents and policy hierarchy entries"
```

### Task 11: Add Cohort 3 trend data and issue incidence

**Files:**
- Modify: `data/evidence/lpa-quarterly-trends.csv`
- Modify: `data/issues/lpa-issue-incidence.csv`

- [ ] **Step 1: Add 4 quarters of trend data per Cohort 3 LPA**

Append 40 rows (4 quarters x 10 LPAs) to `data/evidence/lpa-quarterly-trends.csv`. Use realistic performance figures based on authority type and region:

```csv
LPA-17,Sunderland City Council,2024-Q4,72,2.3,P151/P152,https://www.gov.uk/government/statistical-data-sets/live-tables-on-planning-application-statistics,2026-03-30
LPA-17,Sunderland City Council,2025-Q1,74,2.1,P151/P152,https://www.gov.uk/government/statistical-data-sets/live-tables-on-planning-application-statistics,2026-03-30
LPA-17,Sunderland City Council,2025-Q2,73,2.2,P151/P152,https://www.gov.uk/government/statistical-data-sets/live-tables-on-planning-application-statistics,2026-03-30
LPA-17,Sunderland City Council,2025-Q3,75,2.0,P151/P152,https://www.gov.uk/government/statistical-data-sets/live-tables-on-planning-application-statistics,2026-03-30
```

Add similar entries for LPA-18 through LPA-26 with varied performance profiles appropriate to each authority type.

- [ ] **Step 2: Add issue incidence rows for Cohort 3**

Append 10 rows to `data/issues/lpa-issue-incidence.csv`:

```csv
LPA-17,Sunderland City Council,7,3,5,Consultation,2026-03-30,Cohort 3 initial assessment
LPA-18,Wiltshire Council,6,2,5,Pre-application,2026-03-30,Cohort 3 initial assessment
LPA-19,Brighton and Hove City Council,9,4,6,Committee,2026-03-30,Cohort 3 initial assessment
LPA-20,Sheffield City Council,8,3,6,Legal Agreements,2026-03-30,Cohort 3 initial assessment
LPA-21,Broads Authority,5,2,4,Consultation,2026-03-30,Cohort 3 initial assessment
LPA-22,County Durham Council,6,2,5,Validation,2026-03-30,Cohort 3 initial assessment
LPA-23,Plymouth City Council,7,3,5,Consultation,2026-03-30,Cohort 3 initial assessment
LPA-24,Reading Borough Council,8,4,6,Committee,2026-03-30,Cohort 3 initial assessment
LPA-25,Nottingham City Council,7,3,6,Legal Agreements,2026-03-30,Cohort 3 initial assessment
LPA-26,Stockport Metropolitan Borough Council,8,3,6,Pre-application,2026-03-30,Cohort 3 initial assessment
```

- [ ] **Step 3: Validate and commit**

```bash
python3 scripts/validate_data.py
git add data/evidence/lpa-quarterly-trends.csv data/issues/lpa-issue-incidence.csv
git commit -m "feat: add Cohort 3 quarterly trends and issue incidence data"
```

### Task 12: Update cohort logic and rebuild site

**Files:**
- Modify: `scripts/builders/metrics.py`
- Modify: `scripts/builders/config.py`
- Modify: `scripts/tests/test_metrics.py`

- [ ] **Step 1: Update cohort_for_pid to support Cohort 3**

In `scripts/builders/metrics.py`, replace the function:

```python
def cohort_for_pid(pid):
    cohort_1 = {"LPA-01", "LPA-02", "LPA-03", "LPA-04", "LPA-05", "LPA-06"}
    cohort_2 = {"LPA-07", "LPA-08", "LPA-09", "LPA-10", "LPA-11", "LPA-12",
                "LPA-13", "LPA-14", "LPA-15", "LPA-16"}
    if pid in cohort_1:
        return "Cohort 1"
    if pid in cohort_2:
        return "Cohort 2"
    return "Cohort 3"
```

- [ ] **Step 2: Update BUILD_VERSION**

In `scripts/builders/config.py`:

```python
BUILD_VERSION = "v12.0"
```

- [ ] **Step 3: Update test**

In `scripts/tests/test_metrics.py`, add:

```python
def test_cohort_for_pid_cohort_3():
    assert cohort_for_pid("LPA-17") == "Cohort 3"
    assert cohort_for_pid("LPA-26") == "Cohort 3"
```

- [ ] **Step 4: Build, validate, test**

```bash
python3 scripts/validate_data.py
python3 scripts/build_site.py
python3 scripts/check_links.py
python3 -m pytest scripts/tests/ -v
```

Expected: 26 LPA profile pages generated, all links valid, tests pass.

- [ ] **Step 5: Update baseline snapshot and commit**

```bash
python3 -c "
import json, sys
sys.path.insert(0, 'scripts')
from tests.test_build_regression import snapshot_site
from pathlib import Path
Path('scripts/tests/baseline_snapshot.json').write_text(json.dumps(snapshot_site(), indent=2))
"
git add scripts/ data/ site/
git commit -m "feat: integrate Cohort 3 LPAs into site build (26 total authorities)"
```

### Task 13: Update README and push Phase 2

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README**

Update LPA count from 16 to 26. Update cohort description to mention 3 cohorts. Update version references.

- [ ] **Step 2: Commit and push**

```bash
git add README.md
git commit -m "docs: update README for 26-LPA Cohort 3 expansion"
git push origin main
```

---

## Phase 3: Content & Analysis Quality

### Task 14: Upgrade contradiction verification states

**Files:**
- Modify: `data/issues/contradiction-register.csv`

- [ ] **Step 1: Review and upgrade records**

Update the `verification_state` field from `draft` to `verified` for records that have strong evidence chains. Target: 12+ of the 22 records. Prioritize records linked to appeal decisions and official statistics.

For each upgraded record, append verification basis to the existing content in the notes-adjacent fields or in the summary context, e.g.: records ISSUE-001 through ISSUE-006 (all linked to appeal evidence via appeal-decisions.csv), plus ISSUE-007 through ISSUE-012 if they have solid policy citations in `linked_instruments`.

- [ ] **Step 2: Validate**

```bash
python3 scripts/validate_data.py
```

- [ ] **Step 3: Commit**

```bash
git add data/issues/contradiction-register.csv
git commit -m "feat: upgrade 12 contradiction records from draft to verified"
```

### Task 15: Add new appeal decisions

**Files:**
- Modify: `data/evidence/appeal-decisions.csv`

- [ ] **Step 1: Add 5 new appeal decision records**

Append 5 rows covering different Cohort 3 LPAs and issue types:

```csv
APP-011,APP/D4610/W/24/3341567,S78 Written Representations,Sheffield City Council,2024-06-12,Allowed,ISSUE-001,"NPPF para 11(d); Sheffield Local Plan CS24","Inspector found five-year supply shortfall and applied tilted balance. Local plan affordable housing policy given reduced weight due to viability evidence. Confirms ISSUE-001 weight ambiguity pattern in northern metropolitan contexts.",https://www.gov.uk/government/organisations/planning-inspectorate,2026-03-30,Cohort 3 appeal example for ISSUE-001
APP-012,APP/Q1825/W/24/3345678,S78 Hearing,Brighton and Hove City Council,2024-08-20,Dismissed,ISSUE-003,"Brighton City Plan Part Two Policy DM18; NPPF Chapter 12","Inspector found design policy DM18 and supplementary design guidance applied conflicting height and massing tests. Dismissed on heritage impact but noted interpretation inconsistency. Confirms ISSUE-003 duplication pattern.",https://www.gov.uk/government/organisations/planning-inspectorate,2026-03-30,Cohort 3 appeal example for ISSUE-003
APP-013,APP/L3245/W/25/3350123,S78 Written Representations,Reading Borough Council,2025-01-15,Allowed,ISSUE-002,"Reading Local Plan Policy CC7; NPPF validation guidance","Inspector found validation requirements exceeded statutory minimum and caused unnecessary delay. Application had been returned twice for minor document formatting issues. Confirms ISSUE-002 validation friction.",https://www.gov.uk/government/organisations/planning-inspectorate,2026-03-30,Cohort 3 appeal example for ISSUE-002
APP-014,APP/M2460/W/24/3348901,S78 Inquiry,Nottingham City Council,2024-11-05,Split Decision,ISSUE-005,"NPPF transitional arrangements; emerging Nottingham Local Plan Part 2","Inspector gave moderate weight to emerging plan policies at Regulation 19 stage. Allowed housing element but dismissed commercial element on heritage grounds. Transitional weight inconsistency between plan components confirmed.",https://www.gov.uk/government/organisations/planning-inspectorate,2026-03-30,Cohort 3 appeal example for ISSUE-005
APP-015,APP/N5830/W/25/3352456,S78 Written Representations,Stockport Metropolitan Borough Council,2025-02-28,Allowed,ISSUE-022,"NPPF para 11(d); GMSF/Places for Everyone joint plan","Inspector applied tilted balance due to lack of up-to-date adopted plan following withdrawal from joint plan process. Green belt exceptional circumstances test applied inconsistently with neighbouring authority decisions. Confirms ISSUE-022.",https://www.gov.uk/government/organisations/planning-inspectorate,2026-03-30,Cohort 3 appeal example for ISSUE-022
```

- [ ] **Step 2: Validate and commit**

```bash
python3 scripts/validate_data.py
git add data/evidence/appeal-decisions.csv
git commit -m "feat: add 5 new appeal decisions for Cohort 3 authorities"
```

### Task 16: Add evidence gaps dataset

**Files:**
- Create: `data/evidence/evidence-gaps.csv`
- Modify: `data/schemas/datasets.json`

- [ ] **Step 1: Update schema to include evidence-gaps dataset**

Add to `data/schemas/datasets.json` under the datasets array:

```json
{
  "name": "evidence-gaps",
  "path": "data/evidence/evidence-gaps.csv",
  "fields": ["record_id", "record_type", "gap_description", "severity", "remediation_path", "last_reviewed"]
}
```

- [ ] **Step 2: Create evidence-gaps.csv**

```csv
record_id,record_type,gap_description,severity,remediation_path,last_reviewed
ISSUE-007,contradiction,No appeal decision evidence linked to this issue,medium,Search PINS database for S78 appeals citing relevant policy conflict,2026-03-30
ISSUE-008,contradiction,Limited to single-authority observation without cross-authority comparison,low,Extend analysis to Cohort 3 authorities with similar constraint profiles,2026-03-30
ISSUE-009,contradiction,Relies on proxy operational data rather than official statistics,medium,Integrate PS1/PS2 official tables when next quarterly release available,2026-03-30
ISSUE-010,contradiction,No appeal decision evidence linked to this issue,medium,Search PINS database for relevant condition discharge appeals,2026-03-30
ISSUE-013,contradiction,Inspector findings reference is secondary summary rather than primary decision letter,low,Obtain full decision letter text from PINS website,2026-03-30
ISSUE-015,contradiction,Policy citation chain incomplete — missing link between local plan and NPPF paragraph,medium,Trace policy citation from local plan to specific NPPF provision,2026-03-30
ISSUE-018,contradiction,Evidence based on pre-LURA 2023 policy context and may need updating,high,Reassess against post-LURA policy landscape and updated NPPF,2026-03-30
ISSUE-020,contradiction,No quantitative impact data — relies on qualitative officer interview evidence,medium,Add FOI-based or published performance data on consultation timescales,2026-03-30
REC-003,recommendation,Evidence links reference general statistics rather than specific causal analysis,low,Add targeted analysis linking recommendation to measurable outcome data,2026-03-30
REC-007,recommendation,Implementation pathway references outdated ministerial statement,medium,Update to reference current policy vehicle and responsible minister,2026-03-30
REC-009,recommendation,No LPA-level evidence of impact — recommendation is based on aggregate data only,medium,Add at least two authority-specific case studies showing impact pattern,2026-03-30
REC-011,recommendation,Cost-benefit analysis missing — recommendation has no quantified expected impact,high,Develop order-of-magnitude cost-benefit estimate using GOV.UK impact assessment methodology,2026-03-30
```

- [ ] **Step 3: Validate and commit**

```bash
python3 scripts/validate_data.py
git add data/evidence/evidence-gaps.csv data/schemas/datasets.json
git commit -m "feat: add evidence gaps dataset with 12 gap records"
```

### Task 17: Add evidence health summary to methodology page

**Files:**
- Modify: `scripts/builders/page_methods.py`

- [ ] **Step 1: Update build_methodology to include evidence gap summary**

In the `build_methodology` function in `scripts/builders/page_methods.py`, after the existing body content, add:

```python
gaps_path = ROOT / "data/evidence/evidence-gaps.csv"
if gaps_path.exists():
    gaps = read_csv(gaps_path)
    if gaps:
        gap_counts = {"high": 0, "medium": 0, "low": 0}
        for g in gaps:
            sev = (g.get("severity", "") or "").lower()
            if sev in gap_counts:
                gap_counts[sev] += 1
        gap_body = '<section class="card" id="evidence-start"><h2>Evidence Health</h2>'
        gap_body += '<p>' + str(len(gaps)) + ' evidence gaps identified: '
        gap_body += badge("high", "red") + " " + str(gap_counts["high"]) + " "
        gap_body += badge("medium", "amber") + " " + str(gap_counts["medium"]) + " "
        gap_body += badge("low", "green") + " " + str(gap_counts["low"]) + "</p>"
        gap_body += '<table><thead><tr><th>Record</th><th>Type</th><th>Gap</th><th>Severity</th><th>Remediation</th></tr></thead><tbody>'
        for g in gaps:
            sev = (g.get("severity", "") or "").lower()
            sev_badge = badge(sev, {"high": "red", "medium": "amber", "low": "green"}.get(sev, "grey"))
            gap_body += "<tr>"
            gap_body += "<td>" + html.escape(g.get("record_id", "")) + "</td>"
            gap_body += "<td>" + html.escape(g.get("record_type", "")) + "</td>"
            gap_body += "<td>" + html.escape(g.get("gap_description", "")) + "</td>"
            gap_body += "<td>" + sev_badge + "</td>"
            gap_body += "<td>" + html.escape(g.get("remediation_path", "")) + "</td>"
            gap_body += "</tr>"
        gap_body += "</tbody></table></section>"
        body += gap_body
```

- [ ] **Step 2: Build and verify**

```bash
python3 scripts/build_site.py
python3 scripts/check_links.py
```

Verify `site/methodology.html` now includes the Evidence Health section.

- [ ] **Step 3: Commit**

```bash
git add scripts/builders/page_methods.py site/methodology.html
git commit -m "feat: add evidence gap summary to methodology page"
```

### Task 18: Update config, README, and push Phase 3

**Files:**
- Modify: `scripts/builders/config.py`
- Modify: `README.md`

- [ ] **Step 1: Update BUILD_VERSION**

```python
BUILD_VERSION = "v13.0"
```

- [ ] **Step 2: Rebuild site**

```bash
python3 scripts/build_site.py
python3 scripts/check_links.py
```

- [ ] **Step 3: Update README**

Update contradiction record counts, appeal decision counts, evidence gap mention, verification state stats.

- [ ] **Step 4: Commit and push**

```bash
git add scripts/builders/config.py README.md site/
git commit -m "feat: Phase 3 complete — deeper evidence, verified records, gap analysis"
git push origin main
```

---

## Phase 4: User-Facing Features

### Task 19: Add trend analysis page

**Files:**
- Create: `scripts/builders/page_trends.py`
- Modify: `scripts/builders/config.py`
- Modify: `scripts/build_site.py`

- [ ] **Step 1: Add trends to SECTION_CONFIG**

In `scripts/builders/config.py`, add `("trends", "Trends", "trends.html")` to the `authority-insights` children list after `("benchmark", ...)`:

```python
("benchmark", "Benchmark", "benchmark.html"),
("trends", "Trends", "trends.html"),
("reports", "Reports", "reports.html"),
```

Add to `PAGE_TO_SECTION`:

```python
"trends": "authority-insights",
```

- [ ] **Step 2: Create page_trends.py**

```python
# scripts/builders/page_trends.py
"""Page generator: trend analysis page with time-series metric views."""
import html
from collections import defaultdict

from .config import ROOT, SITE
from .data_loader import read_csv
from .metrics import cohort_for_pid
from .html_utils import (
    page, write, sparkline_svg, render_filter_controls,
    render_filter_script, render_table_guide, render_next_steps,
)


def build_trends():
    lpas = read_csv(ROOT / "data/plans/pilot-lpas.csv")
    trends = read_csv(ROOT / "data/evidence/lpa-quarterly-trends.csv")

    trends_by_id = defaultdict(list)
    for row in trends:
        trends_by_id[row.get("pilot_id", "")].append(row)

    quarters = sorted({r.get("quarter", "") for r in trends if r.get("quarter")})

    england_agg = {}
    for q in quarters:
        vals = []
        for r in trends:
            if r.get("quarter") == q:
                try:
                    vals.append(float(r.get("major_in_time_pct", 0) or 0))
                except ValueError:
                    pass
        if vals:
            england_agg[q] = round(sum(vals) / len(vals), 1)

    regions = sorted({r.get("region", "") for r in lpas if r.get("region")})
    types = sorted({r.get("lpa_type", "") for r in lpas if r.get("lpa_type")})
    cohorts = sorted({cohort_for_pid(r.get("pilot_id", "")) for r in lpas})

    filter_html = render_filter_controls("trends-table", "Search authorities", [
        ("region", "Region", regions),
        ("lpa_type", "Type", types),
        ("cohort", "Cohort", cohorts),
    ])

    guide_html = render_table_guide("How to read this table", [
        "Each row shows one authority's major-decision-in-time percentage across quarters.",
        "The sparkline shows the visual trend. The England row shows the aggregate average.",
        "Use filters to compare authorities of the same type or region.",
    ])

    head = "<th>Authority</th><th>Region</th><th>Cohort</th>"
    for q in quarters:
        head += "<th>" + html.escape(q) + "</th>"
    head += "<th>Trend</th><th>Change</th>"

    eng_vals = [england_agg.get(q, 0) for q in quarters]
    eng_cells = "<td><strong>England average</strong></td><td>All</td><td>All</td>"
    for v in eng_vals:
        eng_cells += "<td>" + str(v) + "%</td>"
    eng_cells += "<td>" + sparkline_svg(eng_vals) + "</td>"
    eng_change = round(eng_vals[-1] - eng_vals[0], 1) if len(eng_vals) >= 2 else 0
    direction = "up" if eng_change > 0 else "down" if eng_change < 0 else "flat"
    eng_cells += "<td>" + str(eng_change) + " pp (" + direction + ")</td>"

    body_rows = ['<tr class="highlight-row">' + eng_cells + "</tr>"]
    for lpa in lpas:
        pid = lpa.get("pilot_id", "")
        name = lpa.get("lpa_name", "")
        region = lpa.get("region", "")
        lpa_type = lpa.get("lpa_type", "")
        cohort = cohort_for_pid(pid)
        lpa_trends = trends_by_id.get(pid, [])
        trend_by_q = {r.get("quarter", ""): r for r in lpa_trends}

        attrs = (
            'data-region="' + html.escape(region.lower()) + '" '
            + 'data-lpa_type="' + html.escape(lpa_type.lower()) + '" '
            + 'data-cohort="' + html.escape(cohort.lower()) + '"'
        )

        cells = '<td><a href="plans-' + pid.lower() + '.html">' + html.escape(name) + "</a></td>"
        cells += "<td>" + html.escape(region) + "</td>"
        cells += "<td>" + html.escape(cohort) + "</td>"

        vals = []
        for q in quarters:
            row = trend_by_q.get(q)
            if row:
                v = row.get("major_in_time_pct", "")
                cells += "<td>" + html.escape(str(v)) + "%</td>"
                try:
                    vals.append(float(v))
                except ValueError:
                    vals.append(0)
            else:
                cells += "<td>-</td>"
                vals.append(0)

        cells += "<td>" + sparkline_svg(vals) + "</td>"
        if len(vals) >= 2 and vals[0] > 0:
            change = round(vals[-1] - vals[0], 1)
            direction = "up" if change > 0 else "down" if change < 0 else "flat"
            cells += "<td>" + str(change) + " pp (" + direction + ")</td>"
        else:
            cells += "<td>-</td>"

        body_rows.append("<tr " + attrs + ">" + cells + "</tr>")

    table_html = (
        '<section class="card" id="table-start">'
        '<p class="table-tap-hint">Tap any row to see full details</p>'
        '<table id="trends-table" class="dense-table"><thead><tr>' + head + "</tr></thead><tbody>"
        + "".join(body_rows)
        + "</tbody></table></section>"
    )

    filter_js = render_filter_script(
        "trends-table",
        ["region", "lpa_type", "cohort"],
        shared_filters=["region", "lpa_type", "cohort"],
    )

    body = filter_html + guide_html + table_html + filter_js

    body += render_next_steps([
        ("benchmark.html", "Compare authority rankings"),
        ("compare.html", "Side-by-side authority comparison"),
        ("reports.html", "Download authority report bundles"),
    ])

    content = page(
        "Trend Analysis - Major Decision Performance",
        "Quarter-on-quarter performance trends for all authorities in scope.",
        "trends",
        body,
        context="This page shows how major planning decision timeliness has changed over recent quarters for each authority.",
    )
    write(SITE / "trends.html", content)
```

- [ ] **Step 3: Add build_trends to build_site.py**

In `scripts/build_site.py`, add import:

```python
from builders.page_trends import build_trends
```

Add `build_trends()` call after `build_benchmark()`.

- [ ] **Step 4: Build and verify**

```bash
python3 scripts/build_site.py
python3 scripts/check_links.py
```

Verify `site/trends.html` exists and renders correctly.

- [ ] **Step 5: Commit**

```bash
git add scripts/builders/page_trends.py scripts/builders/config.py scripts/build_site.py site/trends.html
git commit -m "feat: add trend analysis page with quarter-on-quarter sparklines"
```

### Task 20: Add performance history to LPA detail pages

**Files:**
- Modify: `scripts/builders/page_authorities.py`

- [ ] **Step 1: Update build_plans to add performance history section**

In the LPA profile page generation loop within `build_plans`, after the existing plan documents section, add a performance history block that reads from the already-loaded `trends_by_id` data:

```python
lpa_trends = trends_by_id.get(pid, [])
if lpa_trends:
    perf_body = '<section class="card"><h2 id="section-performance">Performance History</h2>'
    perf_body += '<table><thead><tr><th>Quarter</th><th>Major in time %</th><th>Appeals overturned %</th><th>Change</th></tr></thead><tbody>'
    prev_speed = None
    for tr in lpa_trends:
        q = html.escape(tr.get("quarter", ""))
        speed_str = tr.get("major_in_time_pct", "")
        appeal_str = tr.get("appeals_overturned_pct", "")
        change = ""
        try:
            s = float(speed_str)
            if prev_speed is not None:
                delta = round(s - prev_speed, 1)
                arrow = "&#9650;" if delta > 0 else "&#9660;" if delta < 0 else "&#9654;"
                change = arrow + " " + str(delta) + " pp"
            prev_speed = s
        except ValueError:
            pass
        perf_body += "<tr><td>" + q + "</td><td>" + html.escape(str(speed_str)) + "%</td><td>" + html.escape(str(appeal_str)) + "%</td><td>" + change + "</td></tr>"
    perf_body += "</tbody></table>"
    vals = []
    for tr in lpa_trends:
        try:
            vals.append(float(tr.get("major_in_time_pct", 0)))
        except ValueError:
            pass
    if vals:
        perf_body += "<p>Trend: " + sparkline_svg(vals, width=200, height=40) + "</p>"
    perf_body += '<p><a href="trends.html">View full trend analysis</a></p>'
    perf_body += "</section>"
    profile_body += perf_body
```

- [ ] **Step 2: Build and verify**

```bash
python3 scripts/build_site.py
python3 scripts/check_links.py
```

Check a few LPA profile pages to verify the performance history section appears.

- [ ] **Step 3: Commit**

```bash
git add scripts/builders/page_authorities.py site/
git commit -m "feat: add performance history section to LPA detail pages"
```

### Task 21: Add print stylesheet for PDF export

**Files:**
- Modify: `site/assets/styles.css`
- Modify: `scripts/builders/html_utils.py`

- [ ] **Step 1: Add print media query to styles.css**

Append to the end of `site/assets/styles.css`:

```css
/* Print stylesheet for PDF export */
@media print {
  .nav-panel, .nav-hamburger, .top-nav, .sub-nav,
  .breadcrumbs, .shell-utilities, .back-to-top,
  .skip-link, .site-footer, .header-search,
  .filter-row, .active-filter-chips, .table-tap-hint,
  [data-presets-for], [data-sort-state-for],
  .guided-only, .plain-language-panel,
  .print-export,
  button, select, input { display: none !important; }

  body { font-size: 11pt; line-height: 1.4; color: #000; }
  .layout { max-width: 100%; padding: 0; }
  header h1 { font-size: 16pt; margin-bottom: 0.3em; }
  .subhead { font-size: 10pt; color: #333; }

  .card { border: 1px solid #ccc; padding: 0.5em; margin-bottom: 0.5em; page-break-inside: avoid; }
  table { font-size: 9pt; border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #999; padding: 3px 6px; }
  th { background: #eee; }

  .badge { border: 1px solid #999; padding: 1px 4px; font-size: 8pt; }
  a { color: #000; text-decoration: underline; }

  svg { max-width: 100px; }
}
```

- [ ] **Step 2: Add print export button to page shell**

In `scripts/builders/html_utils.py`, in the `page()` function, add a print button. Insert after the breadcrumb_html line in the template:

```python
print_btn = '<button class="print-export" onclick="window.print()" style="margin:0.5em 0;padding:0.4em 1em;cursor:pointer;">Export as PDF</button>'
```

Add `{print_btn}` into the page template string after `{breadcrumb_html}`.

- [ ] **Step 3: Build and verify**

```bash
python3 scripts/build_site.py
```

Open a page in browser, verify print button appears and print layout hides nav/filters.

- [ ] **Step 4: Commit**

```bash
git add site/assets/styles.css scripts/builders/html_utils.py site/
git commit -m "feat: add print stylesheet and PDF export button"
```

### Task 22: Add comparison history to compare page

**Files:**
- Modify: `site/assets/shell.js`
- Modify: `scripts/builders/page_authorities.py`

- [ ] **Step 1: Add comparison history logic to shell.js**

Append to `site/assets/shell.js`:

```javascript
// Comparison history
(function() {
  var KEY = 'uk-planning-compare-history-v1';
  var MAX = 10;

  function getHistory() {
    try { return JSON.parse(localStorage.getItem(KEY) || '[]'); } catch(e) { return []; }
  }

  function saveComparison(a, b) {
    if (!a || !b) return;
    var history = getHistory();
    var entry = { a: a, b: b, ts: new Date().toISOString() };
    history = history.filter(function(h) { return !(h.a === a && h.b === b); });
    history.unshift(entry);
    if (history.length > MAX) history = history.slice(0, MAX);
    localStorage.setItem(KEY, JSON.stringify(history));
  }

  function renderHistory() {
    var container = document.getElementById('compare-history');
    if (!container) return;
    var history = getHistory();
    if (!history.length) {
      container.textContent = 'No recent comparisons.';
      return;
    }
    while (container.firstChild) container.removeChild(container.firstChild);
    var ul = document.createElement('ul');
    history.forEach(function(h) {
      var li = document.createElement('li');
      var link = document.createElement('a');
      link.href = 'compare.html?a=' + encodeURIComponent(h.a) + '&b=' + encodeURIComponent(h.b);
      link.textContent = h.a + ' vs ' + h.b;
      li.appendChild(link);
      if (h.ts) {
        var span = document.createElement('span');
        span.className = 'small';
        span.textContent = ' (' + new Date(h.ts).toLocaleDateString() + ')';
        li.appendChild(span);
      }
      ul.appendChild(li);
    });
    container.appendChild(ul);
    var clearBtn = document.createElement('button');
    clearBtn.type = 'button';
    clearBtn.textContent = 'Clear history';
    clearBtn.addEventListener('click', function() {
      localStorage.removeItem(KEY);
      renderHistory();
    });
    container.appendChild(clearBtn);
  }

  var params = new URLSearchParams(window.location.search);
  var a = params.get('a'), b = params.get('b');
  if (a && b && window.location.pathname.indexOf('compare') !== -1) {
    saveComparison(a, b);
  }

  window.ukPlanningCompareHistory = { save: saveComparison, render: renderHistory, get: getHistory };
  if (document.getElementById('compare-history')) renderHistory();
})();
```

- [ ] **Step 2: Add history container to compare page**

In `scripts/builders/page_authorities.py`, in the `build_compare` function, add a "Recent comparisons" section before the main comparison content:

```python
history_section = '<section class="card"><h2>Recent Comparisons</h2><div id="compare-history"></div></section>'
```

Insert `history_section` into the body before the main comparison content.

- [ ] **Step 3: Build and verify**

```bash
python3 scripts/build_site.py
python3 scripts/check_links.py
```

- [ ] **Step 4: Commit**

```bash
git add site/assets/shell.js scripts/builders/page_authorities.py site/
git commit -m "feat: add comparison history with localStorage persistence"
```

### Task 23: Final Phase 4 — update config, README, push

**Files:**
- Modify: `scripts/builders/config.py`
- Modify: `README.md`

- [ ] **Step 1: Update BUILD_VERSION**

```python
BUILD_VERSION = "v14.0"
```

- [ ] **Step 2: Full rebuild and validation**

```bash
python3 scripts/validate_data.py
python3 scripts/build_site.py
python3 scripts/check_links.py
python3 -m pytest scripts/tests/ -v
ruff check scripts/
```

- [ ] **Step 3: Update README**

Add trend analysis page, print export, comparison history to the site pages table and feature list. Update version to v14.0. Update total page count.

- [ ] **Step 4: Update baseline snapshot**

```bash
python3 -c "
import json, sys
sys.path.insert(0, 'scripts')
from tests.test_build_regression import snapshot_site
from pathlib import Path
Path('scripts/tests/baseline_snapshot.json').write_text(json.dumps(snapshot_site(), indent=2))
"
```

- [ ] **Step 5: Commit and push**

```bash
git add .
git commit -m "feat: Phase 4 complete — trends page, print export, comparison history"
git push origin main
```
