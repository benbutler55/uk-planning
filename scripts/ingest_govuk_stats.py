#!/usr/bin/env python3
"""Automated ingest of GOV.UK and PINS planning statistics sources.

Checks source pages for freshness and compares against local dataset retrieval dates.
Emits text and JSON reports, and can append run history for quarterly monitoring.

Run quarterly after each GOV.UK statistics release:
  python3 scripts/ingest_govuk_stats.py [--warn-only] [--append-history]
  python3 scripts/ingest_govuk_stats.py --update [--append-history]
  python3 scripts/ingest_govuk_stats.py --dry-run
"""

import csv
import json
import sys
import urllib.request
import urllib.error
from datetime import date, datetime, timezone
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent
METRICS_PATH = ROOT / "data/evidence/official_baseline_metrics.csv"
REPORT_PATH = ROOT / "stats-ingest-report.txt"
REPORT_JSON_PATH = ROOT / "stats-ingest-report.json"
HISTORY_PATH = ROOT / "stats-ingest-history.json"

STATS_TABLES = {
    "P151": {
        "description": "Speed of major decisions",
        "url": "https://www.gov.uk/government/statistical-data-sets/live-tables-on-planning-application-statistics",
        "metrics": [
            "BAS-001",
            "BAS-008",
            "BAS-009",
            "BAS-010",
            "BAS-011",
            "BAS-012",
            "BAS-013",
            "BAS-014",
            "BAS-015",
            "BAS-016",
            "BAS-017",
            "BAS-018",
            "BAS-019",
        ],
    },
    "P152": {
        "description": "Quality of major decisions (appeals overturned)",
        "url": "https://www.gov.uk/government/statistical-data-sets/live-tables-on-planning-application-statistics",
        "metrics": ["BAS-003"],
    },
    "P153": {
        "description": "Speed of non-major decisions",
        "url": "https://www.gov.uk/government/statistical-data-sets/live-tables-on-planning-application-statistics",
        "metrics": ["BAS-002"],
    },
    "P154": {
        "description": "Quality of non-major decisions",
        "url": "https://www.gov.uk/government/statistical-data-sets/live-tables-on-planning-application-statistics",
        "metrics": ["BAS-004"],
    },
    "PS2": {
        "description": "Applications received and decided (validation proxy)",
        "url": "https://www.gov.uk/government/statistical-data-sets/live-tables-on-planning-application-statistics",
        "metrics": ["BAS-007"],
    },
    "PINS_QUARTERLY": {
        "description": "PINS quarterly volume and speed statistics",
        "url": "https://www.gov.uk/government/organisations/planning-inspectorate/about/statistics",
        "metrics": ["BAS-005", "BAS-006"],
    },
}


class TitleDateParser(HTMLParser):
    """Extracts the page title and any date strings for basic freshness detection."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self._in_title = False
        self.dates_found = []

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data.strip()
        import re

        for m in re.findall(r"\d{1,2} \w+ 20\d{2}", data):
            self.dates_found.append(m)


def fetch_page_title(url, timeout=20):
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "uk-planning-stats-ingest/1.0")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read(32768).decode("utf-8", errors="replace")
            parser = TitleDateParser()
            parser.feed(content)
            return parser.title, parser.dates_found, None
    except Exception as e:
        return None, [], str(e)


def read_metrics():
    with METRICS_PATH.open(newline="", encoding="utf-8") as f:
        return {r["metric_id"]: r for r in csv.DictReader(f)}


def parse_iso_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def source_status_for_metrics(metrics, metric_ids):
    entries = []
    for metric_id in metric_ids:
        row = metrics.get(metric_id)
        if not row:
            entries.append({"metric_id": metric_id, "status": "missing"})
            continue
        retrieved = row.get("retrieved_at", "")
        retrieved_date = parse_iso_date(retrieved)
        age_days = (date.today() - retrieved_date).days if retrieved_date else None
        status = "fresh"
        if age_days is None:
            status = "unknown"
        elif age_days > 140:
            status = "critical"
        elif age_days > 100:
            status = "stale"
        entries.append(
            {
                "metric_id": metric_id,
                "status": status,
                "retrieved_at": retrieved,
                "age_days": age_days,
                "source_table": row.get("source_table", ""),
                "value": row.get("value", ""),
            }
        )
    return entries


def download_source_page(url, timeout=30):
    """Download a GOV.UK statistics page and return its content."""
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "uk-planning-stats-ingest/1.0")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace"), None
    except Exception as e:
        return None, str(e)


def parse_metrics_from_page(content, table_config):
    """Extract date information from a statistics page to detect updates.

    Returns a dict with detected publication dates and update signals.
    In a full implementation this would parse the actual CSV data tables.
    Currently detects freshness signals from page metadata.
    """
    parser = TitleDateParser()
    parser.feed(content)
    return {
        "title": parser.title,
        "dates_found": parser.dates_found,
        "has_update": len(parser.dates_found) > 0,
    }


def compute_diff(current_metrics, detected_updates):
    """Compare current metric retrieval dates against detected page updates.

    Returns a list of change records.
    """
    changes = []
    for table_id, config in STATS_TABLES.items():
        update_info = detected_updates.get(table_id, {})
        if not update_info.get("has_update"):
            continue
        for metric_id in config["metrics"]:
            current = current_metrics.get(metric_id, {})
            current_retrieved = current.get("retrieved_at", "")
            changes.append(
                {
                    "metric_id": metric_id,
                    "source_table": table_id,
                    "current_retrieved_at": current_retrieved,
                    "page_dates_detected": update_info.get("dates_found", []),
                    "action": "check_for_update",
                }
            )
    return changes


def write_diff_report(changes, mode):
    """Write a JSON diff report."""
    report = {
        "run_date": date.today().isoformat(),
        "mode": mode,
        "changes": changes,
        "summary": {
            "checked": len(changes),
            "flagged_for_update": sum(
                1 for c in changes if c["action"] == "check_for_update"
            ),
        },
    }
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def append_history(payload):
    history = []
    if HISTORY_PATH.exists():
        try:
            history = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            history = []
    history.append(payload)
    HISTORY_PATH.write_text(json.dumps(history[-24:], indent=2), encoding="utf-8")


def main():
    warn_only = "--warn-only" in sys.argv
    update_mode = "--update" in sys.argv
    dry_run = "--dry-run" in sys.argv
    append_hist = "--append-history" in sys.argv
    metrics = read_metrics()

    if update_mode or dry_run:
        # Download and check each source
        detected_updates = {}
        for table_id, config in STATS_TABLES.items():
            print(f"Checking {table_id}: {config['description']}...")
            content, error = download_source_page(config["url"])
            if error:
                print(f"  Error downloading {table_id}: {error}")
                continue
            parsed = parse_metrics_from_page(content, config)
            detected_updates[table_id] = parsed
            print(f"  Title: {parsed['title']}")
            print(
                f"  Dates found: {', '.join(parsed['dates_found']) if parsed['dates_found'] else 'none'}"
            )

        changes = compute_diff(metrics, detected_updates)
        mode_label = "dry-run" if dry_run else "update"
        report = write_diff_report(changes, mode_label)

        print(
            f"\n{mode_label.title()} report: {report['summary']['checked']} metrics checked, "
            f"{report['summary']['flagged_for_update']} flagged for update"
        )

        if dry_run:
            print("Dry run — no files modified.")
        elif update_mode:
            # In update mode, update retrieved_at dates for checked metrics
            # Full CSV download/parse would go here in a future enhancement
            print(
                "Update mode — source page checks completed. "
                "Full CSV parsing not yet implemented; use manual update for now."
            )

        if append_hist:
            append_history(
                {
                    "run_date": date.today().isoformat(),
                    "mode": mode_label,
                    "summary": report["summary"],
                }
            )
            print(f"Run history appended to {HISTORY_PATH}")

        return

    # Existing warn-only (or no flags) behaviour below.
    report_lines = [
        "GOV.UK / PINS Planning Statistics Ingest Report",
        f"Date: {date.today().isoformat()}",
        "",
    ]
    updates_needed = []
    errors = []
    source_checks = []

    for table_id, spec in STATS_TABLES.items():
        title, dates, err = fetch_page_title(spec["url"])
        if err:
            errors.append(f"{table_id}: could not fetch source page — {err}")
            continue

        metric_entries = source_status_for_metrics(metrics, spec["metrics"])
        stale_metrics = []
        for entry in metric_entries:
            if entry.get("status") in {"stale", "critical", "unknown", "missing"}:
                detail = entry.get("status")
                if entry.get("age_days") is not None:
                    detail += f", {entry['age_days']} days old"
                stale_metrics.append(f"{entry.get('metric_id')} ({detail})")

        source_checks.append(
            {
                "table": table_id,
                "description": spec["description"],
                "url": spec["url"],
                "page_title": title,
                "date_strings_found": dates[:10],
                "metric_entries": metric_entries,
            }
        )

        if stale_metrics:
            updates_needed.append(
                {
                    "table": table_id,
                    "description": spec["description"],
                    "url": spec["url"],
                    "stale_metrics": stale_metrics,
                }
            )

    if errors:
        report_lines.append("Fetch errors:")
        report_lines.extend(f"  [error] {e}" for e in errors)
        report_lines.append("")

    if updates_needed:
        report_lines.append(
            f"{len(updates_needed)} table(s) with potentially stale metrics:"
        )
        for item in updates_needed:
            report_lines.append(f"\n  [{item['table']}] {item['description']}")
            report_lines.append(f"  Source: {item['url']}")
            report_lines.append("  Stale metrics:")
            report_lines.extend(f"    - {m}" for m in item["stale_metrics"])
        report_lines.append("")
        report_lines.append(
            "Action: visit the source URLs above, download the latest data tables,"
        )
        report_lines.append(
            "and update data/evidence/official_baseline_metrics.csv with new values and retrieved_at dates."
        )
    else:
        report_lines.append("All metrics are within the 100-day freshness window.")

    report_text = "\n".join(report_lines)
    REPORT_PATH.write_text(report_text, encoding="utf-8")
    json_payload = {
        "generated_at": date.today().isoformat(),
        "generated_at_utc": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "stale_table_count": len(updates_needed),
        "error_count": len(errors),
        "stale_tables": updates_needed,
        "errors": errors,
        "source_checks": source_checks,
    }
    REPORT_JSON_PATH.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")
    if append_hist:
        append_history(
            {
                "generated_at": json_payload["generated_at_utc"],
                "stale_table_count": json_payload["stale_table_count"],
                "error_count": json_payload["error_count"],
                "tables_checked": len(source_checks),
            }
        )
    print(report_text)

    if errors and not warn_only:
        sys.exit(1)


if __name__ == "__main__":
    main()
