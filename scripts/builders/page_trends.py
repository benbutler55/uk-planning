"""Trend analysis page builder: quarter-on-quarter sparklines and delta table."""
import html
from collections import defaultdict

from .config import ROOT, SITE
from .data_loader import read_csv
from .metrics import cohort_for_pid
from .html_utils import (
    render_filter_controls, render_filter_script, render_table_guide,
    render_next_steps, sparkline_svg, page, write,
)


def build_trends():
    lpas = read_csv(ROOT / "data/plans/pilot-lpas.csv")
    trend_rows = read_csv(ROOT / "data/evidence/lpa-quarterly-trends.csv")
    trends_by_id = defaultdict(list)
    for r in trend_rows:
        trends_by_id[r["pilot_id"]].append(r)
    for pid in trends_by_id:
        trends_by_id[pid].sort(key=lambda x: x["quarter"])

    # Determine all quarters in sorted order
    all_quarters = sorted({r["quarter"] for r in trend_rows})

    # Build per-LPA row data
    table_rows = []
    for lpa in lpas:
        pid = lpa["pilot_id"]
        trows = trends_by_id.get(pid, [])
        cohort = cohort_for_pid(pid)
        region = lpa.get("region", "")
        lpa_type = lpa.get("lpa_type", "")
        by_quarter = {t["quarter"]: t for t in trows}
        speeds = [float(t["major_in_time_pct"]) for t in trows]
        first_speed = speeds[0] if speeds else None
        last_speed = speeds[-1] if speeds else None
        delta = (last_speed - first_speed) if first_speed is not None and last_speed is not None else None
        table_rows.append({
            "pilot_id": pid,
            "lpa_name": lpa.get("lpa_name", ""),
            "region": region,
            "lpa_type": lpa_type,
            "cohort": cohort,
            "by_quarter": by_quarter,
            "speeds": speeds,
            "delta": delta,
        })

    # Compute England average per quarter
    eng_by_quarter = {}
    for q in all_quarters:
        vals = []
        for row in table_rows:
            t = row["by_quarter"].get(q)
            if t:
                vals.append(float(t["major_in_time_pct"]))
        eng_by_quarter[q] = (sum(vals) / len(vals)) if vals else None
    eng_speeds = [eng_by_quarter[q] for q in all_quarters if eng_by_quarter[q] is not None]
    eng_first = eng_speeds[0] if eng_speeds else None
    eng_last = eng_speeds[-1] if eng_speeds else None
    eng_delta = (eng_last - eng_first) if eng_first is not None and eng_last is not None else None

    # Collect filter options
    regions = sorted({r["region"] for r in table_rows if r.get("region")})
    lpa_types = sorted({r["lpa_type"] for r in table_rows if r.get("lpa_type")})
    cohorts = sorted({r["cohort"] for r in table_rows if r.get("cohort")})

    body = '<section class="card"><p>Quarter-on-quarter trend analysis for major application decision speed across all authorities in scope. Each row shows performance per quarter with sparkline trends and net change.</p></section>'

    body += render_filter_controls("trends-table", "Search authorities", [
        ("region", "Region", regions),
        ("lpa_type", "LPA type", lpa_types),
        ("cohort", "Cohort", cohorts),
    ])

    body += render_table_guide("How to read this table", [
        "Each row is one authority with quarterly major-in-time percentages.",
        "The sparkline shows the visual trajectory across the trend window.",
        "Change (pp) is the percentage-point delta from first to last quarter.",
        "Positive change indicates improving speed; negative indicates declining.",
        "The England average row aggregates all authorities per quarter.",
    ])

    # Build table header
    quarter_headers = "".join(f"<th>{html.escape(q)}</th>" for q in all_quarters)
    body += '<section class="card" id="table-start">'
    body += '<table id="trends-table" class="dense-table"><thead><tr>'
    body += f'<th>Authority</th><th>Region</th><th>Cohort</th>{quarter_headers}<th>Trend</th><th>Change (pp)</th>'
    body += '</tr></thead><tbody>'

    # England average row
    eng_cells = ""
    for q in all_quarters:
        val = eng_by_quarter.get(q)
        eng_cells += f"<td>{val:.1f}</td>" if val is not None else "<td>n/a</td>"
    eng_spark = sparkline_svg(eng_speeds)
    eng_delta_str = f"{eng_delta:+.1f}" if eng_delta is not None else "n/a"
    body += (
        '<tr data-search="england average" data-region="" data-lpa_type="" data-cohort="">'
        f'<td><strong>England average</strong></td><td>All</td><td>All</td>'
        f'{eng_cells}<td>{eng_spark}</td><td>{eng_delta_str}</td></tr>'
    )

    # Per-LPA rows
    for row in sorted(table_rows, key=lambda r: r["lpa_name"]):
        pid = row["pilot_id"]
        lpa_page = f"plans-{pid.lower()}.html"
        search_blob = " ".join([
            row["lpa_name"], row["region"], row["cohort"], row["lpa_type"],
        ]).strip().lower()
        attrs = (
            f'data-search="{html.escape(search_blob)}" '
            f'data-region="{html.escape(row["region"].strip().lower())}" '
            f'data-lpa_type="{html.escape(row["lpa_type"].strip().lower())}" '
            f'data-cohort="{html.escape(row["cohort"].strip().lower())}"'
        )
        cells = ""
        for q in all_quarters:
            t = row["by_quarter"].get(q)
            if t:
                cells += f'<td>{html.escape(t["major_in_time_pct"])}</td>'
            else:
                cells += "<td>n/a</td>"
        spark = sparkline_svg(row["speeds"])
        delta_str = f"{row['delta']:+.1f}" if row["delta"] is not None else "n/a"
        body += (
            f'<tr {attrs}>'
            f'<td><a href="{html.escape(lpa_page)}">{html.escape(row["lpa_name"])}</a></td>'
            f'<td>{html.escape(row["region"])}</td>'
            f'<td>{html.escape(row["cohort"])}</td>'
            f'{cells}<td>{spark}</td><td>{delta_str}</td></tr>'
        )

    body += '</tbody></table></section>'

    body += render_filter_script(
        "trends-table",
        ["search", "region", "lpa_type", "cohort"],
        shared_filters=["region", "lpa_type", "cohort"],
    )

    body += render_next_steps([
        ("benchmark.html", "View benchmark ranking"),
        ("compare.html", "Compare two authorities"),
        ("plans.html", "Open authority profiles"),
    ])

    write(SITE / "trends.html", page(
        "Trend Analysis",
        "Quarter-on-quarter decision speed trends across all authorities in scope.",
        "trends", body,
        "This page shows how major application decision speed has changed over time for each authority, with sparkline visualisations and net change indicators.",
        purpose={
            "what": "Quarterly trend data for major decision speed across all LPAs in scope.",
            "who": "Policy teams, analysts, and stakeholders tracking performance trajectories.",
            "how": "Use the sparklines and change column to identify improving and declining authorities, then drill into profiles for context.",
            "data": "Trend data is sourced from GOV.UK P151 planning statistics. See Data Health for recency.",
        },
    ))
