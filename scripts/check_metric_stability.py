#!/usr/bin/env python3
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from builders.data_loader import read_csv
from builders.metrics import derive_metric_bundle


ROOT = Path(__file__).resolve().parent.parent
TXT_REPORT = ROOT / "metric-stability-report.txt"
JSON_REPORT = ROOT / "metric-stability-report.json"


def to_float(value, fallback=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def read_inputs():
    lpas = read_csv(ROOT / "data/plans/pilot-lpas.csv")
    docs = read_csv(ROOT / "data/plans/pilot-plan-documents.csv")
    baselines = read_csv(ROOT / "data/evidence/official_baseline_metrics.csv")
    quality_rows = read_csv(ROOT / "data/plans/lpa-data-quality.csv")
    issue_rows = read_csv(ROOT / "data/issues/lpa-issue-incidence.csv")
    trend_rows = read_csv(ROOT / "data/evidence/lpa-quarterly-trends.csv")
    return lpas, docs, baselines, quality_rows, issue_rows, trend_rows


def build_metric_state(
    lpas, docs, baselines, quality_rows, issue_rows, trend_rows, quarter_index
):
    quality_by_id = {r["pilot_id"]: r for r in quality_rows}
    issues_by_id = {r["pilot_id"]: r for r in issue_rows}
    docs_by_lpa = defaultdict(list)
    for row in docs:
        docs_by_lpa[row["pilot_id"]].append(row)
    trends_by_id = defaultdict(list)
    for row in trend_rows:
        trends_by_id[row["pilot_id"]].append(row)
    for pid in trends_by_id:
        trends_by_id[pid].sort(key=lambda x: x.get("quarter", ""))

    national_validation_proxy = 12.0
    for b in baselines:
        if b.get("metric_id") == "BAS-007":
            national_validation_proxy = to_float(b.get("value"), 12.0)
            break

    state = {}
    for lpa in lpas:
        pid = lpa["pilot_id"]
        q = quality_by_id.get(pid, {})
        i = issues_by_id.get(pid, {})
        series = trends_by_id.get(pid, [])
        if len(series) < 2:
            continue
        if quarter_index == -1:
            subset = series
        elif quarter_index == -2:
            subset = series[:-1]
        else:
            subset = series
        if len(subset) < 2:
            continue
        derived = derive_metric_bundle(
            lpa, i, q, subset, docs_by_lpa, national_validation_proxy
        )
        state[pid] = derived
    return state


def main():
    parser = argparse.ArgumentParser(
        description="Check quarter-on-quarter stability of derived authority metrics"
    )
    parser.add_argument("--max-validation-delta", type=float, default=2.5)
    parser.add_argument("--max-delegated-delta", type=float, default=2.5)
    parser.add_argument("--max-consult-delta", type=float, default=1.5)
    parser.add_argument("--max-backlog-delta", type=float, default=12.0)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    lpas, docs, baselines, quality_rows, issue_rows, trend_rows = read_inputs()
    previous_state = build_metric_state(
        lpas, docs, baselines, quality_rows, issue_rows, trend_rows, -2
    )
    latest_state = build_metric_state(
        lpas, docs, baselines, quality_rows, issue_rows, trend_rows, -1
    )

    flags = []
    for pid in sorted(set(previous_state.keys()) & set(latest_state.keys())):
        prev = previous_state[pid]
        curr = latest_state[pid]
        checks = [
            ("validation_rework_proxy", args.max_validation_delta),
            ("delegated_ratio_proxy", args.max_delegated_delta),
            ("consultation_lag_proxy", args.max_consult_delta),
            ("backlog_pressure", args.max_backlog_delta),
        ]
        breaches = []
        for metric, threshold in checks:
            delta = to_float(curr.get(metric)) - to_float(prev.get(metric))
            if abs(delta) > threshold:
                breaches.append(
                    {"metric": metric, "delta": round(delta, 2), "threshold": threshold}
                )
        if breaches:
            flags.append({"pilot_id": pid, "breaches": breaches})

    lines = [
        "Derived Metric Stability Report",
        f"Checked LPAs: {len(latest_state)}",
        f"Flagged LPAs: {len(flags)}",
        "Thresholds:",
        f"  validation_rework_proxy: +/-{args.max_validation_delta}",
        f"  delegated_ratio_proxy: +/-{args.max_delegated_delta}",
        f"  consultation_lag_proxy: +/-{args.max_consult_delta}",
        f"  backlog_pressure: +/-{args.max_backlog_delta}",
        "",
    ]
    if not flags:
        lines.append("No stability thresholds exceeded.")
    else:
        for flag in flags:
            lines.append(f"- {flag['pilot_id']}")
            for breach in flag["breaches"]:
                lines.append(
                    f"  * {breach['metric']}: {breach['delta']:+.2f} (threshold +/-{breach['threshold']})"
                )

    TXT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    JSON_REPORT.write_text(
        json.dumps(
            {
                "checked_lpas": len(latest_state),
                "flagged_count": len(flags),
                "thresholds": {
                    "max_validation_delta": args.max_validation_delta,
                    "max_delegated_delta": args.max_delegated_delta,
                    "max_consult_delta": args.max_consult_delta,
                    "max_backlog_delta": args.max_backlog_delta,
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
