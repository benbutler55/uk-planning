#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import build_site


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "site/reports/onboarding"


def gate_summary(row):
    checks = row.get("checks", {})
    return {
        "ingest": bool(checks.get("ingest")),
        "validate": bool(checks.get("validate")),
        "profile": bool(checks.get("profile")),
        "qa": bool(checks.get("qa")),
    }


def write_reports(rows):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    summary = []
    for row in rows:
        payload = {
            "generated_at": generated,
            "pilot_id": row["pilot_id"],
            "lpa_name": row["lpa_name"],
            "coverage_status": row["coverage_status"],
            "quality_tier": row["quality_tier"],
            "cohort": row["cohort"],
            "region": row["region"],
            "gate_status": gate_summary(row),
            "failed_checks": row["failed_checks"],
            "documents_count": row["documents_count"],
            "trend_points": row["trend_points"],
            "profile_page": row["profile_page"],
            "pipeline": ["ingest", "validate", "profile", "qa"],
        }
        path = OUT_DIR / f"{row['pilot_id'].lower()}-onboarding.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        summary.append(payload)

    (OUT_DIR / "onboarding-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Run council onboarding gate checks")
    parser.add_argument("--pilot-id", help="Specific pilot ID to check (e.g. LPA-01)")
    parser.add_argument("--all", action="store_true", help="Check all authorities")
    args = parser.parse_args()

    rows, counts = build_site.compute_onboarding_status_rows(profile_page_check=True)
    target_rows = rows
    if args.pilot_id:
        pid = args.pilot_id.upper().strip()
        target_rows = [row for row in rows if row["pilot_id"] == pid]
        if not target_rows:
            raise SystemExit(f"No authority found for {pid}")
    elif not args.all:
        target_rows = rows[:1]

    summary = write_reports(target_rows)
    print(f"Onboarding checks written: {len(summary)} authority report(s)")
    print(f"Coverage status totals (all authorities): complete={counts.get('complete', 0)}, partial={counts.get('partial', 0)}, estimated={counts.get('estimated', 0)}")


if __name__ == "__main__":
    main()
