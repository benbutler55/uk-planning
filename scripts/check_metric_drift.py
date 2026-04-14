#!/usr/bin/env python3
import argparse
import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TRENDS_PATH = ROOT / "data/evidence/lpa-quarterly-trends.csv"
TXT_REPORT = ROOT / "metric-drift-report.txt"
JSON_REPORT = ROOT / "metric-drift-report.json"


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    parser = argparse.ArgumentParser(
        description="Check quarter-on-quarter metric drift"
    )
    parser.add_argument("--max-speed-delta", type=float, default=8.0)
    parser.add_argument("--max-appeal-delta", type=float, default=1.0)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    rows = read_rows(TRENDS_PATH)
    by_lpa = {}
    for row in rows:
        by_lpa.setdefault(row["pilot_id"], []).append(row)
    for pid in by_lpa:
        by_lpa[pid].sort(key=lambda r: r["quarter"])

    flags = []
    for pid, items in sorted(by_lpa.items()):
        if len(items) < 2:
            continue
        prev = items[-2]
        curr = items[-1]
        speed_delta = float(curr["major_in_time_pct"]) - float(
            prev["major_in_time_pct"]
        )
        appeal_delta = float(curr["appeals_overturned_pct"]) - float(
            prev["appeals_overturned_pct"]
        )
        if (
            abs(speed_delta) > args.max_speed_delta
            or abs(appeal_delta) > args.max_appeal_delta
        ):
            flags.append(
                {
                    "pilot_id": pid,
                    "lpa_name": curr["lpa_name"],
                    "previous_quarter": prev["quarter"],
                    "latest_quarter": curr["quarter"],
                    "speed_delta": round(speed_delta, 2),
                    "appeal_delta": round(appeal_delta, 2),
                }
            )

    lines = [
        "Quarterly Metric Drift Report",
        f"Checked LPAs: {len(by_lpa)}",
        f"Flagged LPAs: {len(flags)}",
        f"Thresholds: speed>{args.max_speed_delta} pp, appeal>{args.max_appeal_delta} pp",
        "",
    ]
    for f in flags:
        lines.append(
            f"- {f['pilot_id']} {f['lpa_name']} ({f['previous_quarter']} -> {f['latest_quarter']}): "
            f"speed {f['speed_delta']:+.2f} pp, appeal {f['appeal_delta']:+.2f} pp"
        )
    if not flags:
        lines.append("No drift thresholds exceeded.")

    TXT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    JSON_REPORT.write_text(
        json.dumps(
            {
                "flagged_count": len(flags),
                "checked_lpas": len(by_lpa),
                "thresholds": {
                    "max_speed_delta": args.max_speed_delta,
                    "max_appeal_delta": args.max_appeal_delta,
                },
                "flags": flags,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\n".join(lines))
    if flags and not args.warn_only:
        sys.exit(1)


if __name__ == "__main__":
    main()
