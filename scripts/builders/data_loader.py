"""Data loading, scoring config, data-health checks, and onboarding status."""
import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from .config import ROOT, SITE, SCORING_PATH
from .metrics import cohort_for_pid, parse_iso_date


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_scoring():
    data = json.loads(SCORING_PATH.read_text(encoding="utf-8"))
    return data["scoring_model"]["dimensions"]


def compute_data_health():
    from .html_utils import badge  # lazy import to avoid circular dependency

    specs = [
        {
            "dataset": "Official baseline metrics",
            "path": ROOT / "data/evidence/official_baseline_metrics.csv",
            "date_field": "retrieved_at",
            "stale_after_days": 100,
            "critical_after_days": 140,
        },
        {
            "dataset": "LPA quarterly trends",
            "path": ROOT / "data/evidence/lpa-quarterly-trends.csv",
            "date_field": "retrieved_at",
            "stale_after_days": 100,
            "critical_after_days": 140,
        },
        {
            "dataset": "Recommendation evidence links",
            "path": ROOT / "data/evidence/recommendation_evidence_links.csv",
            "date_field": "retrieved_at",
            "stale_after_days": 100,
            "critical_after_days": 140,
        },
        {
            "dataset": "Appeal decision evidence",
            "path": ROOT / "data/evidence/appeal-decisions.csv",
            "date_field": "retrieved_at",
            "stale_after_days": 120,
            "critical_after_days": 180,
        },
        {
            "dataset": "LPA issue incidence",
            "path": ROOT / "data/issues/lpa-issue-incidence.csv",
            "date_field": "last_reviewed",
            "stale_after_days": 45,
            "critical_after_days": 75,
        },
    ]

    rows = []
    for spec in specs:
        data = read_csv(spec["path"])
        values = [parse_iso_date(r.get(spec["date_field"], "")) for r in data]
        valid_dates = [d for d in values if d is not None]
        most_recent = max(valid_dates) if valid_dates else None
        age_days = (date.today() - most_recent).days if most_recent else 9999
        if age_days > spec["critical_after_days"]:
            status = "critical"
            css = "red"
        elif age_days > spec["stale_after_days"]:
            status = "stale"
            css = "amber"
        else:
            status = "fresh"
            css = "green"
        rows.append({
            "dataset": spec["dataset"],
            "row_count": len(data),
            "last_updated": most_recent.isoformat() if most_recent else "n/a",
            "age_days": age_days if most_recent else "n/a",
            "status": status,
            "status_badge": badge(status, css),
            "source_path": str(spec["path"].relative_to(ROOT)),
        })

    counts = defaultdict(int)
    for row in rows:
        counts[row["status"]] += 1
    return rows, dict(counts)


def compute_onboarding_status_rows(profile_page_check=True):
    lpas = read_csv(ROOT / "data/plans/pilot-lpas.csv")
    docs = read_csv(ROOT / "data/plans/pilot-plan-documents.csv")
    quality_rows = read_csv(ROOT / "data/plans/lpa-data-quality.csv")
    issue_rows = read_csv(ROOT / "data/issues/lpa-issue-incidence.csv")
    trend_rows = read_csv(ROOT / "data/evidence/lpa-quarterly-trends.csv")

    docs_by_id = defaultdict(list)
    for row in docs:
        docs_by_id[row.get("pilot_id", "")].append(row)
    trends_by_id = defaultdict(list)
    for row in trend_rows:
        trends_by_id[row.get("pilot_id", "")].append(row)
    quality_by_id = {row.get("pilot_id", ""): row for row in quality_rows}
    issues_by_id = {row.get("pilot_id", ""): row for row in issue_rows}

    rows = []
    counts = defaultdict(int)
    for lpa in lpas:
        pid = lpa.get("pilot_id", "")
        profile_page = SITE / f"plans-{pid.lower()}.html"
        checks = {
            "ingest": bool(lpa.get("lpa_name")),
            "validate": bool(quality_by_id.get(pid)) and bool(trends_by_id.get(pid)),
            "profile": (profile_page.exists() if profile_page_check else True),
            "qa": bool(issues_by_id.get(pid)) and bool(docs_by_id.get(pid)),
        }
        passed = sum(1 for value in checks.values() if value)
        quality_tier = quality_by_id.get(pid, {}).get("data_quality_tier", "")
        if passed == 4 and quality_tier in {"A", "B"}:
            coverage = "complete"
        elif passed >= 2:
            coverage = "partial"
        else:
            coverage = "estimated"
        counts[coverage] += 1
        failed = [name for name, ok in checks.items() if not ok]
        rows.append({
            "pilot_id": pid,
            "lpa_name": lpa.get("lpa_name", ""),
            "region": lpa.get("region", ""),
            "lpa_type": lpa.get("lpa_type", ""),
            "cohort": cohort_for_pid(pid),
            "quality_tier": quality_tier or "n/a",
            "coverage_status": coverage,
            "checks": checks,
            "failed_checks": failed,
            "documents_count": len(docs_by_id.get(pid, [])),
            "trend_points": len(trends_by_id.get(pid, [])),
            "issue_rows": 1 if pid in issues_by_id else 0,
            "profile_page": f"plans-{pid.lower()}.html",
        })
    return rows, dict(counts)
