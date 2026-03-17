#!/usr/bin/env python3
"""Check source URL freshness and data staleness. Warning-only by default."""
import csv
import sys
import urllib.request
import urllib.error
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT_PATH = ROOT / "freshness-report.txt"
STALE_DAYS = 90  # warn if last_updated older than this


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check_url(url, timeout=15):
    """HEAD request to verify URL is reachable. Returns (status_code, error_msg)."""
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "uk-planning-freshness-checker/1.0")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, None
    except urllib.error.HTTPError as e:
        return e.code, str(e)
    except Exception as e:
        return None, str(e)


def check_staleness(rows, date_col, label):
    warnings = []
    cutoff = date.today() - timedelta(days=STALE_DAYS)
    for idx, row in enumerate(rows, start=2):
        val = (row.get(date_col, "") or "").strip()
        if not val:
            continue
        try:
            d = date.fromisoformat(val)
            if d < cutoff:
                warnings.append(f"{label}:{idx} stale {date_col}={val} (>{STALE_DAYS} days old)")
        except ValueError:
            pass
    return warnings


def check_urls_in_rows(rows, url_col, label):
    warnings = []
    seen = set()
    for idx, row in enumerate(rows, start=2):
        url = (row.get(url_col, "") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        status, err = check_url(url)
        if status is None:
            warnings.append(f"{label}:{idx} URL unreachable: {url} ({err})")
        elif status == 403:
            # 403 may indicate server-level bot-blocking rather than a missing page
            warnings.append(f"{label}:{idx} URL returned 403 (access blocked - verify manually): {url}")
        elif status >= 400:
            warnings.append(f"{label}:{idx} URL returned {status}: {url}")
    return warnings


def main():
    warn_only = "--warn-only" in sys.argv
    all_warnings = []

    datasets = [
        # (path, date_col_for_staleness, url_col, check_staleness_flag)
        ("data/legislation/england-core-legislation.csv", "last_updated", "source_url", True),
        ("data/policy/england-national-policy.csv", "last_updated", "source_url", True),
        # plan adoption dates are intentionally historical — skip staleness, check URLs only
        ("data/plans/pilot-plan-documents.csv", "adoption_or_publication_date", "source_url", False),
        ("data/evidence/recommendation_evidence_links.csv", "retrieved_at", "source_url", True),
        ("data/evidence/official_baseline_metrics.csv", "retrieved_at", "source_url", True),
    ]

    for path_str, date_col, url_col, check_stale in datasets:
        path = ROOT / path_str
        if not path.exists():
            all_warnings.append(f"Missing dataset: {path_str}")
            continue
        rows = read_csv(path)
        if check_stale:
            all_warnings.extend(check_staleness(rows, date_col, path_str))
        all_warnings.extend(check_urls_in_rows(rows, url_col, path_str))

    # Write report
    report_lines = ["Freshness Check Report", f"Date: {date.today().isoformat()}", ""]
    if all_warnings:
        report_lines.append(f"{len(all_warnings)} warning(s):")
        report_lines.extend(f"  [warn] {w}" for w in all_warnings)
    else:
        report_lines.append("No freshness warnings.")
    report_text = "\n".join(report_lines)
    REPORT_PATH.write_text(report_text, encoding="utf-8")
    print(report_text)

    if all_warnings and not warn_only:
        sys.exit(1)


if __name__ == "__main__":
    main()
