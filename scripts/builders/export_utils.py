"""Export utilities: CSV/JSON exports, manifest generation, UX KPI report."""
import csv
import hashlib
import json
from datetime import date, datetime

from .config import ROOT, SITE, EXPORTS, BUILD_VERSION
from .data_loader import read_csv, compute_onboarding_status_rows


def write_exports(datasets):
    EXPORTS.mkdir(parents=True, exist_ok=True)
    for name, rows in datasets.items():
        # CSV
        if rows:
            csv_path = EXPORTS / f"{name}.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=rows[0].keys())
                w.writeheader()
                w.writerows(rows)
            # JSON
            json_path = EXPORTS / f"{name}.json"
            json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


def write_exports_manifest(datasets):
    EXPORTS.mkdir(parents=True, exist_ok=True)
    latest = None
    for rows in datasets.values():
        for row in rows:
            for value in row.values():
                if not value:
                    continue
                candidate = None
                try:
                    candidate = date.fromisoformat(str(value)[:10])
                except ValueError:
                    candidate = None
                if candidate and (latest is None or candidate > latest):
                    latest = candidate
    if latest is None:
        latest = date.today()
    generated = datetime(latest.year, latest.month, latest.day, 0, 0, 0).isoformat() + "Z"
    items = []
    for name, rows in datasets.items():
        encoded = json.dumps(rows, sort_keys=True, ensure_ascii=False).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
        fields = list(rows[0].keys()) if rows else []
        items.append({
            "dataset": name,
            "row_count": len(rows),
            "fields": fields,
            "content_sha256": digest,
            "csv_path": f"exports/{name}.csv",
            "json_path": f"exports/{name}.json",
        })
    manifest = {
        "version": BUILD_VERSION,
        "generated_at": generated,
        "dataset_count": len(items),
        "datasets": sorted(items, key=lambda x: x["dataset"]),
    }
    (EXPORTS / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


# --- Page builders ---


def build_ux_kpi_report():
    contradictions = read_csv(ROOT / "data/issues/contradiction-register.csv")
    recommendations = read_csv(ROOT / "data/issues/recommendations.csv")
    coverage_rows, coverage_counts = compute_onboarding_status_rows(profile_page_check=True)
    report = {
        "generated_at": date.today().isoformat(),
        "kpis": {
            "detail_page_coverage": {
                "contradictions_with_detail_pages": len(contradictions),
                "recommendations_with_detail_pages": len(recommendations),
            },
            "coverage_status": coverage_counts,
            "instrumentation": {
                "event_schema": ["page_view", "link_click"],
                "storage": "localStorage:uk-planning-ux-events-v1",
                "guided_mode_available": True,
                "plain_language_toggle_available": True,
            },
            "targets": {
                "time_to_first_insight_seconds": 45,
                "detail_page_click_through_rate": 0.35,
                "filter_use_success_rate": 0.8,
            },
        },
    }
    reports_dir = SITE / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "ux-kpi-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with (reports_dir / "ux-kpi-report.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        w.writerow(["contradiction_detail_pages", len(contradictions)])
        w.writerow(["recommendation_detail_pages", len(recommendations)])
        w.writerow(["coverage_complete", coverage_counts.get("complete", 0)])
        w.writerow(["coverage_partial", coverage_counts.get("partial", 0)])
        w.writerow(["coverage_estimated", coverage_counts.get("estimated", 0)])
