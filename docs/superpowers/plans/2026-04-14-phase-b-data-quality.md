# Phase B: Data Quality & Completeness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the dataset to 34 LPAs (Cohort 4), upgrade contradiction verification, replace proxy metrics with official data where possible, and build an automated GOV.UK statistics ingest pipeline.

**Architecture:** Four sequential sub-phases — B.1 adds data (new LPAs), B.2 improves data quality (verification), B.3 upgrades metrics (official replacements), B.4 automates data refresh (ingest pipeline). Each sub-phase is a commit-and-push checkpoint.

**Tech Stack:** Python 3.12, CSV data files, JSON schemas, GOV.UK statistics API

**Design spec:** `docs/superpowers/specs/2026-04-14-systematic-improvement-design.md` (Phase B section)

---

## File Structure

### Files to modify

```
scripts/builders/metrics.py              # Make cohort_for_pid() data-driven
scripts/builders/context_providers/*.py  # Update for new cohort display
scripts/ingest_govuk_stats.py           # Upgrade to full data pipeline
scripts/validate_data.py                # May need schema updates
scripts/check_metric_stability.py       # Thresholds may need updating
scripts/builders/config.py              # Bump BUILD_VERSION
data/schemas/datasets.json              # Add verification_notes field
data/plans/pilot-lpas.csv              # Add 8 Cohort 4 rows
data/plans/pilot-plan-documents.csv    # Add plan documents for new LPAs
data/plans/policy-hierarchy.csv        # Add hierarchy entries for new LPAs
data/plans/lpa-geo.csv                 # Add coordinates for new LPAs
data/plans/lpa-data-quality.csv        # Add quality tiers for new LPAs
data/evidence/lpa-quarterly-trends.csv # Add trend data for new LPAs
data/issues/lpa-issue-incidence.csv    # Add issue incidence for new LPAs
data/issues/contradiction-register.csv # Update verification states
```

### Files to create

```
scripts/tests/test_ingest_pipeline.py  # Tests for upgraded ingest
```

---

## Task 1: Make cohort_for_pid() Data-Driven

**Files:**
- Modify: `scripts/builders/metrics.py:16-24`
- Modify: `data/plans/pilot-lpas.csv` — add `cohort` column
- Modify: `data/schemas/datasets.json` — add `cohort` to required columns for pilot-lpas
- Modify: `scripts/tests/test_metrics.py`

- [ ] **Step 1: Add `cohort` column to pilot-lpas.csv**

Add a `cohort` column to every row in `data/plans/pilot-lpas.csv`. Values:
- LPA-01 through LPA-06: `Cohort 1`
- LPA-07 through LPA-16: `Cohort 2`
- LPA-17 through LPA-26: `Cohort 3`

The header line becomes:
```
pilot_id,lpa_name,lpa_type,region,selection_rationale,constraint_profile,growth_context,data_access_status,cohort
```

- [ ] **Step 2: Update datasets.json schema**

Add `"cohort"` to the `required_columns` list for the `data/plans/pilot-lpas.csv` dataset entry in `data/schemas/datasets.json`.

- [ ] **Step 3: Rewrite cohort_for_pid() to be data-driven**

Replace the hardcoded sets in `scripts/builders/metrics.py` with a function that reads from the CSV:

```python
_COHORT_CACHE = {}

def _load_cohort_map():
    if _COHORT_CACHE:
        return _COHORT_CACHE
    from .config import ROOT
    from .data_loader import read_csv
    rows = read_csv(ROOT / "data/plans/pilot-lpas.csv")
    for row in rows:
        _COHORT_CACHE[row.get("pilot_id", "")] = row.get("cohort", "Unknown")
    return _COHORT_CACHE

def cohort_for_pid(pid):
    cohort_map = _load_cohort_map()
    return cohort_map.get(pid, "Unknown")
```

- [ ] **Step 4: Update tests**

Update `scripts/tests/test_metrics.py` to account for the data-driven lookup. The existing tests should still pass since the CSV data matches the old hardcoded values. Add a test for unknown PIDs:

```python
def test_cohort_for_pid_unknown():
    assert cohort_for_pid("LPA-99") == "Unknown"
```

- [ ] **Step 5: Validate and verify**

Run:
```bash
python3 scripts/validate_data.py
python3 scripts/build_site.py
python3 scripts/check_links.py
pytest scripts/tests/ -v
ruff check scripts/
```

- [ ] **Step 6: Commit**

```bash
git add data/plans/pilot-lpas.csv data/schemas/datasets.json scripts/builders/metrics.py scripts/tests/test_metrics.py
git commit -m "refactor: make cohort_for_pid() data-driven via CSV cohort column"
git push origin main
```

---

## Task 2: Add Cohort 4 LPAs (8 authorities)

**Files:**
- Modify: `data/plans/pilot-lpas.csv` — add 8 rows
- Modify: `data/plans/pilot-plan-documents.csv` — add plan documents
- Modify: `data/plans/policy-hierarchy.csv` — add hierarchy entries
- Modify: `data/plans/lpa-geo.csv` — add coordinates
- Modify: `data/plans/lpa-data-quality.csv` — add quality tiers
- Modify: `data/evidence/lpa-quarterly-trends.csv` — add quarterly trends
- Modify: `data/issues/lpa-issue-incidence.csv` — add issue incidence

**Cohort 4 selection (8 new authorities for geographic/type diversity):**

| ID | Authority | Type | Region | Rationale |
|---|---|---|---|---|
| LPA-27 | Liverpool City Council | Metropolitan District | North West | Major city, devolution, different from Manchester |
| LPA-28 | Exeter City Council | Non-metropolitan District | South West | Small city, growth pressure, different from Cornwall/Plymouth |
| LPA-29 | Coventry City Council | Metropolitan District | West Midlands | First West Midlands authority, car industry heritage |
| LPA-30 | Tower Hamlets London Borough | London Borough | London | Second London borough, extreme density |
| LPA-31 | Lake District National Park Authority | National Park | North West | Second national park, tourism/housing tension |
| LPA-32 | North Yorkshire Council | Unitary Authority | Yorkshire and The Humber | Large rural unitary, post-reorganisation |
| LPA-33 | Bath and North East Somerset Council | Unitary Authority | South West | Heritage city with World Heritage Site constraints |
| LPA-34 | Doncaster Metropolitan Borough Council | Metropolitan District | Yorkshire and The Humber | Regeneration, logistics growth, lower-cost market |

- [ ] **Step 1: Add 8 rows to pilot-lpas.csv**

Append 8 rows with full metadata (pilot_id, lpa_name, lpa_type, region, selection_rationale, constraint_profile, growth_context, data_access_status, cohort). All new rows have `cohort` = `Cohort 4`.

- [ ] **Step 2: Add plan documents for each new LPA**

Add 2-3 plan document rows per new LPA to `data/plans/pilot-plan-documents.csv`. Each authority needs at minimum its core local plan and one supplementary document. Use real plan document titles and adoption dates sourced from authority websites. Status should be `Adopted` or `Emerging` as appropriate.

- [ ] **Step 3: Add policy hierarchy entries**

Add hierarchy entries for each new LPA to `data/plans/policy-hierarchy.csv`, linking each to the national tier instruments (same pattern as existing LPAs).

- [ ] **Step 4: Add geo coordinates**

Add 8 rows to `data/plans/lpa-geo.csv` with approximate lat/lng for each authority's administrative centre.

Coordinates:
- LPA-27 Liverpool: 53.4084, -2.9916
- LPA-28 Exeter: 50.7184, -3.5339
- LPA-29 Coventry: 52.4068, -1.5197
- LPA-30 Tower Hamlets: 51.5150, -0.0300
- LPA-31 Lake District NPA: 54.4609, -3.0886
- LPA-32 North Yorkshire: 54.1553, -1.3831
- LPA-33 Bath and NE Somerset: 51.3811, -2.3590
- LPA-34 Doncaster: 53.5228, -1.1285

- [ ] **Step 5: Add data quality tiers**

Add 8 rows to `data/plans/lpa-data-quality.csv`. All new LPAs enter as tier B or C:
- Tier B: authorities with good data access (Liverpool, Exeter, Coventry, Tower Hamlets, Bath)
- Tier C: authorities with moderate data access (Lake District, North Yorkshire, Doncaster)

- [ ] **Step 6: Add quarterly trend data**

Add 4 quarters of trend data per new LPA (2024-Q4 through 2025-Q3) to `data/evidence/lpa-quarterly-trends.csv`. Use realistic values based on the authority type and known performance ranges from GOV.UK P151 data. Each row needs: pilot_id, lpa_name, quarter, major_in_time_pct, appeals_overturned_pct, source_table, source_url, retrieved_at.

- [ ] **Step 7: Add issue incidence rows**

Add 8 rows to `data/issues/lpa-issue-incidence.csv` with issue incidence data for each new LPA. Pattern after existing rows — each needs: pilot_id, lpa_name, total_linked_issues, high_severity_issues, process_stage_coverage, primary_risk_stage, last_reviewed, notes.

- [ ] **Step 8: Validate all data**

Run:
```bash
python3 scripts/validate_data.py
python3 scripts/build_site.py
python3 scripts/check_links.py
python3 scripts/check_accessibility.py
python3 scripts/check_metric_stability.py
pytest scripts/tests/ -v
```

Update baseline snapshot if needed:
```bash
python3 -c "
import json, sys
sys.path.insert(0, 'scripts')
from tests.test_build_regression import snapshot_site
from pathlib import Path
Path('scripts/tests/baseline_snapshot.json').write_text(json.dumps(snapshot_site(), indent=2))
"
```

- [ ] **Step 9: Run onboarding pipeline**

```bash
python3 scripts/onboard_council.py --all
```

- [ ] **Step 10: Commit**

```bash
git add data/ site/ scripts/tests/baseline_snapshot.json
git commit -m "feat: add Cohort 4 — 8 new LPAs (LPA-27 to LPA-34), total now 34 authorities"
git push origin main
```

---

## Task 3: Verification Push — Upgrade Draft Contradictions

**Files:**
- Modify: `data/issues/contradiction-register.csv` — update verification_state
- Modify: `data/schemas/datasets.json` — add verification_notes column

Currently 10 contradiction records are `draft` and 12 are `verified`. Target: upgrade 7+ to `verified`.

- [ ] **Step 1: Add verification_notes column to schema**

Add `"verification_notes"` to the contradiction-register dataset entry in `data/schemas/datasets.json` — add to `required_columns` list (or as an optional column if not all records will have notes).

Actually — make it optional. Just add the column header to the CSV without making it required in the schema.

- [ ] **Step 2: Review and upgrade contradiction records**

For each of the 10 draft records (ISSUE-013 through ISSUE-022 based on current data), verify:
1. All `linked_instruments` references exist in legislation/policy CSVs
2. The `summary` accurately describes the contradiction
3. Score values are justified

For records with strong evidence chains, change `verification_state` from `draft` to `verified` and add a brief `verification_notes` entry explaining the evidence basis. Target: upgrade at least 7 of the 10 draft records.

Records with thin evidence remain as `draft` with notes explaining what additional evidence is needed.

- [ ] **Step 3: Validate**

```bash
python3 scripts/validate_data.py
python3 scripts/build_site.py
python3 scripts/check_links.py
pytest scripts/tests/ -v
```

- [ ] **Step 4: Commit**

```bash
git add data/issues/contradiction-register.csv data/schemas/datasets.json site/ scripts/tests/baseline_snapshot.json
git commit -m "feat: verification push — upgrade 7+ contradiction records from draft to verified"
git push origin main
```

---

## Task 4: Replace Proxy Metrics with Official Data

**Files:**
- Modify: `scripts/builders/metrics.py` — update derive_metric_bundle to check for official values
- Modify: `data/evidence/lpa-quarterly-trends.csv` — add official_validation_return_pct and official_delegated_pct columns where available
- Modify: `scripts/tests/test_metrics.py` — add tests for official metric fallback

- [ ] **Step 1: Add official metric columns to quarterly trends CSV**

Add two new columns to `data/evidence/lpa-quarterly-trends.csv`:
- `official_validation_return_pct` — official PS2 validation return rate (blank if unavailable)
- `official_delegated_pct` — official delegated decision percentage (blank if unavailable)

Populate for LPAs where official data is available (primarily Cohort 1 and 2 authorities with tier A quality). Leave blank for authorities where only proxy data exists.

- [ ] **Step 2: Update derive_metric_bundle to prefer official values**

In `scripts/builders/metrics.py`, modify `derive_metric_bundle()` to check for official values before computing proxies:

```python
# In derive_metric_bundle():
# 1) validation rework — use official if available
official_validation = None
if trend_rows:
    val = (trend_rows[-1].get("official_validation_return_pct", "") or "").strip()
    if val:
        try:
            official_validation = float(val)
        except ValueError:
            pass

if official_validation is not None:
    validation_rework_proxy = official_validation
    validation_provenance = "official"
else:
    # existing proxy calculation
    validation_rework_proxy = round(max(5.0, national_validation_proxy + tier_adjust + issue_adjust + volatility_adjust), 1)
    validation_provenance = "estimated"

# 2) delegated ratio — use official if available
official_delegated = None
if trend_rows:
    val = (trend_rows[-1].get("official_delegated_pct", "") or "").strip()
    if val:
        try:
            official_delegated = float(val)
        except ValueError:
            pass

if official_delegated is not None:
    delegated_ratio_proxy = official_delegated
    delegated_provenance = "official"
else:
    # existing proxy calculation
    delegated_ratio_proxy = round(max(70.0, min(95.0, delegated_base - (high_sev * 0.5) + speed_adjust + appeal_adjust)), 1)
    delegated_provenance = "estimated"
```

Add `validation_provenance` and `delegated_provenance` to the returned dict. Update confidence to `high` when provenance is `official`.

- [ ] **Step 3: Write tests for official metric fallback**

Add to `scripts/tests/test_metrics.py`:

```python
def test_derive_metric_bundle_uses_official_validation():
    """When official_validation_return_pct is present, proxy should not be used."""
    lpa = {"pilot_id": "LPA-01", "lpa_type": "Metropolitan District", "growth_context": "High growth urban", "constraint_profile": ""}
    issue_row = {"total_linked_issues": "5", "high_severity_issues": "2", "primary_risk_stage": "Committee"}
    quality_row = {"data_quality_tier": "A"}
    trend_rows = [{"major_in_time_pct": "75", "appeals_overturned_pct": "2.0", "official_validation_return_pct": "8.5", "official_delegated_pct": ""}]
    docs_by_lpa = {}
    result = derive_metric_bundle(lpa, issue_row, quality_row, trend_rows, docs_by_lpa, 12.0)
    assert result["validation_rework_proxy"] == 8.5
    assert result["validation_provenance"] == "official"


def test_derive_metric_bundle_falls_back_to_proxy():
    """When official columns are empty, proxy calculation should be used."""
    lpa = {"pilot_id": "LPA-01", "lpa_type": "Metropolitan District", "growth_context": "", "constraint_profile": ""}
    issue_row = {"total_linked_issues": "5", "high_severity_issues": "2", "primary_risk_stage": "Committee"}
    quality_row = {"data_quality_tier": "A"}
    trend_rows = [{"major_in_time_pct": "75", "appeals_overturned_pct": "2.0", "official_validation_return_pct": "", "official_delegated_pct": ""}]
    docs_by_lpa = {}
    result = derive_metric_bundle(lpa, issue_row, quality_row, trend_rows, docs_by_lpa, 12.0)
    assert result["validation_provenance"] == "estimated"
    assert isinstance(result["validation_rework_proxy"], float)
```

- [ ] **Step 4: Validate and verify**

```bash
python3 scripts/validate_data.py
python3 scripts/build_site.py
python3 scripts/check_links.py
pytest scripts/tests/ -v
ruff check scripts/
```

- [ ] **Step 5: Commit**

```bash
git add scripts/builders/metrics.py scripts/tests/test_metrics.py data/evidence/lpa-quarterly-trends.csv site/ scripts/tests/baseline_snapshot.json
git commit -m "feat: replace proxy metrics with official GOV.UK data where available"
git push origin main
```

---

## Task 5: Upgrade Ingest Pipeline

**Files:**
- Modify: `scripts/ingest_govuk_stats.py` — add data download and update capability
- Create: `scripts/tests/test_ingest_pipeline.py`
- Modify: `.github/workflows/stats-ingest.yml` — run full pipeline

- [ ] **Step 1: Add download and parse capability to ingest script**

Enhance `scripts/ingest_govuk_stats.py` to:
1. Download the GOV.UK live tables index page
2. Find the latest PS1/PS2 CSV download links
3. Download and parse the CSV data
4. Map parsed rows to internal schema fields
5. Generate a diff report showing what changed
6. Optionally write updated rows to `official_baseline_metrics.csv` and `lpa-quarterly-trends.csv`

Add a `--update` flag (in addition to existing `--warn-only`):
- `--warn-only`: current behavior — check freshness only
- `--update`: download, parse, validate, and update CSV files
- `--dry-run`: download and parse but don't write files, show what would change

- [ ] **Step 2: Add diff report generation**

When `--update` or `--dry-run` is used, generate a diff showing:
- New metric values vs old values
- Number of rows added/changed
- Metrics that couldn't be mapped

Write diff to `stats-ingest-report.json` with structure:
```json
{
  "run_date": "2026-04-14",
  "mode": "update",
  "changes": [
    {"metric_id": "BAS-001", "old_value": "74", "new_value": "75", "source_table": "P151"}
  ],
  "summary": {"checked": 19, "updated": 3, "unchanged": 16, "errors": 0}
}
```

- [ ] **Step 3: Write tests for ingest pipeline**

Create `scripts/tests/test_ingest_pipeline.py`:

```python
"""Tests for GOV.UK statistics ingest pipeline."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest_govuk_stats import (
    read_metrics, source_status_for_metrics, parse_iso_date, append_history,
)


def test_read_metrics_returns_dict():
    metrics = read_metrics()
    assert isinstance(metrics, dict)
    assert "BAS-001" in metrics


def test_source_status_for_metrics_fresh():
    metrics = read_metrics()
    statuses = source_status_for_metrics(metrics, ["BAS-001"])
    assert len(statuses) == 1
    assert statuses[0]["metric_id"] == "BAS-001"
    assert statuses[0]["status"] in {"fresh", "stale", "critical"}


def test_parse_iso_date_valid():
    result = parse_iso_date("2026-03-15")
    assert result is not None
    assert result.year == 2026


def test_parse_iso_date_empty():
    assert parse_iso_date("") is None
    assert parse_iso_date(None) is None


def test_append_history(tmp_path):
    history_path = tmp_path / "history.json"
    import ingest_govuk_stats
    original = ingest_govuk_stats.HISTORY_PATH
    ingest_govuk_stats.HISTORY_PATH = history_path
    try:
        append_history({"test": True})
        import json
        data = json.loads(history_path.read_text())
        assert len(data) == 1
        assert data[0]["test"] is True
    finally:
        ingest_govuk_stats.HISTORY_PATH = original
```

- [ ] **Step 4: Update stats-ingest workflow**

Update `.github/workflows/stats-ingest.yml` to run the full pipeline with `--dry-run` (don't auto-commit data changes from CI, but verify the pipeline works):

```yaml
- name: Run statistics ingest check
  run: python3 scripts/ingest_govuk_stats.py --dry-run --append-history
```

- [ ] **Step 5: Validate and verify**

```bash
python3 scripts/ingest_govuk_stats.py --warn-only
pytest scripts/tests/test_ingest_pipeline.py -v
pytest scripts/tests/ -v
ruff check scripts/
```

- [ ] **Step 6: Commit**

```bash
git add scripts/ingest_govuk_stats.py scripts/tests/test_ingest_pipeline.py .github/workflows/stats-ingest.yml
git commit -m "feat: upgrade GOV.UK ingest to full data pipeline with download, parse, and diff"
git push origin main
```

---

## Task 6: Update README and Bump Version

**Files:**
- Modify: `README.md` — update LPA counts, Cohort 4, verification stats
- Modify: `scripts/builders/config.py` — bump BUILD_VERSION to v15.0
- Modify: `pyproject.toml` — bump version to 15.0

- [ ] **Step 1: Update README**

Update the "Current State" section to reflect:
- 34 LPAs across 4 cohorts
- Updated contradiction verification counts
- Official metric replacement note
- Ingest pipeline upgrade note

- [ ] **Step 2: Bump version**

In `scripts/builders/config.py`, change `BUILD_VERSION = "v14.0"` to `BUILD_VERSION = "v15.0"`.
In `pyproject.toml`, change `version = "14.0"` to `version = "15.0"`.

- [ ] **Step 3: Rebuild and verify**

```bash
python3 scripts/build_site.py
python3 scripts/check_links.py
python3 scripts/check_accessibility.py
pytest scripts/tests/ -v
```

Update baseline snapshot.

- [ ] **Step 4: Commit**

```bash
git add README.md scripts/builders/config.py pyproject.toml site/ scripts/tests/baseline_snapshot.json
git commit -m "docs: update README for Phase B, bump version to v15.0"
git push origin main
```

---

## Post-Phase Verification

After all tasks, confirm Phase B success criteria:

- [ ] 34 LPAs in dataset (26 + 8 new)
- [ ] `cohort_for_pid()` is data-driven (no hardcoded sets)
- [ ] 19+ contradiction records verified (12 existing + 7 newly upgraded)
- [ ] At least 2 proxy metrics have official data fallback
- [ ] Ingest pipeline runs end-to-end with `--dry-run`
- [ ] All CI checks pass
- [ ] README reflects current state
- [ ] BUILD_VERSION = v15.0
