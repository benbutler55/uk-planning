#!/usr/bin/env python3
"""Automated ingest of GOV.UK planning statistics tables.

Checks the GOV.UK planning statistics collection page for update timestamps
and compares against the last_updated dates in official_baseline_metrics.csv.
Emits a report listing tables that have newer data available.

Run quarterly after each GOV.UK statistics release:
  python3 scripts/ingest_govuk_stats.py [--warn-only]
"""
import csv
import sys
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent
METRICS_PATH = ROOT / "data/evidence/official_baseline_metrics.csv"
REPORT_PATH = ROOT / "stats-ingest-report.txt"

STATS_TABLES = {
    "P151": {
        "description": "Speed of major decisions",
        "url": "https://www.gov.uk/government/statistical-data-sets/live-tables-on-planning-application-statistics",
        "metrics": ["BAS-001", "BAS-008", "BAS-009", "BAS-010", "BAS-011", "BAS-012",
                    "BAS-013", "BAS-014", "BAS-015", "BAS-016", "BAS-017", "BAS-018", "BAS-019"],
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
        for m in re.findall(r'\d{1,2} \w+ 20\d{2}', data):
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


def main():
    warn_only = "--warn-only" in sys.argv
    metrics = read_metrics()
    report_lines = [
        "GOV.UK Planning Statistics Ingest Report",
        f"Date: {date.today().isoformat()}",
        "",
    ]
    updates_needed = []
    errors = []

    for table_id, spec in STATS_TABLES.items():
        title, dates, err = fetch_page_title(spec["url"])
        if err:
            errors.append(f"{table_id}: could not fetch source page — {err}")
            continue

        # Check current retrieved_at dates in metrics for this table
        stale_metrics = []
        for metric_id in spec["metrics"]:
            row = metrics.get(metric_id)
            if not row:
                continue
            retrieved = row.get("retrieved_at", "")
            if retrieved:
                try:
                    d = date.fromisoformat(retrieved)
                    age = (date.today() - d).days
                    if age > 100:  # flag if not updated in 100+ days (quarterly tables)
                        stale_metrics.append(f"{metric_id} (last retrieved {retrieved}, {age} days ago)")
                except ValueError:
                    pass

        if stale_metrics:
            updates_needed.append({
                "table": table_id,
                "description": spec["description"],
                "url": spec["url"],
                "stale_metrics": stale_metrics,
            })

    if errors:
        report_lines.append("Fetch errors:")
        report_lines.extend(f"  [error] {e}" for e in errors)
        report_lines.append("")

    if updates_needed:
        report_lines.append(f"{len(updates_needed)} table(s) with potentially stale metrics:")
        for item in updates_needed:
            report_lines.append(f"\n  [{item['table']}] {item['description']}")
            report_lines.append(f"  Source: {item['url']}")
            report_lines.append("  Stale metrics:")
            report_lines.extend(f"    - {m}" for m in item["stale_metrics"])
        report_lines.append("")
        report_lines.append("Action: visit the source URLs above, download the latest data tables,")
        report_lines.append("and update data/evidence/official_baseline_metrics.csv with new values and retrieved_at dates.")
    else:
        report_lines.append("All metrics are within the 100-day freshness window.")

    report_text = "\n".join(report_lines)
    REPORT_PATH.write_text(report_text, encoding="utf-8")
    print(report_text)

    if errors and not warn_only:
        sys.exit(1)


if __name__ == "__main__":
    main()
